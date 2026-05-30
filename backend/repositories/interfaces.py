"""
Repository 接口定义 - 数据访问层抽象
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime, date


class IRepository(ABC):
    """Repository 基接口"""

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Any]:
        """根据 ID 获取"""
        pass

    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> Any:
        """创建"""
        pass

    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Any]:
        """更新"""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """删除（软删除）"""
        pass

    @abstractmethod
    async def list(
        self,
        filters: Dict[str, Any] = None,
        order_by: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Any]:
        """列表查询"""
        pass

    @abstractmethod
    async def count(self, filters: Dict[str, Any] = None) -> int:
        """计数"""
        pass


class IUserRepository(IRepository):
    """用户 Repository 接口"""

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Any]:
        """根据邮箱获取用户"""
        pass

    @abstractmethod
    async def get_by_supabase_uid(self, uid: str) -> Optional[Any]:
        """根据 Supabase UID 获取用户"""
        pass

    @abstractmethod
    async def get_by_google_id(self, google_id: str) -> Optional[Any]:
        """根据 Google ID 获取用户"""
        pass

    @abstractmethod
    async def get_by_apple_id(self, apple_id: str) -> Optional[Any]:
        """根据 Apple ID 获取用户"""
        pass


class IArticleRepository(IRepository):
    """文章 Repository 接口"""

    @abstractmethod
    async def get_by_url_hash(self, url_hash: str) -> Optional[Any]:
        """根据 URL 哈希获取文章"""
        pass

    @abstractmethod
    async def get_by_event_id(self, event_id: str) -> List[Any]:
        """根据事件 ID 获取文章列表"""
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> List[Any]:
        """全文搜索"""
        pass

    @abstractmethod
    async def get_recent(self, category: str = None, limit: int = 20) -> List[Any]:
        """获取最近文章"""
        pass

    @abstractmethod
    async def get_unsummarized(self, limit: int = 100) -> List[Any]:
        """获取未生成摘要的文章"""
        pass

    @abstractmethod
    async def update_summary(
        self,
        id: str,
        summary: str,
        model: str,
        relevance_score: Optional[float] = None,
    ) -> bool:
        """更新摘要"""
        pass


class ISourceRepository(IRepository):
    """信息源 Repository 接口"""

    @abstractmethod
    async def get_active_sources(self) -> List[Any]:
        """获取活跃的信息源"""
        pass

    @abstractmethod
    async def get_by_feed_url(self, feed_url: str) -> Optional[Any]:
        """根据 Feed URL 获取信息源"""
        pass

    @abstractmethod
    async def update_fetch_status(
        self,
        id: str,
        success: bool,
        error: str = None,
    ) -> bool:
        """更新抓取状态"""
        pass


class ITopicRepository(IRepository):
    """话题 Repository 接口"""

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Any]:
        """根据 slug 获取话题"""
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> List[Any]:
        """搜索话题"""
        pass

    @abstractmethod
    async def get_popular(self, limit: int = 20) -> List[Any]:
        """获取热门话题"""
        pass

    @abstractmethod
    async def get_by_category(self, category: str) -> List[Any]:
        """根据分类获取话题"""
        pass


class ISubscriptionRepository(IRepository):
    """订阅 Repository 接口"""

    @abstractmethod
    async def get_user_subscriptions(self, user_id: str) -> List[Any]:
        """获取用户的所有订阅"""
        pass

    @abstractmethod
    async def is_subscribed(self, user_id: str, topic_id: str) -> bool:
        """检查是否已订阅"""
        pass

    @abstractmethod
    async def get_topic_subscribers(self, topic_id: str) -> List[str]:
        """获取话题的订阅者列表"""
        pass


class INotificationRepository(IRepository):
    """通知 Repository 接口"""

    @abstractmethod
    async def get_user_notifications(
        self,
        user_id: str,
        is_read: bool = None,
        limit: int = 50,
    ) -> List[Any]:
        """获取用户通知"""
        pass

    @abstractmethod
    async def mark_as_read(self, id: str) -> bool:
        """标记为已读"""
        pass

    @abstractmethod
    async def mark_all_as_read(self, user_id: str) -> int:
        """标记所有为已读"""
        pass

    @abstractmethod
    async def get_unpushed(self, limit: int = 100) -> List[Any]:
        """获取未推送的通知"""
        pass


class IEventRepository(IRepository):
    """事件 Repository 接口"""

    @abstractmethod
    async def get_recent(self, category: str = None, limit: int = 20) -> List[Any]:
        """获取最近事件"""
        pass

    @abstractmethod
    async def get_by_article_hash(self, content_hash: str) -> Optional[Any]:
        """根据文章哈希查找匹配的事件"""
        pass

    @abstractmethod
    async def update_article_count(self, id: str, increment: int = 1) -> bool:
        """更新文章计数"""
        pass


class ICostRepository(IRepository):
    """成本 Repository 接口"""

    @abstractmethod
    async def log_usage(self, data: Dict[str, Any]) -> Any:
        """记录 API 使用"""
        pass

    @abstractmethod
    async def get_daily_summary(self, date: date) -> Optional[Any]:
        """获取每日汇总"""
        pass

    @abstractmethod
    async def get_cost_trend(self, days: int = 7) -> List[Any]:
        """获取成本趋势"""
        pass

    @abstractmethod
    async def get_cost_by_model(self, date: date) -> List[Dict]:
        """按模型获取成本"""
        pass

    @abstractmethod
    async def get_total_cost(self, start_date: date, end_date: date) -> float:
        """获取时间区间总成本"""
        pass
