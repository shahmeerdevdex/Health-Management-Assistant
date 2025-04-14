from fastapi import APIRouter, Depends, HTTPException
from app.services.payment_service import create_stripe_checkout
from app.api.endpoints.dependencies import get_current_user

router = APIRouter()

@router.post("/checkout")
async def checkout(
    price_id: str,
    quantity: int = 1,  
    db_user=Depends(get_current_user)
):
    try:
        checkout_url = create_stripe_checkout(
            price_id=price_id,
            quantity=quantity,
            success_url="https://yourapp.com/success",
            cancel_url="https://yourapp.com/cancel"
        )
        return {"checkout_url": checkout_url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
