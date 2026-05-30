"""
认证 API：注册、登录、OAuth、刷新 token。
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from core.cache import cache_manager
from core.dependencies import get_db
from repositories.sqlalchemy.user import UserRepository
from services.auth import AuthService

router = APIRouter()

LOGIN_RATE_LIMIT = 10
LOGIN_RATE_LIMIT_WINDOW_SECONDS = 60
REGISTER_RATE_LIMIT = 5
REGISTER_RATE_LIMIT_WINDOW_SECONDS = 300
REFRESH_RATE_LIMIT = 30
REFRESH_RATE_LIMIT_WINDOW_SECONDS = 60


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class OAuthLoginRequest(BaseModel):
    provider_id: str = Field(min_length=1, max_length=255)
    email: EmailStr
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


async def get_auth_service(db=Depends(get_db)) -> AuthService:
    repo = UserRepository(db)
    return AuthService(repo)


def _build_login_rate_limit_key(request: Request, email: str) -> str:
    ip = _get_client_ip(request)
    return f"rate_limit:auth_login:{ip}:{email.lower()}"


def _build_auth_rate_limit_key(request: Request, scope: str, identifier: Optional[str] = None) -> str:
    ip = _get_client_ip(request)
    suffix = f":{identifier.lower()}" if identifier else ""
    return f"rate_limit:auth:{scope}:{ip}{suffix}"


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _set_rate_limit_headers(response: Response, limit: int, remaining: int, reset_seconds: int) -> None:
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
    response.headers["X-RateLimit-Reset"] = str(max(0, reset_seconds))


def _build_rate_limit_headers(limit: int, remaining: int, reset_seconds: int) -> dict[str, str]:
    return {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(max(0, remaining)),
        "X-RateLimit-Reset": str(max(0, reset_seconds)),
    }


async def _consume_rate_limit_slot(key: str, limit: int, window_seconds: int):
    redis_client = cache_manager._redis_client
    if not redis_client:
        return None
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, window_seconds)
    ttl = await redis_client.ttl(key)
    if ttl < 0:
        ttl = window_seconds
    allowed = count <= limit
    remaining = max(0, limit - count)
    return allowed, remaining, ttl


async def _get_login_failure_state(key: str):
    redis_client = cache_manager._redis_client
    if not redis_client:
        return None
    raw = await redis_client.get(key)
    ttl = await redis_client.ttl(key)
    if ttl < 0:
        ttl = LOGIN_RATE_LIMIT_WINDOW_SECONDS
    if not raw:
        return 0, ttl
    try:
        return int(raw), ttl
    except (TypeError, ValueError):
        return 0, ttl


async def _track_login_failure(key: str) -> None:
    redis_client = cache_manager._redis_client
    if not redis_client:
        return None
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, LOGIN_RATE_LIMIT_WINDOW_SECONDS)
    ttl = await redis_client.ttl(key)
    if ttl < 0:
        ttl = LOGIN_RATE_LIMIT_WINDOW_SECONDS
    return count, ttl


async def _clear_login_failures(key: str) -> None:
    redis_client = cache_manager._redis_client
    if not redis_client:
        return
    await redis_client.delete(key)


@router.post("/register")
async def register(
    http_request: Request,
    response: Response,
    request: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
):
    rate_limit_key = _build_auth_rate_limit_key(http_request, "register", request.email)
    rate_limit = await _consume_rate_limit_slot(
        rate_limit_key,
        REGISTER_RATE_LIMIT,
        REGISTER_RATE_LIMIT_WINDOW_SECONDS,
    )
    if rate_limit:
        allowed, remaining, reset_seconds = rate_limit
        _set_rate_limit_headers(response, REGISTER_RATE_LIMIT, remaining, reset_seconds)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many register attempts. Please try again later.",
                headers=_build_rate_limit_headers(REGISTER_RATE_LIMIT, remaining, reset_seconds),
            )

    try:
        return await service.register(
            email=request.email,
            password=request.password,
            display_name=request.display_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/login")
async def login(
    http_request: Request,
    response: Response,
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    rate_limit_key = _build_login_rate_limit_key(http_request, payload.email)
    failure_state = await _get_login_failure_state(rate_limit_key)
    if failure_state:
        failure_count, reset_seconds = failure_state
        _set_rate_limit_headers(
            response,
            LOGIN_RATE_LIMIT,
            LOGIN_RATE_LIMIT - failure_count,
            reset_seconds,
        )
        if failure_count >= LOGIN_RATE_LIMIT:
            raise HTTPException(
                status_code=429,
                detail="Too many login attempts. Please try again later.",
                headers=_build_rate_limit_headers(LOGIN_RATE_LIMIT, LOGIN_RATE_LIMIT - failure_count, reset_seconds),
            )

    try:
        result = await service.login(email=payload.email, password=payload.password)
        await _clear_login_failures(rate_limit_key)
        _set_rate_limit_headers(response, LOGIN_RATE_LIMIT, LOGIN_RATE_LIMIT, 0)
        return result
    except ValueError as exc:
        tracked = await _track_login_failure(rate_limit_key)
        if tracked:
            failure_count, reset_seconds = tracked
            _set_rate_limit_headers(
                response,
                LOGIN_RATE_LIMIT,
                LOGIN_RATE_LIMIT - failure_count,
                reset_seconds,
            )
        raise HTTPException(status_code=401, detail=str(exc))


@router.post("/oauth/{provider}")
async def oauth_login(
    provider: str,
    request: OAuthLoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    try:
        return await service.oauth_login(
            provider=provider,
            provider_id=request.provider_id,
            email=request.email,
            display_name=request.display_name,
            avatar_url=request.avatar_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/refresh")
async def refresh_token(
    http_request: Request,
    response: Response,
    request: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
):
    rate_limit_key = _build_auth_rate_limit_key(http_request, "refresh")
    rate_limit = await _consume_rate_limit_slot(
        rate_limit_key,
        REFRESH_RATE_LIMIT,
        REFRESH_RATE_LIMIT_WINDOW_SECONDS,
    )
    if rate_limit:
        allowed, remaining, reset_seconds = rate_limit
        _set_rate_limit_headers(response, REFRESH_RATE_LIMIT, remaining, reset_seconds)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many refresh attempts. Please try again later.",
                headers=_build_rate_limit_headers(REFRESH_RATE_LIMIT, remaining, reset_seconds),
            )

    try:
        return await service.refresh_access_token(request.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
