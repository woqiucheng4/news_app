"""
任务队列模块 - 支持 APScheduler 和 Celery，可无缝切换
"""

from typing import Optional, Any, Callable, Dict
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import uuid
import logging
from functools import wraps

from .config import get_settings

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    metadata: Dict = field(default_factory=dict)


@dataclass
class TaskConfig:
    """任务配置"""
    max_retries: int = 3
    retry_delay: int = 60  # 秒
    timeout: int = 300  # 秒
    priority: TaskPriority = TaskPriority.NORMAL
    queue: str = "default"
    metadata: Dict = field(default_factory=dict)


class TaskQueue(ABC):
    """任务队列抽象接口"""

    @abstractmethod
    async def enqueue(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict = None,
        config: TaskConfig = None,
    ) -> str:
        """
        入队任务

        Args:
            task_name: 任务名称
            args: 位置参数
            kwargs: 关键字参数
            config: 任务配置

        Returns:
            任务 ID
        """
        pass

    @abstractmethod
    async def get_status(self, task_id: str) -> Optional[TaskResult]:
        """获取任务状态"""
        pass

    @abstractmethod
    async def cancel(self, task_id: str) -> bool:
        """取消任务"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass


class SimpleTaskQueue(TaskQueue):
    """
    简单任务队列（基于 asyncio）

    适用场景：
    - MVP 阶段
    - 单机部署
    - 任务量小
    """

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._tasks: Dict[str, TaskResult] = {}
        self._task_funcs: Dict[str, Callable] = {}
        self._semaphore = asyncio.Semaphore(max_workers)
        self._running_tasks: Dict[str, asyncio.Task] = {}

    def register_task(self, name: str, func: Callable):
        """注册任务函数"""
        self._task_funcs[name] = func
        logger.info(f"Task registered: {name}")

    async def enqueue(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict = None,
        config: TaskConfig = None,
    ) -> str:
        if task_name not in self._task_funcs:
            raise ValueError(f"Task not registered: {task_name}")

        task_id = str(uuid.uuid4())
        config = config or TaskConfig()

        # 创建任务结果
        result = TaskResult(
            task_id=task_id,
            status=TaskStatus.PENDING,
            metadata={"task_name": task_name, **config.metadata},
        )
        self._tasks[task_id] = result

        # 异步执行任务
        asyncio.create_task(
            self._execute_task(
                task_id=task_id,
                task_name=task_name,
                args=args,
                kwargs=kwargs or {},
                config=config,
            )
        )

        return task_id

    async def _execute_task(
        self,
        task_id: str,
        task_name: str,
        args: tuple,
        kwargs: dict,
        config: TaskConfig,
    ):
        """执行任务"""
        result = self._tasks[task_id]

        async with self._semaphore:
            result.status = TaskStatus.RUNNING
            result.started_at = datetime.now()

            try:
                # 执行任务函数
                task_func = self._task_funcs[task_name]

                # 超时控制
                task_result = await asyncio.wait_for(
                    task_func(*args, **kwargs),
                    timeout=config.timeout,
                )

                result.status = TaskStatus.COMPLETED
                result.result = task_result
                result.completed_at = datetime.now()

            except asyncio.TimeoutError:
                result.status = TaskStatus.FAILED
                result.error = "Task timeout"
                result.completed_at = datetime.now()
                logger.error(f"Task {task_id} timeout")

            except Exception as e:
                result.retry_count += 1

                if result.retry_count < config.max_retries:
                    # 重试
                    result.status = TaskStatus.RETRY
                    logger.warning(
                        f"Task {task_id} failed, retry {result.retry_count}/{config.max_retries}: {e}"
                    )
                    await asyncio.sleep(config.retry_delay)
                    await self._execute_task(task_id, task_name, args, kwargs, config)
                else:
                    result.status = TaskStatus.FAILED
                    result.error = str(e)
                    result.completed_at = datetime.now()
                    logger.error(f"Task {task_id} failed after {config.max_retries} retries: {e}")

    async def get_status(self, task_id: str) -> Optional[TaskResult]:
        return self._tasks.get(task_id)

    async def cancel(self, task_id: str) -> bool:
        if task_id in self._running_tasks:
            task = self._running_tasks[task_id]
            task.cancel()
            self._tasks[task_id].status = TaskStatus.CANCELLED
            return True
        return False

    async def health_check(self) -> bool:
        return True

    def get_stats(self) -> dict:
        """获取队列统计"""
        stats = {status: 0 for status in TaskStatus}
        for result in self._tasks.values():
            stats[result.status] += 1
        return {
            "total": len(self._tasks),
            "by_status": stats,
            "max_workers": self.max_workers,
        }


class CeleryTaskQueue(TaskQueue):
    """
    Celery 任务队列

    适用场景：
    - 生产环境
    - 分布式部署
    - 高并发任务
    """

    def __init__(self, celery_app):
        self.celery = celery_app

    async def enqueue(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict = None,
        config: TaskConfig = None,
    ) -> str:
        config = config or TaskConfig()

        # 发送任务到 Celery
        result = self.celery.send_task(
            task_name,
            args=args,
            kwargs=kwargs or {},
            queue=config.queue,
            priority=config.priority.value,
            retry=True,
            retry_policy={
                "max_retries": config.max_retries,
                "interval_start": config.retry_delay,
            },
        )

        return result.id

    async def get_status(self, task_id: str) -> Optional[TaskResult]:
        result = self.celery.AsyncResult(task_id)

        status_map = {
            "PENDING": TaskStatus.PENDING,
            "STARTED": TaskStatus.RUNNING,
            "SUCCESS": TaskStatus.COMPLETED,
            "FAILURE": TaskStatus.FAILED,
            "RETRY": TaskStatus.RETRY,
            "REVOKED": TaskStatus.CANCELLED,
        }

        return TaskResult(
            task_id=task_id,
            status=status_map.get(result.state, TaskStatus.PENDING),
            result=result.result if result.state == "SUCCESS" else None,
            error=str(result.result) if result.state == "FAILURE" else None,
        )

    async def cancel(self, task_id: str) -> bool:
        self.celery.control.revoke(task_id, terminate=True)
        return True

    async def health_check(self) -> bool:
        try:
            inspect = self.celery.control.inspect()
            return inspect.ping() is not None
        except Exception:
            return False


class TaskManager:
    """任务管理器 - 统一管理任务队列"""

    def __init__(self):
        self.settings = get_settings()
        self._queue: Optional[TaskQueue] = None

    async def initialize(self):
        """初始化任务队列"""
        if self.settings.celery.use_celery:
            # 使用 Celery
            try:
                from celery import Celery

                celery_app = Celery(
                    "newflow",
                    broker=self.settings.celery.celery_broker_url,
                    backend=self.settings.celery.celery_result_backend,
                )
                celery_app.conf.update(
                    worker_concurrency=self.settings.celery.celery_worker_concurrency,
                    task_serializer="json",
                    accept_content=["json"],
                    result_serializer="json",
                    timezone="UTC",
                    enable_utc=True,
                )

                self._queue = CeleryTaskQueue(celery_app)
                logger.info("Task queue initialized: Celery")
            except ImportError:
                logger.warning("Celery not installed, falling back to SimpleTaskQueue")
                self._queue = SimpleTaskQueue()
        else:
            # 使用简单队列
            self._queue = SimpleTaskQueue()
            logger.info("Task queue initialized: SimpleTaskQueue")

    @property
    def queue(self) -> TaskQueue:
        if not self._queue:
            raise RuntimeError("Task queue not initialized")
        return self._queue

    async def enqueue(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict = None,
        config: TaskConfig = None,
    ) -> str:
        return await self.queue.enqueue(task_name, args, kwargs, config)

    async def get_status(self, task_id: str) -> Optional[TaskResult]:
        return await self.queue.get_status(task_id)

    async def cancel(self, task_id: str) -> bool:
        return await self.queue.cancel(task_id)

    async def health_check(self) -> bool:
        return await self.queue.health_check()


# 任务注册表
_task_registry: Dict[str, Callable] = {}


def task(
    name: str,
    max_retries: int = 3,
    retry_delay: int = 60,
    timeout: int = 300,
    queue: str = "default",
):
    """
    任务装饰器

    用法：
    @task("generate_summary", max_retries=3)
    async def generate_summary(article_id: str, title: str, content: str):
        ...
    """
    def decorator(func):
        _task_registry[name] = func

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        wrapper.task_name = name
        wrapper.task_config = TaskConfig(
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            queue=queue,
        )
        return wrapper
    return decorator


# 全局任务管理器实例
task_manager = TaskManager()


async def init_tasks():
    """初始化任务队列"""
    await task_manager.initialize()

    # 注册所有已装饰的任务
    if isinstance(task_manager._queue, SimpleTaskQueue):
        for name, func in _task_registry.items():
            task_manager._queue.register_task(name, func)


async def enqueue_task(
    task_name: str,
    args: tuple = (),
    kwargs: dict = None,
    config: TaskConfig = None,
) -> str:
    """便捷的入队函数"""
    return await task_manager.enqueue(task_name, args, kwargs, config)
