"""
存储模块 - 支持本地存储、S3、GCS，可无缝切换
"""

from typing import Optional, BinaryIO, Dict, List
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
import hashlib
import uuid
import aiofiles
import logging

from .config import get_settings

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """存储后端抽象接口"""

    @abstractmethod
    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Dict = None,
    ) -> str:
        """
        上传文件

        Args:
            key: 文件键（路径）
            data: 文件数据
            content_type: 内容类型
            metadata: 元数据

        Returns:
            文件 URL
        """
        pass

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """下载文件"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查是否存在"""
        pass

    @abstractmethod
    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        """获取访问 URL（支持签名 URL）"""
        pass

    @abstractmethod
    async def list_files(self, prefix: str = "") -> List[str]:
        """列出文件"""
        pass

    @abstractmethod
    async def get_metadata(self, key: str) -> Optional[Dict]:
        """获取文件元数据"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass


class LocalStorage(StorageBackend):
    """
    本地文件存储

    适用场景：
    - 开发环境
    - 单机部署
    - 小规模存储
    """

    def __init__(self, base_path: str = "./uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, key: str) -> Path:
        """获取完整文件路径"""
        return self.base_path / key

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Dict = None,
    ) -> str:
        file_path = self._get_full_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(data)

        # 保存元数据
        if metadata:
            meta_path = file_path.with_suffix(file_path.suffix + ".meta")
            import json
            async with aiofiles.open(meta_path, "w") as f:
                await f.write(json.dumps(metadata))

        logger.info(f"File uploaded: {key} ({len(data)} bytes)")
        return f"/uploads/{key}"

    async def download(self, key: str) -> bytes:
        file_path = self._get_full_path(key)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {key}")

        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    async def delete(self, key: str) -> bool:
        file_path = self._get_full_path(key)

        if file_path.exists():
            file_path.unlink()
            # 删除元数据
            meta_path = file_path.with_suffix(file_path.suffix + ".meta")
            if meta_path.exists():
                meta_path.unlink()
            logger.info(f"File deleted: {key}")
            return True
        return False

    async def exists(self, key: str) -> bool:
        return self._get_full_path(key).exists()

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        # 本地存储直接返回相对路径
        return f"/uploads/{key}"

    async def list_files(self, prefix: str = "") -> List[str]:
        base = self.base_path / prefix if prefix else self.base_path
        files = []

        if base.exists():
            for file_path in base.rglob("*"):
                if file_path.is_file() and not file_path.suffix == ".meta":
                    relative = file_path.relative_to(self.base_path)
                    files.append(str(relative))

        return files

    async def get_metadata(self, key: str) -> Optional[Dict]:
        file_path = self._get_full_path(key)
        meta_path = file_path.with_suffix(file_path.suffix + ".meta")

        if meta_path.exists():
            import json
            async with aiofiles.open(meta_path, "r") as f:
                return json.loads(await f.read())
        return None

    async def health_check(self) -> bool:
        return self.base_path.exists() and self.base_path.is_dir()


class S3Storage(StorageBackend):
    """
    S3 兼容存储

    适用场景：
    - 生产环境
    - 分布式部署
    - 大规模存储
    """

    def __init__(
        self,
        bucket: str,
        region: str = None,
        access_key: str = None,
        secret_key: str = None,
        endpoint_url: str = None,
    ):
        self.bucket = bucket
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint_url = endpoint_url
        self._client = None

    async def _get_client(self):
        """获取 S3 客户端（延迟初始化）"""
        if self._client is None:
            try:
                import aioboto3
                session = aioboto3.Session()
                self._client = await session.client(
                    "s3",
                    region_name=self.region,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    endpoint_url=self.endpoint_url,
                ).__aenter__()
            except ImportError:
                raise ImportError("aioboto3 is required for S3 storage")
        return self._client

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Dict = None,
    ) -> str:
        client = await self._get_client()

        extra_args = {"ContentType": content_type}
        if metadata:
            extra_args["Metadata"] = {k: str(v) for k, v in metadata.items()}

        await client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            **extra_args,
        )

        logger.info(f"File uploaded to S3: {key} ({len(data)} bytes)")

        # 返回 URL
        if self.endpoint_url:
            return f"{self.endpoint_url}/{self.bucket}/{key}"
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"

    async def download(self, key: str) -> bytes:
        client = await self._get_client()

        response = await client.get_object(Bucket=self.bucket, Key=key)
        return await response["Body"].read()

    async def delete(self, key: str) -> bool:
        client = await self._get_client()

        try:
            await client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"File deleted from S3: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False

    async def exists(self, key: str) -> bool:
        client = await self._get_client()

        try:
            await client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        client = await self._get_client()

        url = await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return url

    async def list_files(self, prefix: str = "") -> List[str]:
        client = await self._get_client()

        response = await client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix,
        )

        return [obj["Key"] for obj in response.get("Contents", [])]

    async def get_metadata(self, key: str) -> Optional[Dict]:
        client = await self._get_client()

        try:
            response = await client.head_object(Bucket=self.bucket, Key=key)
            return response.get("Metadata")
        except Exception:
            return None

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            await client.head_bucket(Bucket=self.bucket)
            return True
        except Exception:
            return False

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None


class StorageManager:
    """存储管理器 - 统一管理存储后端"""

    def __init__(self):
        self.settings = get_settings()
        self._backend: Optional[StorageBackend] = None

    async def initialize(self):
        """初始化存储后端"""
        storage_type = self.settings.storage.storage_type

        if storage_type == "s3":
            self._backend = S3Storage(
                bucket=self.settings.storage.s3_bucket,
                region=self.settings.storage.s3_region,
                access_key=self.settings.storage.s3_access_key,
                secret_key=self.settings.storage.s3_secret_key,
                endpoint_url=self.settings.storage.s3_endpoint_url,
            )
            logger.info("Storage initialized: S3")
        else:
            self._backend = LocalStorage(
                base_path=self.settings.storage.storage_base_path,
            )
            logger.info("Storage initialized: Local")

    @property
    def backend(self) -> StorageBackend:
        if not self._backend:
            raise RuntimeError("Storage not initialized")
        return self._backend

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Dict = None,
    ) -> str:
        return await self.backend.upload(key, data, content_type, metadata)

    async def download(self, key: str) -> bytes:
        return await self.backend.download(key)

    async def delete(self, key: str) -> bool:
        return await self.backend.delete(key)

    async def exists(self, key: str) -> bool:
        return await self.backend.exists(key)

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        url = await self.backend.get_url(key, expires_in)

        # 如果配置了 CDN，替换为 CDN URL
        if self.settings.storage.cdn_domain:
            url = url.replace(
                f"https://{self.settings.storage.s3_bucket}.s3.amazonaws.com",
                f"https://{self.settings.storage.cdn_domain}",
            )

        return url

    async def list_files(self, prefix: str = "") -> List[str]:
        return await self.backend.list_files(prefix)

    async def get_metadata(self, key: str) -> Optional[Dict]:
        return await self.backend.get_metadata(key)

    async def generate_key(
        self,
        prefix: str,
        filename: str,
        user_id: str = None,
    ) -> str:
        """生成唯一的文件键"""
        # 生成唯一 ID
        unique_id = str(uuid.uuid4())[:8]

        # 获取文件扩展名
        ext = Path(filename).suffix

        # 构建键
        parts = [prefix]
        if user_id:
            parts.append(user_id)
        parts.append(f"{unique_id}{ext}")

        return "/".join(parts)

    async def health_check(self) -> bool:
        return await self.backend.health_check()


# 全局存储管理器实例
storage_manager = StorageManager()


async def init_storage():
    """初始化存储"""
    await storage_manager.initialize()


async def close_storage():
    """关闭存储"""
    if hasattr(storage_manager._backend, "close"):
        await storage_manager._backend.close()
