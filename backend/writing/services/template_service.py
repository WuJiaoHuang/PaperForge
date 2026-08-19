# -*- coding: utf-8 -*-
"""模板服务 - 章节顺序、标题可配置化"""

import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.core.template_engine import CHAPTER_HINTS, CHAPTER_ORDER
from backend.utils import logger
from ..models import TemplateConfig, Paper, Chapter
from ..schemas import (
    TemplateConfigCreate,
    TemplateConfigUpdate,
    ChapterConfigItem,
    CustomChapterCreate,
    TemplateApplyRequest,
)


class TemplateService:
    """模板配置服务"""

    # 系统预定义章节
    AVAILABLE_CHAPTERS = [
        {"key": "summary", "default_title": "摘要与关键词", "hint": "中文摘要(约300字)与关键词", "group": "前置"},
        {"key": "abstract", "default_title": "Abstract", "hint": "英文摘要与Keywords", "group": "前置"},
        {"key": "ch1", "default_title": "第 1 章 绪论", "hint": CHAPTER_HINTS.get("ch1", ""), "group": "正文"},
        {"key": "ch2", "default_title": "第 2 章 相关技术介绍", "hint": CHAPTER_HINTS.get("ch2", ""), "group": "正文"},
        {"key": "ch3", "default_title": "第 3 章 系统需求分析", "hint": CHAPTER_HINTS.get("ch3", ""), "group": "正文"},
        {"key": "ch4", "default_title": "第 4 章 系统设计", "hint": CHAPTER_HINTS.get("ch4", ""), "group": "正文"},
        {"key": "ch5", "default_title": "第 5 章 系统实现", "hint": CHAPTER_HINTS.get("ch5", ""), "group": "正文"},
        {"key": "ch6", "default_title": "第 6 章 系统测试", "hint": CHAPTER_HINTS.get("ch6", ""), "group": "正文"},
        {"key": "ch7", "default_title": "第 7 章 总结与展望", "hint": CHAPTER_HINTS.get("ch7", ""), "group": "正文"},
        {"key": "refs", "default_title": "参考文献与致谢", "hint": "参考文献5条以上(GB/T 7714格式)与致谢", "group": "附录"},
    ]

    def __init__(self):
        self._available = self.AVAILABLE_CHAPTERS

    # ==================== 模板配置 CRUD ====================

    async def get_default_config(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
    ) -> Optional[TemplateConfig]:
        """获取默认模板配置"""
        query = select(TemplateConfig).where(
            TemplateConfig.is_default == True
        )
        if user_id:
            query = query.where(
                (TemplateConfig.user_id == user_id) | (TemplateConfig.user_id.is_(None))
            )
        else:
            query = query.where(TemplateConfig.user_id.is_(None))

        result = await db.execute(query.order_by(TemplateConfig.user_id.desc()).limit(1))
        return result.scalar_one_or_none()

    async def get_config(
        self,
        db: AsyncSession,
        config_id: str,
    ) -> Optional[TemplateConfig]:
        """获取模板配置"""
        result = await db.execute(
            select(TemplateConfig).where(TemplateConfig.id == config_id)
        )
        return result.scalar_one_or_none()

    async def get_user_configs(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> List[TemplateConfig]:
        """获取用户的所有模板配置"""
        result = await db.execute(
            select(TemplateConfig).where(
                (TemplateConfig.user_id == user_id) | (TemplateConfig.user_id.is_(None))
            ).order_by(TemplateConfig.is_default.desc(), TemplateConfig.created_at.desc())
        )
        return result.scalars().all()

    async def create_config(
        self,
        db: AsyncSession,
        data: TemplateConfigCreate,
        user_id: Optional[str] = None,
    ) -> TemplateConfig:
        """创建模板配置"""
        # 如果设为默认，取消其他默认
        if data.is_default:
            await self._clear_default(db, user_id)

        config = TemplateConfig(
            id=uuid.uuid4().hex[:10],
            user_id=user_id,
            name=data.name,
            is_default=data.is_default,
            chapter_order=[c.model_dump() for c in data.chapter_order],
            custom_chapters=[c.model_dump() for c in data.custom_chapters or []],
            available_chapters=self._available,
            description=data.description,
            version=1,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)

        logger.info(f"模板配置创建: {config.id}, name={config.name}")
        return config

    async def update_config(
        self,
        db: AsyncSession,
        config_id: str,
        data: TemplateConfigUpdate,
        user_id: Optional[str] = None,
    ) -> Optional[TemplateConfig]:
        """更新模板配置"""
        config = await self.get_config(db, config_id)
        if not config:
            return None

        # 权限检查
        if config.user_id and config.user_id != user_id:
            raise PermissionError("无权修改此模板")

        # 如果设为默认，取消其他默认
        if data.is_default:
            await self._clear_default(db, config.user_id)

        if data.name is not None:
            config.name = data.name
        if data.is_default is not None:
            config.is_default = data.is_default
        if data.description is not None:
            config.description = data.description
        if data.chapter_order is not None:
            config.chapter_order = [c.model_dump() for c in data.chapter_order]
        if data.custom_chapters is not None:
            config.custom_chapters = [c.model_dump() for c in data.custom_chapters]

        config.version += 1
        await db.commit()
        await db.refresh(config)

        logger.info(f"模板配置更新: {config_id}")
        return config

    async def delete_config(
        self,
        db: AsyncSession,
        config_id: str,
        user_id: Optional[str] = None,
    ) -> bool:
        """删除模板配置"""
        config = await self.get_config(db, config_id)
        if not config:
            return False

        # 权限检查
        if config.user_id and config.user_id != user_id:
            raise PermissionError("无权删除此模板")

        # 不能删除系统默认模板
        if config.is_default and not config.user_id:
            raise ValueError("不能删除系统默认模板")

        await db.delete(config)
        await db.commit()

        logger.info(f"模板配置删除: {config_id}")
        return True

    # ==================== 章节顺序管理 ====================

    async def update_chapter_order(
        self,
        db: AsyncSession,
        config_id: str,
        chapter_order: List[ChapterConfigItem],
        user_id: Optional[str] = None,
    ) -> Optional[TemplateConfig]:
        """调整章节顺序"""
        config = await self.get_config(db, config_id)
        if not config:
            return None

        if config.user_id and config.user_id != user_id:
            raise PermissionError("无权修改此模板")

        # 验证所有章节都在可用池中
        available_keys = {c["key"] for c in self._available}
        custom_keys = {c.get("key") for c in config.custom_chapters}
        all_keys = available_keys | custom_keys

        for item in chapter_order:
            if item.key not in all_keys:
                raise ValueError(f"未知章节: {item.key}")

        config.chapter_order = [c.model_dump() for c in chapter_order]
        config.version += 1
        await db.commit()
        await db.refresh(config)

        logger.info(f"章节顺序更新: {config_id}")
        return config

    async def add_custom_chapter(
        self,
        db: AsyncSession,
        config_id: str,
        data: CustomChapterCreate,
        user_id: Optional[str] = None,
    ) -> Optional[TemplateConfig]:
        """添加自定义章节"""
        config = await self.get_config(db, config_id)
        if not config:
            return None

        if config.user_id and config.user_id != user_id:
            raise PermissionError("无权修改此模板")

        # 生成唯一 key
        custom_keys = [c.get("key") for c in config.custom_chapters]
        next_num = 1
        while True:
            key = f"custom_{next_num}"
            if key not in custom_keys:
                break
            next_num += 1

        new_chapter = {
            "key": key,
            "title": data.title,
            "hint": data.hint or "",
        }

        # 插入到指定位置
        if data.insert_after:
            new_order = []
            inserted = False
            for item in config.chapter_order:
                new_order.append(item)
                if item.get("key") == data.insert_after and not inserted:
                    new_order.append({**new_chapter, "enabled": True})
                    inserted = True
            if not inserted:
                new_order.append({**new_chapter, "enabled": True})
            config.chapter_order = new_order
        else:
            config.chapter_order.append({**new_chapter, "enabled": True})

        config.custom_chapters.append(new_chapter)
        config.version += 1
        await db.commit()
        await db.refresh(config)

        logger.info(f"自定义章节添加: {config_id}, key={key}")
        return config

    async def remove_custom_chapter(
        self,
        db: AsyncSession,
        config_id: str,
        chapter_key: str,
        user_id: Optional[str] = None,
    ) -> Optional[TemplateConfig]:
        """移除自定义章节"""
        config = await self.get_config(db, config_id)
        if not config:
            return None

        if config.user_id and config.user_id != user_id:
            raise PermissionError("无权修改此模板")

        # 从 custom_chapters 移除
        config.custom_chapters = [
            c for c in config.custom_chapters
            if c.get("key") != chapter_key
        ]

        # 从 chapter_order 移除
        config.chapter_order = [
            c for c in config.chapter_order
            if c.get("key") != chapter_key
        ]

        config.version += 1
        await db.commit()
        await db.refresh(config)

        logger.info(f"自定义章节移除: {config_id}, key={chapter_key}")
        return config

    # ==================== 应用模板到论文 ====================

    async def apply_template_to_paper(
        self,
        db: AsyncSession,
        paper_id: str,
        template_id: str,
        regenerate_existing: bool = False,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        应用模板配置到论文
        
        Args:
            db: 数据库会话
            paper_id: 论文ID
            template_id: 模板配置ID
            regenerate_existing: 是否重新生成已存在章节
            user_id: 用户ID
        
        Returns:
            应用结果
        """
        # 1. 获取论文和模板
        paper = await db.execute(
            select(Paper).where(Paper.id == paper_id)
        )
        paper = paper.scalar_one_or_none()
        if not paper:
            raise ValueError(f"论文不存在: {paper_id}")

        template = await self.get_config(db, template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")

        # 2. 获取模板的章节配置
        template_chapters = template.get_all_chapters()

        # 3. 获取现有章节
        existing = await db.execute(
            select(Chapter).where(
                Chapter.paper_id == paper_id,
                Chapter.is_enabled == True,
            )
        )
        existing_chapters = {c.key: c for c in existing.scalars().all()}

        # 4. 应用模板
        updated_count = 0
        created_count = 0
        disabled_count = 0

        for seq, tpl_ch in enumerate(template_chapters, start=0):
            key = tpl_ch["key"]
            is_custom = tpl_ch.get("is_custom", False)

            if key in existing_chapters:
                # 更新现有章节
                chapter = existing_chapters[key]
                chapter.seq = seq
                if not chapter.is_custom:  # 只有非自定义章节才更新标题
                    chapter.title = tpl_ch["title"]
                chapter.is_enabled = True
                if regenerate_existing:
                    # 标记需要重新生成
                    chapter.status = "pending"
                updated_count += 1
                del existing_chapters[key]
            else:
                # 创建新章节
                chapter = Chapter(
                    id=uuid.uuid4().hex[:10],
                    paper_id=paper_id,
                    key=key,
                    seq=seq,
                    title=tpl_ch["title"],
                    hint=tpl_ch.get("hint", ""),
                    status="pending",
                    is_custom=is_custom,
                    is_enabled=True,
                    version=1,
                    design_version=1,
                )
                db.add(chapter)
                created_count += 1

        # 5. 禁用不在模板中的章节
        for chapter in existing_chapters.values():
            chapter.is_enabled = False
            disabled_count += 1

        await db.commit()

        result = {
            "status": "success",
            "paper_id": paper_id,
            "template_id": template_id,
            "created": created_count,
            "updated": updated_count,
            "disabled": disabled_count,
            "total": created_count + updated_count,
        }

        logger.info(f"模板应用到论文: {paper_id}, result={result}")
        return result

    # ==================== 辅助方法 ====================

    async def _clear_default(self, db: AsyncSession, user_id: Optional[str]):
        """清除默认标记"""
        query = select(TemplateConfig).where(TemplateConfig.is_default == True)
        if user_id:
            query = query.where(TemplateConfig.user_id == user_id)
        else:
            query = query.where(TemplateConfig.user_id.is_(None))

        result = await db.execute(query)
        for config in result.scalars().all():
            config.is_default = False

    def get_available_chapters(self) -> List[Dict[str, Any]]:
        """获取所有可用章节"""
        return self._available