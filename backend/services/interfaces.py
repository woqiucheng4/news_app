"""
Service 接口定义 - 业务逻辑层抽象
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime


class IArticleService(ABC):
    """文章服务接口"""

    @abstractmethod
    async def get_article(self, id: str) -> Optional[Dict]:
        """获取文章详情"""
        pass

    @abstractmethod
    async def get_feed(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        topic_id: Optional[str] = None,
        topic_name: Optional[str] = None,
    ) -> Dict:
        """获取用户信息流"""
        pass

    @abstractmethod
    async def search_articles(self, query: str, limit: int = 20) -> List[Dict]:
        """搜索文章"""
        pass

    @abstractmethod
    async def get_trending(self, limit: int = 20) -> List[Dict]:
        """获取热门事件"""
        pass

    @abstractmethod
    async def generate_summary(self, article_id: str) -> Optional[str]:
        """生成摘要"""
        pass


class IUserService(ABC):
    """用户服务接口"""

    @abstractmethod
    async def get_user(self, id: str) -> Optional[Dict]:
        """获取用户信息"""
        pass

    @abstractmethod
    async def get_or_create_by_oauth(
        self,
        email: str,
        provider: str,
        provider_id: str,
        **kwargs,
    ) -> Dict:
        """通过 OAuth 获取或创建用户"""
        pass

    @abstractmethod
    async def update_settings(self, user_id: str, settings: Dict) -> bool:
        """更新用户设置"""
        pass

    @abstractmethod
    async def export_user_data(self, user_id: str) -> Dict:
        """导出用户数据（GDPR）"""
        pass

    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """删除用户（GDPR）"""
        pass


class ISubscriptionService(ABC):
    """订阅服务接口"""

    @abstractmethod
    async def subscribe(self, user_id: str, topic_id: str) -> bool:
        """订阅话题"""
        pass

    @abstractmethod
    async def unsubscribe(self, user_id: str, topic_id: str) -> bool:
        """取消订阅"""
        pass

    @abstractmethod
    async def get_user_subscriptions(self, user_id: str) -> List[Dict]:
        """获取用户订阅列表"""
        pass

    @abstractmethod
    async def get_recommended_topics(self, user_id: str, limit: int = 10) -> List[Dict]:
        """获取推荐话题"""
        pass


class INotificationService(ABC):
    """通知服务接口"""

    @abstractmethod
    async def send_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        notification_type: str,
        **kwargs,
    ) -> bool:
        """发送通知"""
        pass

    @abstractmethod
    async def send_push(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Dict = None,
    ) -> bool:
        """发送推送"""
        pass

    @abstractmethod
    async def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
    ) -> List[Dict]:
        """获取用户通知"""
        pass

    @abstractmethod
    async def mark_as_read(self, notification_id: str) -> bool:
        """标记为已读"""
        pass

    @abstractmethod
    async def generate_daily_briefing(self, user_id: str) -> Optional[str]:
        """生成每日简报"""
        pass


class IContentIngestionService(ABC):
    """内容采集服务接口"""

    @abstractmethod
    async def fetch_feed(self, source_id: str) -> List[Dict]:
        """抓取单个信息源"""
        pass

    @abstractmethod
    async def fetch_all_feeds(self) -> Dict:
        """抓取所有信息源"""
        pass

    @abstractmethod
    async def crawl_hot_topics(self) -> List[Dict]:
        """抓取热点话题"""
        pass

    @abstractmethod
    async def process_article(self, article_data: Dict) -> Optional[str]:
        """处理文章（去重、存储、生成摘要）"""
        pass


class IDeduplicationService(ABC):
    """去重服务接口"""

    @abstractmethod
    async def check_duplicate(self, article_data: Dict) -> Dict:
        """
        检查是否重复

        返回：
        {
            "is_duplicate": bool,
            "duplicate_of": str,  # 重复的文章 ID
            "event_id": str,      # 所属事件 ID
            "similarity": float,
            "layer": str,         # 在哪一层被判定为重复
        }
        """
        pass

    @abstractmethod
    async def find_similar_articles(
        self,
        title: str,
        content: str,
        limit: int = 10,
    ) -> List[Dict]:
        """查找相似文章"""
        pass

    @abstractmethod
    async def cluster_articles(self, articles: List[Dict]) -> List[List[str]]:
        """文章聚类"""
        pass


class ICostService(ABC):
    """成本服务接口"""

    @abstractmethod
    async def record_usage(self, data: Dict) -> bool:
        """记录 API 使用"""
        pass

    @abstractmethod
    async def get_daily_summary(self, date: datetime = None) -> Dict:
        """获取每日成本摘要"""
        pass

    @abstractmethod
    async def get_cost_trend(self, days: int = 7) -> List[Dict]:
        """获取成本趋势"""
        pass

    @abstractmethod
    async def check_budget(self, estimated_cost: float) -> bool:
        """检查预算"""
        pass

    @abstractmethod
    async def get_degradation_level(self) -> str:
        """获取降级级别"""
        pass
