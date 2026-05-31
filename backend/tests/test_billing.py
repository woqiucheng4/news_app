from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.billing import BillingService


class FakeUserRepo:
    async def update(self, user_id: str, data: dict):
        return SimpleNamespace(
            id=user_id,
            is_premium=data.get("is_premium", False),
            premium_expires_at=data.get("premium_expires_at"),
        )


@pytest.mark.asyncio
async def test_verify_purchase_grants_premium_in_debug(monkeypatch):
    service = BillingService(session=SimpleNamespace())
    service.user_repo = FakeUserRepo()
    service.settings = SimpleNamespace(
        debug=True,
        freemium=SimpleNamespace(
            premium_product_id="newsflow_premium_monthly",
            allow_dev_purchase_verify=False,
        ),
    )

    async def fake_delete(_key):
        return True

    monkeypatch.setattr("core.cache.cache_manager.delete", fake_delete)

    result = await service.verify_purchase(
        user_id="user-1",
        platform="ios",
        product_id="newsflow_premium_monthly",
        purchase_token="dev-token",
    )
    assert result["success"] is True
    assert result["is_premium"] is True


@pytest.mark.asyncio
async def test_verify_purchase_rejects_unknown_product():
    service = BillingService(session=SimpleNamespace())
    service.user_repo = FakeUserRepo()
    service.settings = SimpleNamespace(
        debug=True,
        freemium=SimpleNamespace(
            premium_product_id="newsflow_premium_monthly",
            allow_dev_purchase_verify=False,
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await service.verify_purchase(
            user_id="user-1",
            platform="android",
            product_id="wrong_product",
            purchase_token="token",
        )

    assert exc.value.detail["code"] == "INVALID_PRODUCT"
