# -*- coding: utf-8 -*-
"""PaperForge V2 SSE 推送工具"""

import json
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime


class SSEEvent:
    """SSE 事件封装"""
    
    def __init__(self, event: Optional[str] = None, data: Any = None):
        self.event = event
        self.data = data
    
    def to_sse(self) -> str:
        """转换为 SSE 格式字符串"""
        lines = []
        if self.event:
            lines.append(f"event: {self.event}")
        if self.data is not None:
            data_str = json.dumps(self.data, ensure_ascii=False)
            for line in data_str.splitlines():
                lines.append(f"data: {line}")
        lines.append("")
        return "\n".join(lines)


def sse_generator(
    event_queue: asyncio.Queue,
    keep_alive_interval: int = 15,
) -> AsyncGenerator[str, None]:
    """
    SSE 生成器
    
    Args:
        event_queue: 事件队列，生产者往里面放事件
        keep_alive_interval: 心跳间隔（秒），保持连接
    
    Yields:
        SSE 格式字符串
    """
    async def _inner():
        last_heartbeat = datetime.now()
        
        while True:
            try:
                # 尝试从队列获取事件，超时则发送心跳
                event = await asyncio.wait_for(
                    event_queue.get(), 
                    timeout=keep_alive_interval
                )
                if event is None:  # 结束信号
                    break
                yield event.to_sse()
                
            except asyncio.TimeoutError:
                # 发送心跳保持连接
                yield SSEEvent(event="ping", data={"timestamp": datetime.now().isoformat()}).to_sse()
            
            except Exception as e:
                # 错误事件
                yield SSEEvent(
                    event="error", 
                    data={"message": str(e)}
                ).to_sse()
                break
    
    return _inner()


class ProgressPublisher:
    """进度发布器 - 封装论文生成进度推送"""
    
    def __init__(self, event_queue: asyncio.Queue):
        self.queue = event_queue
        self._closed = False
    
    async def publish_stage(self, current: int, total: int, stage_name: str, detail: str = ""):
        """发布阶段进度"""
        if self._closed:
            return
        await self.queue.put(SSEEvent(
            event="stage",
            data={
                "type": "stage",
                "current": current,
                "total": total,
                "stage": stage_name,
                "detail": detail,
                "progress": round(current / total * 100, 1) if total > 0 else 0,
                "timestamp": datetime.now().isoformat(),
            }
        ))
    
    async def publish_chapter(self, seq: int, key: str, title: str, content_md: str = ""):
        """发布章节完成"""
        if self._closed:
            return
        await self.queue.put(SSEEvent(
            event="chapter",
            data={
                "type": "chapter",
                "seq": seq,
                "key": key,
                "title": title,
                "content_md": content_md,
                "timestamp": datetime.now().isoformat(),
            }
        ))
    
    async def publish_design(self, design: Dict[str, Any]):
        """发布系统设定"""
        if self._closed:
            return
        await self.queue.put(SSEEvent(
            event="design",
            data={
                "type": "design",
                "design": design,
                "timestamp": datetime.now().isoformat(),
            }
        ))
    
    async def publish_done(self, paper_id: str, message: str = "生成完成"):
        """发布完成事件"""
        if self._closed:
            return
        await self.queue.put(SSEEvent(
            event="done",
            data={
                "type": "done",
                "paper_id": paper_id,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }
        ))
        self._closed = True
        await self.queue.put(None)  # 结束信号
    
    async def publish_error(self, error: str):
        """发布错误事件"""
        if self._closed:
            return
        await self.queue.put(SSEEvent(
            event="error",
            data={
                "type": "error",
                "message": error,
                "timestamp": datetime.now().isoformat(),
            }
        ))
        self._closed = True
        await self.queue.put(None)  # 结束信号
    
    async def publish_log(self, level: str, message: str):
        """发布日志"""
        if self._closed:
            return
        await self.queue.put(SSEEvent(
            event="log",
            data={
                "type": "log",
                "level": level,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }
        ))
    
    def close(self):
        """关闭发布器"""
        self._closed = True