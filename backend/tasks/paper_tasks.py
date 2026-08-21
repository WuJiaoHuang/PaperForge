# -*- coding: utf-8 -*-
"""PaperForge V2 论文生成异步任务"""

import asyncio
from typing import Optional, Dict, Any
from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession

from .celery_app import celery_app
from ..config import settings
from ..utils import logger
from ..dependencies import AsyncSessionLocal


class PaperGenerationTask(Task):
    """论文生成任务基类"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"任务 {task_id} 失败: {exc}")
        # TODO: 更新数据库状态
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"任务 {task_id} 完成")


@celery_app.task(base=PaperGenerationTask, bind=True, name="generate_paper")
def generate_paper_task(
    self,
    paper_id: str,
    use_ai: bool = False,
) -> Dict[str, Any]:
    """
    异步生成论文任务
    
    Args:
        paper_id: 论文ID
        use_ai: 是否使用AI
    
    Returns:
        论文生成结果
    """
    logger.info(f"开始生成论文: {paper_id}, use_ai={use_ai}")
    
    # 在 Celery 任务中运行异步代码
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _generate_paper_async(paper_id, use_ai, self.request.id)
        )
        return result
    except Exception as e:
        logger.error(f"论文生成失败: {paper_id}, error={e}")
        raise
    finally:
        loop.close()


async def _generate_paper_async(
    paper_id: str,
    use_ai: bool,
    task_id: str,
) -> Dict[str, Any]:
    """异步执行论文生成"""
    from ..writing.services import WritingService
    from ..utils import ProgressPublisher
    
    # 创建数据库会话
    async with AsyncSessionLocal() as db:
        # 创建 SSE 发布器（将进度推送到 Redis，供 SSE 端点读取）
        publisher = ProgressPublisher(
            # TODO: 对接 Redis 发布进度
            # 目前使用内存队列，后续对接 Redis Pub/Sub
        )
        
        service = WritingService()
        
        try:
            paper = await service.generate_paper(
                db=db,
                paper_id=paper_id,
                use_ai=use_ai,
                publisher=publisher,
            )
            
            # TODO: 将进度推送到 Redis，供 SSE 端点读取
            # await redis_client.publish(f"paper:{paper_id}:progress", ...)
            
            return {
                "task_id": task_id,
                "paper_id": paper_id,
                "status": "success",
                "mode": paper.mode,
                "word_count": paper.word_count,
                "chapter_count": paper.chapter_count,
            }
            
        except Exception as e:
            logger.error(f"生成失败: {e}")
            # TODO: 推送错误到 Redis
            raise


@celery_app.task(name="regenerate_chapter")
def regenerate_chapter_task(
    paper_id: str,
    chapter_key: str,
    instructions: str = "",
    use_ai: bool = False,
) -> Dict[str, Any]:
    """重新生成章节任务"""
    logger.info(f"重新生成章节: {paper_id}/{chapter_key}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _regenerate_chapter_async(paper_id, chapter_key, instructions, use_ai)
        )
        return result
    except Exception as e:
        logger.error(f"章节重写失败: {paper_id}/{chapter_key}, error={e}")
        raise
    finally:
        loop.close()


async def _regenerate_chapter_async(
    paper_id: str,
    chapter_key: str,
    instructions: str,
    use_ai: bool,
) -> Dict[str, Any]:
    """异步执行章节重写"""
    from ..writing.services import WritingService
    
    async with AsyncSessionLocal() as db:
        service = WritingService()
        
        chapter = await service.regenerate_chapter(
            db=db,
            paper_id=paper_id,
            chapter_key=chapter_key,
            instructions=instructions,
            use_ai=use_ai,
        )
        
        return {
            "paper_id": paper_id,
            "chapter_key": chapter_key,
            "status": "success",
            "version": chapter.version,
        }


@celery_app.task(name="export_paper")
def export_paper_task(
    paper_id: str,
    format: str = "docx",
) -> Dict[str, Any]:
    """导出论文任务（大文件场景）"""
    logger.info(f"导出论文: {paper_id}, format={format}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _export_paper_async(paper_id, format)
        )
        return result
    except Exception as e:
        logger.error(f"导出失败: {paper_id}, error={e}")
        raise
    finally:
        loop.close()


async def _export_paper_async(
    paper_id: str,
    format: str,
) -> Dict[str, Any]:
    """异步执行导出"""
    from ..writing.services import ExportService
    
    async with AsyncSessionLocal() as db:
        service = ExportService()
        
        if format == "docx":
            # TODO: 对接成员3获取图表图片
            chart_images = None  # await chart_service.get_chart_images(paper_id)
            buf = await service.export_docx(db, paper_id, chart_images)
            return {
                "paper_id": paper_id,
                "format": format,
                "status": "success",
                "size": len(buf.getvalue()),
            }
        else:
            md_text = await service.export_markdown(db, paper_id)
            return {
                "paper_id": paper_id,
                "format": format,
                "status": "success",
                "size": len(md_text.encode("utf-8")),
            }