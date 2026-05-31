"""
Billing API — premium purchase verification (MVP stub).
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from core.dependencies import get_current_user_id, get_db
from services.billing import BillingService

router = APIRouter()


class VerifyPurchaseRequest(BaseModel):
    platform: str = Field(pattern=r"^(ios|android)$")
    product_id: str = Field(min_length=1, max_length=200)
    purchase_token: str = Field(min_length=1, max_length=2000)


@router.post("/verify-purchase")
async def verify_purchase(
    body: VerifyPurchaseRequest,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Verify an app-store purchase and activate premium."""
    service = BillingService(db)
    result = await service.verify_purchase(
        user_id=user_id,
        platform=body.platform,
        product_id=body.product_id,
        purchase_token=body.purchase_token,
    )
    await db.commit()
    return result
