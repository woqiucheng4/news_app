"""
AI 服务模块 - 支持多模型、批量调用、成本控制
"""

from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

from .config import get_settings
from .cache import cached, cache_manager

logger = logging.getLogger(__name__)


class AIModel(Enum):
    """AI 模型"""
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"
    DEEPSEEK_CHAT = "deepseek-chat"
    DEEPSEEK_REASONER = "deepseek-reasoner"
    CLAUDE_HAIKU = "claude-haiku-4-5-20251001"
    CLAUDE_SONNET = "claude-sonnet-4-20250514"


def resolve_chat_model(model_name: Optional[str] = None) -> AIModel:
    """Map configured OPENAI_MODEL string to AIModel."""
    name = (model_name or get_settings().ai.openai_model).strip()
    for candidate in AIModel:
        if candidate.value == name:
            return candidate
    return AIModel.GPT_4O_MINI


@dataclass
class AIRequest:
    """AI 请求"""
    prompt: str
    system_prompt: str = ""
    max_tokens: int = 150
    temperature: float = 0.3
    model: AIModel = AIModel.GPT_4O_MINI


@dataclass
class AIResponse:
    """AI 响应"""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    cached: bool = False


class AIServiceBackend(ABC):
    """AI 服务后端抽象接口"""

    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:
        """生成内容"""
        pass

    @abstractmethod
    async def batch_generate(self, requests: List[AIRequest]) -> List[AIResponse]:
        """批量生成"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass


class OpenAIBackend(AIServiceBackend):
    """OpenAI 后端"""

    PRICING = {
        "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
        "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
        "deepseek-chat": {"input": 0.27 / 1_000_000, "output": 1.10 / 1_000_000},
        "deepseek-reasoner": {"input": 0.55 / 1_000_000, "output": 2.19 / 1_000_000},
    }

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key
        self.default_model = model
        self.base_url = base_url.rstrip("/") if base_url else None
        self._client = None

    async def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                kwargs: Dict[str, Any] = {"api_key": self.api_key}
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                self._client = AsyncOpenAI(**kwargs)
            except ImportError:
                raise ImportError("openai package is required")
        return self._client

    async def generate(self, request: AIRequest) -> AIResponse:
        client = await self._get_client()

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        response = await client.chat.completions.create(
            model=request.model.value,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        # 计算成本
        pricing = self.PRICING.get(request.model.value, self.PRICING["gpt-4o-mini"])
        input_cost = response.usage.prompt_tokens * pricing["input"]
        output_cost = response.usage.completion_tokens * pricing["output"]
        total_cost = input_cost + output_cost

        return AIResponse(
            content=response.choices[0].message.content.strip(),
            model=request.model.value,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            cost_usd=total_cost,
        )

    async def batch_generate(self, requests: List[AIRequest]) -> List[AIResponse]:
        """并发批量生成"""
        semaphore = asyncio.Semaphore(50)  # 并发限制

        async def process_one(req: AIRequest) -> AIResponse:
            async with semaphore:
                return await self.generate(req)

        tasks = [process_one(req) for req in requests]
        return await asyncio.gather(*tasks, return_exceptions=False)

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            # 简单测试
            await client.chat.completions.create(
                model=self.default_model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False


class AnthropicBackend(AIServiceBackend):
    """Anthropic 后端"""

    PRICING = {
        "claude-haiku-4-5-20251001": {"input": 1.00 / 1_000_000, "output": 5.00 / 1_000_000},
        "claude-sonnet-4-20250514": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
    }

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001"):
        self.api_key = api_key
        self.default_model = model
        self._client = None

    async def _get_client(self):
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package is required")
        return self._client

    async def generate(self, request: AIRequest) -> AIResponse:
        client = await self._get_client()

        response = await client.messages.create(
            model=request.model.value,
            max_tokens=request.max_tokens,
            system=request.system_prompt or "You are a helpful assistant.",
            messages=[{"role": "user", "content": request.prompt}],
        )

        # 计算成本
        pricing = self.PRICING.get(request.model.value, self.PRICING["claude-haiku-4-5-20251001"])
        input_cost = response.usage.input_tokens * pricing["input"]
        output_cost = response.usage.output_tokens * pricing["output"]
        total_cost = input_cost + output_cost

        return AIResponse(
            content=response.content[0].text.strip(),
            model=request.model.value,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            cost_usd=total_cost,
        )

    async def batch_generate(self, requests: List[AIRequest]) -> List[AIResponse]:
        semaphore = asyncio.Semaphore(20)

        async def process_one(req: AIRequest) -> AIResponse:
            async with semaphore:
                return await self.generate(req)

        tasks = [process_one(req) for req in requests]
        return await asyncio.gather(*tasks, return_exceptions=False)

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            await client.messages.create(
                model=self.default_model,
                max_tokens=5,
                messages=[{"role": "user", "content": "test"}],
            )
            return True
        except Exception:
            return False


class CostTracker:
    """成本追踪器"""

    def __init__(self, daily_budget: float, monthly_budget: float):
        self.daily_budget = daily_budget
        self.monthly_budget = monthly_budget
        self._daily_cost: float = 0.0
        self._monthly_cost: float = 0.0

    async def check_budget(self, estimated_cost: float) -> bool:
        """检查预算是否充足"""
        if self._daily_cost + estimated_cost > self.daily_budget:
            logger.warning(f"Daily budget exceeded: {self._daily_cost:.4f} + {estimated_cost:.4f}")
            return False
        return True

    async def record_cost(self, cost: float):
        """记录成本"""
        self._daily_cost += cost
        self._monthly_cost += cost

    async def get_stats(self) -> dict:
        """获取统计"""
        return {
            "daily_cost": self._daily_cost,
            "daily_budget": self.daily_budget,
            "daily_remaining": max(0, self.daily_budget - self._daily_cost),
            "daily_usage_percent": (self._daily_cost / self.daily_budget * 100) if self.daily_budget > 0 else 0,
            "monthly_cost": self._monthly_cost,
            "monthly_budget": self.monthly_budget,
            "monthly_remaining": max(0, self.monthly_budget - self._monthly_cost),
        }

    async def reset_daily(self):
        """重置每日统计"""
        self._daily_cost = 0.0

    async def reset_monthly(self):
        """重置每月统计"""
        self._monthly_cost = 0.0


class AIServiceManager:
    """AI 服务管理器 - 统一管理 AI 服务"""

    def __init__(self):
        self.settings = get_settings()
        self._backends: Dict[str, AIServiceBackend] = {}
        self._cost_tracker: Optional[CostTracker] = None

    async def initialize(self):
        """初始化 AI 服务"""
        # OpenAI
        if self.settings.ai.openai_api_key:
            self._backends["openai"] = OpenAIBackend(
                api_key=self.settings.ai.openai_api_key,
                model=self.settings.ai.openai_model,
                base_url=self.settings.ai.openai_base_url,
            )
            provider = "DeepSeek" if self.settings.ai.openai_base_url else "OpenAI"
            logger.info("AI backend initialized: %s (%s)", provider, self.settings.ai.openai_model)

        # Anthropic
        if self.settings.ai.anthropic_api_key:
            self._backends["anthropic"] = AnthropicBackend(
                api_key=self.settings.ai.anthropic_api_key,
                model=self.settings.ai.anthropic_model,
            )
            logger.info("AI backend initialized: Anthropic")

        # 成本追踪
        self._cost_tracker = CostTracker(
            daily_budget=self.settings.ai.ai_daily_budget_usd,
            monthly_budget=self.settings.ai.ai_monthly_budget_usd,
        )

    def _get_backend(self, model: AIModel) -> AIServiceBackend:
        """获取后端"""
        if model.value.startswith("gpt") or model.value.startswith("deepseek"):
            return self._backends.get("openai")
        elif model.value.startswith("claude"):
            return self._backends.get("anthropic")
        else:
            return self._backends.get("openai")

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        model: AIModel = AIModel.GPT_4O_MINI,
        max_tokens: int = 150,
        temperature: float = 0.3,
        use_cache: bool = True,
    ) -> AIResponse:
        """
        生成内容

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            model: AI 模型
            max_tokens: 最大 token 数
            temperature: 温度
            use_cache: 是否使用缓存

        Returns:
            AI 响应
        """
        backend = self._get_backend(model)
        if not backend:
            raise ValueError(f"No backend available for model: {model}")

        # 检查缓存
        if use_cache:
            cache_key_str = f"ai:{model.value}:{hash(prompt)}"
            cached_result = await cache_manager.get(cache_key_str)
            if cached_result:
                cached_result["cached"] = True
                return AIResponse(**cached_result)

        # 检查预算
        estimated_cost = self._estimate_cost(prompt, max_tokens, model)
        if not await self._cost_tracker.check_budget(estimated_cost):
            # 降级到更便宜的模型
            fallback = resolve_chat_model()
            if model != fallback:
                logger.warning("Budget exceeded, degrading to %s", fallback.value)
                model = fallback
                backend = self._get_backend(model)
                estimated_cost = self._estimate_cost(prompt, max_tokens, model)

        # 生成
        request = AIRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model,
        )

        response = await backend.generate(request)

        # 记录成本
        await self._cost_tracker.record_cost(response.cost_usd)

        # 缓存结果
        if use_cache:
            await cache_manager.set(
                cache_key_str,
                {
                    "content": response.content,
                    "model": response.model,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "total_tokens": response.total_tokens,
                    "cost_usd": response.cost_usd,
                },
                ttl=86400 * 7,  # 缓存 7 天
            )

        return response

    async def batch_generate(
        self,
        requests: List[Dict[str, Any]],
        model: AIModel = AIModel.GPT_4O_MINI,
    ) -> List[AIResponse]:
        """批量生成"""
        backend = self._get_backend(model)
        if not backend:
            raise ValueError(f"No backend available for model: {model}")

        ai_requests = [
            AIRequest(
                prompt=req["prompt"],
                system_prompt=req.get("system_prompt", ""),
                max_tokens=req.get("max_tokens", 150),
                temperature=req.get("temperature", 0.3),
                model=model,
            )
            for req in requests
        ]

        responses = await backend.batch_generate(ai_requests)

        # 记录成本
        for response in responses:
            await self._cost_tracker.record_cost(response.cost_usd)

        return responses

    def _estimate_cost(self, prompt: str, max_tokens: int, model: AIModel) -> float:
        """估算成本"""
        # 粗略估算：1 token ≈ 4 字符
        input_tokens = len(prompt) / 4
        output_tokens = max_tokens

        pricing = OpenAIBackend.PRICING.get(
            model.value,
            OpenAIBackend.PRICING["gpt-4o-mini"],
        )

        return (input_tokens * pricing["input"]) + (output_tokens * pricing["output"])

    async def get_cost_stats(self) -> dict:
        """获取成本统计"""
        return await self._cost_tracker.get_stats()

    async def health_check(self) -> dict:
        """健康检查"""
        results = {}
        for name, backend in self._backends.items():
            results[name] = await backend.health_check()
        return results


# 摘要生成提示词
SUMMARY_SYSTEM_PROMPT = """你是一位专业的新闻摘要编辑。

任务：将输入的文章转换为简洁、准确、客观的摘要。

要求：
1. 长度：2-3 句话，总计 50-100 字
2. 内容：仅包含核心事实，不添加评论或推测
3. 语言：与原文语言一致
4. 格式：纯文本，无列表、无标题

禁止：
- 不要复制原文句子，用自己的话重新表述
- 不要添加"根据报道"、"据悉"等引导词
- 不要包含个人观点或情感倾向
- 不要猜测未明确说明的信息"""


# 全局 AI 服务管理器实例
ai_manager = AIServiceManager()


async def init_ai():
    """初始化 AI 服务"""
    await ai_manager.initialize()


async def generate_summary(
    title: str,
    content: str,
    source: str = "",
    model: AIModel = AIModel.GPT_4O_MINI,
) -> AIResponse:
    """便捷的摘要生成函数"""
    prompt = f"标题：{title}\n来源：{source}\n\n{content}"
    return await ai_manager.generate(
        prompt=prompt,
        system_prompt=SUMMARY_SYSTEM_PROMPT,
        model=model,
        max_tokens=150,
        temperature=0.3,
    )
