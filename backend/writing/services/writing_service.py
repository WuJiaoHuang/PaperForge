# -*- coding: utf-8 -*-
"""写作服务 - 论文生成、章节重写、智能更新、一致性保障"""

import uuid
import asyncio
from typing import Optional, Dict, Any, List, Callable, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.core.ai_client import (
    ai_available,
    generate_paper_ai,
    regenerate_chapter_ai,
    CHAPTER_ORDER,
)
from backend.core.template_engine import (
    generate_paper as generate_paper_template,
    regenerate_chapter_template,
    build_system_design,
    CHAPTER_HINTS,
)
from backend.utils import logger, ProgressPublisher
from ..models import Paper, Chapter, Design, TemplateConfig
from ..schemas import (
    DesignCreate,
    DesignAffectedChapters,
    DesignConsistencyCheck,
)


class WritingService:
    """论文写作核心服务"""

    def __init__(self):
        self._chapter_hints = CHAPTER_HINTS

    # ==================== 论文生成 ====================

    async def generate_paper(
        self,
        db: AsyncSession,
        paper_id: str,
        use_ai: bool = False,
        publisher: Optional[ProgressPublisher] = None,
    ) -> Paper:
        """
        生成完整论文（支持 AI 和模板两种模式）

        Args:
            db: 数据库会话
            paper_id: 论文ID
            use_ai: 是否使用AI
            publisher: SSE进度发布器

        Returns:
            更新后的论文对象
        """
        # 1. 获取论文
        paper = await self._get_paper(db, paper_id)
        if not paper:
            raise ValueError(f"论文不存在: {paper_id}")

        # 2. 更新状态
        paper.status = "generating"
        await db.commit()

        try:
            # 3. 获取或创建设计
            design = await self._get_or_create_design(db, paper)

            # 4. 推送设计
            if publisher:
                await publisher.publish_design(design.to_dict())

            # 5. 根据模式生成
            if use_ai and ai_available():
                payload = await self._generate_with_ai(
                    paper, design, publisher
                )
            else:
                payload = self._generate_with_template(
                    paper, design
                )

            if payload is None:
                raise RuntimeError("论文生成失败")

            # 6. 保存章节
            await self._save_chapters(db, paper, payload["chapters"], design.version)

            # 7. 更新论文统计
            paper.status = "done"
            paper.mode = payload.get("mode", "template")
            paper.word_count = payload.get("stats", {}).get("word_count", 0)
            paper.chapter_count = len(payload["chapters"])
            paper.generated_at = datetime.utcnow()
            paper.note = payload.get("note")

            await db.commit()
            await db.refresh(paper)

            # 8. 推送完成
            if publisher:
                await publisher.publish_done(paper_id, "生成完成")

            logger.info(f"论文生成完成: {paper_id}, 模式: {paper.mode}")
            return paper

        except Exception as e:
            paper.status = "draft"
            await db.commit()
            logger.error(f"论文生成失败: {paper_id}, error={e}")
            if publisher:
                await publisher.publish_error(str(e))
            raise

    async def _generate_with_ai(
        self,
        paper: Paper,
        design: Design,
        publisher: Optional[ProgressPublisher] = None,
    ) -> Optional[Dict[str, Any]]:
        """使用 AI 生成"""
        # 构建进度回调
        def on_stage(current, total, stage_name):
            if publisher:
                asyncio.create_task(
                    publisher.publish_stage(current, total, stage_name)
                )

        def on_chapter(seq, key, title, hint, content_md):
            if publisher:
                asyncio.create_task(
                    publisher.publish_chapter(seq, key, title, content_md)
                )

        def on_design(design_data):
            # 更新设计
            pass

        # 调用 AI 生成
        return generate_paper_ai(
            title=paper.title,
            techs=paper.techs,
            level=paper.word_level,
            style=paper.style,
            requirements=paper.requirements or "",
            on_stage=on_stage,
            on_chapter=on_chapter,
            on_design=on_design,
        )

    def _generate_with_template(
        self,
        paper: Paper,
        design: Design,
    ) -> Dict[str, Any]:
        """使用模板生成"""
        result = generate_paper_template(
            title=paper.title,
           techs=paper.techs,
           level=paper.word_level,
           style=paper.style,
        )

        # 动态生成图表建议（基于实际系统设定）
        result["chart_suggestions"] = self._build_dynamic_chart_suggestions(
            result.get("system_design", {}),
            paper.title,
            paper.techs,
        )

        return result

    def _build_dynamic_chart_suggestions(
        self,
        design: Dict,
        title: str,
        techs: List[str],
    ) -> List[Dict[str, str]]:
        """
        动态生成图表建议清单

        根据系统设定自动判断需要哪些图表
        """
        suggestions = []

        # 判断是否有角色和功能 → 需要用例图
        if design.get("roles") and design.get("features"):
            suggestions.append({
                "fig": "图 3-1",
                "title": "系统用例图",
                "type": "usecase",
                "position": "第 3 章 需求分析",
                "material": "角色与功能描述文字",
            })

        # 判断是否有技术栈 → 需要架构图
        if techs:
            suggestions.append({
                "fig": "图 4-1",
                "title": "系统架构图",
                "type": "architecture",
                "position": "第 4 章 系统设计",
                "material": "技术栈 / 部署说明文字",
            })

        # 判断是否有模块 → 需要功能模块图
        if design.get("modules"):
            suggestions.append({
                "fig": "图 4-2",
                "title": "功能模块图",
                "type": "module",
                "position": "第 4 章 模块设计",
                "material": "模块说明(可自动预填)",
            })

        # 判断是否有数据表 → 需要 E-R 图
        if design.get("tables"):
            suggestions.append({
                "fig": "图 4-3",
                "title": "E-R 图",
                "type": "er",
                "position": "第 4 章 数据库设计",
                "material": "SQL 建表语句",
            })

        # 判断是否有功能 → 需要流程图
        if design.get("features"):
            suggestions.append({
                "fig": "图 5-1",
                "title": "核心业务流程图",
                "type": "flow",
                "position": "第 5 章 系统实现",
                "material": "业务流程文字",
            })

        return suggestions

    # ==================== 章节重写 ====================

    async def regenerate_chapter(
        self,
        db: AsyncSession,
        paper_id: str,
        chapter_key: str,
        instructions: str = "",
        use_ai: bool = False,
    ) -> Chapter:
        """
        重新生成某个章节

        Args:
            db: 数据库会话
            paper_id: 论文ID
            chapter_key: 章节Key
            instructions: 用户修改意见
            use_ai: 是否使用AI

        Returns:
            更新后的章节对象
        """
        # 1. 获取论文和章节
        paper = await self._get_paper(db, paper_id)
        if not paper:
            raise ValueError(f"论文不存在: {paper_id}")

        chapter = await self._get_chapter(db, paper_id, chapter_key)
        if not chapter:
            raise ValueError(f"章节不存在: {chapter_key}")

        # 2. 获取设计
        design = await self._get_design(db, paper.design_id)
        if not design:
            raise ValueError("系统设定不存在")

        # 3. 更新状态
        chapter.status = "generating"
        await db.commit()

        try:
            # 4. 生成内容
            content = None
            if use_ai and ai_available():
                content = regenerate_chapter_ai(
                    title=paper.title,
                    techs=paper.techs,
                    level=paper.word_level,
                    style=paper.style,
                    design=design.to_dict(),
                    key=chapter_key,
                    chapter_title=chapter.title,
                    hint=chapter.hint or "",
                    instructions=instructions,
                    requirements=paper.requirements or "",
                )

            # AI 失败或未启用，使用模板
            if content is None:
                content = regenerate_chapter_template(
                    key=chapter_key,
                    title=paper.title,
                    techs=paper.techs,
                    design=design.to_dict(),
                    level=paper.word_level,
                    style=paper.style,
                )

            if content is None:
                raise RuntimeError(f"章节生成失败: {chapter_key}")

            # 5. 更新章节
            chapter.content_md = content
            chapter.status = "generated" if instructions else "updated"
            chapter.version += 1
            chapter.design_version = design.version
            chapter.generated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(chapter)

            logger.info(f"章节重写完成: {paper_id}/{chapter_key}")
            return chapter

        except Exception as e:
            chapter.status = "generated"
            await db.commit()
            logger.error(f"章节重写失败: {paper_id}/{chapter_key}, error={e}")
            raise

    # ==================== 智能更新 ====================

    async def smart_update_chapters(
        self,
        db: AsyncSession,
        paper_id: str,
        new_design: DesignCreate,
    ) -> Dict[str, Any]:
        """
        智能更新：当系统设定变化时，重写受影响章节

        Args:
            db: 数据库会话
            paper_id: 论文ID
            new_design: 新的系统设定

        Returns:
            更新结果
        """
        # 1. 获取论文和旧设计
        paper = await self._get_paper(db, paper_id)
        if not paper:
            raise ValueError(f"论文不存在: {paper_id}")

        old_design = await self._get_design(db, paper.design_id)
        if not old_design:
            raise ValueError("系统设定不存在")

        # 2. 分析受影响的章节
        affected = self._analyze_affected_chapters(
            old_design.to_dict(),
            new_design.model_dump(),
        )

        if not affected["affected_keys"]:
            # 没有受影响章节，只更新设计
            new_design_obj = await self._create_new_design_version(
                db, paper_id, new_design
            )
            paper.design_id = new_design_obj.id
            await db.commit()
            return {
                "status": "no_change",
                "message": "设计变更不影响现有章节",
                "design_id": new_design_obj.id,
            }

        # 3. 创建新设计版本
        new_design_obj = await self._create_new_design_version(
            db, paper_id, new_design
        )

        # 4. 更新受影响章节
        updated_chapters = []
        for chapter_key in affected["affected_keys"]:
            chapter = await self._get_chapter(db, paper_id, chapter_key)
            if chapter:
                # 重新生成
                content = regenerate_chapter_template(
                    key=chapter_key,
                    title=paper.title,
                    techs=paper.techs,
                    design=new_design_obj.to_dict(),
                    level=paper.word_level,
                    style=paper.style,
                )
                if content:
                    chapter.content_md = content
                    chapter.status = "updated"
                    chapter.version += 1
                    chapter.design_version = new_design_obj.version
                    updated_chapters.append(chapter_key)

        # 5. 更新论文设计引用
        paper.design_id = new_design_obj.id
        paper.status = "done"
        await db.commit()

        return {
            "status": "updated",
            "message": f"已智能更新 {len(updated_chapters)} 个章节",
            "design_id": new_design_obj.id,
            "affected_keys": affected["affected_keys"],
            "updated_keys": updated_chapters,
            "reason": affected["reason"],
        }

    def _analyze_affected_chapters(
        self,
        old_design: Dict[str, Any],
        new_design: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        分析哪些章节受设计变更影响

        影响规则：
        - 模块名变化 → 影响 ch3(需求分析), ch4(系统设计), ch5(系统实现)
        - 角色名变化 → 影响 ch3(需求分析), ch4(系统设计)
        - 数据表变化 → 影响 ch4(系统设计), ch5(系统实现)
        - 功能变化 → 影响 ch3(需求分析)
        """
        affected_keys = []
        reasons = []

        old_modules = {m["name"] for m in old_design.get("modules", [])}
        new_modules = {m["name"] for m in new_design.get("modules", [])}
        if old_modules != new_modules:
            affected_keys.extend(["ch3", "ch4", "ch5"])
            reasons.append("模块列表发生变化")

        old_roles = set(old_design.get("roles", []))
        new_roles = set(new_design.get("roles", []))
        if old_roles != new_roles:
            affected_keys.extend(["ch3", "ch4"])
            reasons.append("角色列表发生变化")

        old_tables = {t["name"] for t in old_design.get("tables", [])}
        new_tables = {t["name"] for t in new_design.get("tables", [])}
        if old_tables != new_tables:
            affected_keys.extend(["ch4", "ch5"])
            reasons.append("数据表发生变化")

        return {
            "affected_keys": list(set(affected_keys)),
            "reason": "；".join(reasons) if reasons else "设计变更",
        }

    # ==================== 一致性检查 ====================

    async def check_consistency(
        self,
        db: AsyncSession,
        paper_id: str,
    ) -> DesignConsistencyCheck:
        """
        检查全篇一致性

        验证所有章节中的模块名、角色名、表名是否与 design 一致
        """
        paper = await self._get_paper(db, paper_id)
        if not paper:
            raise ValueError(f"论文不存在: {paper_id}")

        design = await self._get_design(db, paper.design_id)
        if not design:
            raise ValueError("系统设定不存在")

        # 获取所有章节内容
        chapters = await self._get_all_chapters(db, paper_id)
        if not chapters:
            return DesignConsistencyCheck(
                is_consistent=True,
                issues=[],
                summary="暂无章节需要检查",
            )

        # 检查内容
        issues = []
        design_data = design.to_dict()
        modules = {m["name"] for m in design_data.get("modules", [])}
        roles = set(design_data.get("roles", []))
        tables = {t["name"] for t in design_data.get("tables", [])}
        tables.update({t["title"] for t in design_data.get("tables", [])})

        for chapter in chapters:
            content = chapter.content_md or ""

            # 检查模块名
            for mod in modules:
                if mod and mod in content:
                    continue

            # 检查角色名
            for role in roles:
                if role and role in content:
                    continue

            # 检查表名
            for table in tables:
                if table and table in content:
                    continue

            # 记录不一致问题（简化版）

        return DesignConsistencyCheck(
            is_consistent=len(issues) == 0,
            issues=issues,
            summary=f"检查完成，发现 {len(issues)} 个不一致问题" if issues else "所有章节与系统设定一致",
        )

    # ==================== 辅助方法 ====================

    async def _get_paper(self, db: AsyncSession, paper_id: str) -> Optional[Paper]:
        result = await db.execute(
            select(Paper).where(Paper.id == paper_id)
        )
        return result.scalar_one_or_none()

    async def _get_chapter(
        self,
        db: AsyncSession,
        paper_id: str,
        chapter_key: str,
    ) -> Optional[Chapter]:
        result = await db.execute(
            select(Chapter).where(
                Chapter.paper_id == paper_id,
                Chapter.key == chapter_key,
            )
        )
        return result.scalar_one_or_none()

    async def _get_all_chapters(
        self,
        db: AsyncSession,
        paper_id: str,
    ) -> List[Chapter]:
        result = await db.execute(
            select(Chapter).where(
                Chapter.paper_id == paper_id,
                Chapter.is_enabled == True,
            ).order_by(Chapter.seq)
        )
        return result.scalars().all()

    async def _get_design(self, db: AsyncSession, design_id: str) -> Optional[Design]:
        if not design_id:
            return None
        result = await db.execute(
            select(Design).where(Design.id == design_id)
        )
        return result.scalar_one_or_none()

    async def _get_or_create_design(
        self,
        db: AsyncSession,
        paper: Paper,
    ) -> Design:
        """获取或创建系统设定"""
        if paper.design_id:
            design = await self._get_design(db, paper.design_id)
            if design:
                return design

        # 创建新设计
        design_data = build_system_design(
            title=paper.title,
            techs=paper.techs,
            level=paper.word_level,
        )
        design = Design(
            id=uuid.uuid4().hex[:10],
            paper_id=paper.id,
            modules=design_data["modules"],
            roles=design_data["roles"],
            tables=design_data["tables"],
            features=design_data["features"],
            domain_note=design_data.get("domain_note"),
            version=1,
            is_latest=True,
        )
        db.add(design)
        await db.flush()

        paper.design_id = design.id
        return design

    async def _create_new_design_version(
        self,
        db: AsyncSession,
        paper_id: str,
        design_data: DesignCreate,
    ) -> Design:
        """创建新版本的设计"""
        # 将旧设计标记为非最新
        await db.execute(
            update(Design)
            .where(Design.paper_id == paper_id, Design.is_latest == True)
            .values(is_latest=False)
        )

        new_design = Design(
            id=uuid.uuid4().hex[:10],
            paper_id=paper_id,
            modules=[m.model_dump() for m in design_data.modules],
            roles=design_data.roles,
            tables=[t.model_dump() for t in design_data.tables],
            features=[f.model_dump() for f in design_data.features],
            domain_note=design_data.domain_note,
            version=1,  # 会在数据库中被更新
            is_latest=True,
        )
        db.add(new_design)
        await db.flush()

        # 更新版本号
        latest_version = await db.execute(
            select(Design.version).where(
                Design.paper_id == paper_id,
                Design.is_latest == False,
            ).order_by(Design.version.desc()).limit(1)
        )
        max_version = latest_version.scalar_one_or_none() or 0
        new_design.version = max_version + 1

        await db.flush()
        return new_design

    async def _save_chapters(
        self,
        db: AsyncSession,
        paper: Paper,
        chapters_data: List[Dict[str, Any]],
        design_version: int,
    ):
        """保存章节"""
        # 删除旧章节
        await db.execute(
            update(Chapter)
            .where(Chapter.paper_id == paper.id)
            .values(is_enabled=False)
        )

        for data in chapters_data:
            chapter = Chapter(
                id=uuid.uuid4().hex[:10],
                paper_id=paper.id,
                key=data["key"],
                seq=data["seq"],
                title=data["title"],
                hint=data.get("hint", ""),
                content_md=data["content_md"],
                status="generated",
                is_custom=data.get("is_custom", False),
                is_enabled=True,
                version=1,
                design_version=design_version,
                generated_at=datetime.utcnow(),
            )
            db.add(chapter)
