from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from app.schemas.pharmacy import PharmacyOrderRequest, PharmacyOrderResponse
from app.services.pharmacy_service import process_pharmacy_order, get_pharmacy_order, update_pharmacy_order, delete_pharmacy_order
from app.api.endpoints.dependencies import get_db,get_current_user
from app.db.models.pharmacy import PharmacyOrder
import stripe
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter()

@router.post("/orders", response_model=PharmacyOrderResponse)
async def pharmacy_order(
    request: PharmacyOrderRequest,
    db: Session = Depends(get_db),
    db_user = Depends(get_current_user)
):
    """
    Processes pharmacy orders and provides order confirmation.
    """
    try:
        order_data = await process_pharmacy_order(request, db)
        return order_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders/{order_id}", response_model=PharmacyOrderResponse)
async def get_order(order_id: int, db: Session = Depends(get_db), db_user = Depends(get_current_user)):
    """
    Retrieves a pharmacy order by order ID.
    """
    order = await get_pharmacy_order(order_id, db)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.put("/orders/{order_id}", response_model=PharmacyOrderResponse)
async def update_order(order_id: int, request: PharmacyOrderRequest, db: Session = Depends(get_db), db_user = Depends(get_current_user)):
    """
    Updates an existing pharmacy order.
    """
    updated_order = await update_pharmacy_order(order_id, request, db)
    if not updated_order:
        raise HTTPException(status_code=404, detail="Order not found or update failed")
    return updated_order

@router.delete("/orders/{order_id}")
async def delete_order(order_id: int, db: Session = Depends(get_db), db_user = Depends(get_current_user)):
    """
    Deletes a pharmacy order by order ID.
    """
    success = await delete_pharmacy_order(order_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Order not found or delete failed")
    return {"message": "Order deleted successfully"}


@router.post("/pharmacy/order/{order_id}/mark-paid")
async def mark_order_paid(order_id: int, db: Session = Depends(get_db)):
    order = await db.get(PharmacyOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not order.stripe_payment_intent_id:
        raise HTTPException(status_code=400, detail="No payment intent associated with this order")

    try:
        intent = stripe.PaymentIntent.retrieve(order.stripe_payment_intent_id)
        if intent.status != "succeeded":
            raise HTTPException(status_code=402, detail="Payment not confirmed by Stripe")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")

    order.status = "Paid"
    await db.commit()
    return {"status": "Stripe payment verified. Order marked as Paid."}
