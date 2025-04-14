from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from app.schemas.pharmacy import PharmacyOrderRequest, PharmacyOrderResponse
from app.db.models.pharmacy import PharmacyOrder

import stripe
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

async def process_pharmacy_order(request: PharmacyOrderRequest, db: Session) -> PharmacyOrderResponse:
    """
    Creates a Stripe payment, stores the order, and returns confirmation.
    """

    try:
        # 1. Create Stripe PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=int(request.total_amount * 100),  # Stripe requires amount in cents
            currency="usd",  # Change as needed
            payment_method_types=["card"],
            metadata={
                "user_id": request.user_id,
                "medications": ", ".join(request.medications),
            }
        )

        # 2. Store the order with status "Pending Payment"
        estimated_delivery = datetime.utcnow() + timedelta(days=1)

        order = PharmacyOrder(
            user_id=request.user_id,
            medications=request.medications,
            delivery_address=request.delivery_address,
            payment_method=request.payment_method,
            insurance_used=request.insurance_used,
            status="Pending Payment",
            estimated_delivery=estimated_delivery,
            order_date=datetime.utcnow(),
            stripe_payment_intent_id=intent.id
        )

        db.add(order)
        await db.commit()
        await db.refresh(order)

        # 3. Return client_secret so frontend can complete the payment
        return PharmacyOrderResponse(
            order_id=order.id,
            user_id=request.user_id,
            medications=request.medications,
            status=order.status,
            estimated_delivery=str(order.estimated_delivery),
            stripe_client_secret=intent.client_secret
        )

    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error: {str(e)}")
    except SQLAlchemyError as e:
        await db.rollback()
        raise Exception(f"Database error: {str(e)}")


async def get_pharmacy_order(order_id: int, db: Session) -> PharmacyOrderResponse:
    """Retrieve a specific pharmacy order by order ID."""
    order = await db.get(PharmacyOrder, order_id)
    if not order:
        return None
    return PharmacyOrderResponse(
        order_id=order.id,
        user_id=order.user_id,
        medications=order.medications,
        status=order.status,
        estimated_delivery=str(order.estimated_delivery)
    )

async def update_pharmacy_order(order_id: int, request: PharmacyOrderRequest, db: Session) -> PharmacyOrderResponse:
    """Update an existing pharmacy order."""
    order = await db.get(PharmacyOrder, order_id)
    if not order:
        return None
    try:
        order.medications = request.medications
        order.delivery_address = request.delivery_address
        order.payment_method = request.payment_method
        order.insurance_used = request.insurance_used
        order.status = "Updated"
        await db.commit()
        await db.refresh(order)
    except SQLAlchemyError as e:
        await db.rollback()
        raise Exception(f"Database error: {str(e)}")
    return PharmacyOrderResponse(
        order_id=order.id,
        user_id=order.user_id,
        medications=order.medications,
        status=order.status,
        estimated_delivery=str(order.estimated_delivery)
    )

async def delete_pharmacy_order(order_id: int, db: Session) -> bool:
    """Delete a pharmacy order by order ID."""
    order = await db.get(PharmacyOrder, order_id)
    if not order:
        return False
    try:
        await db.delete(order)
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        raise Exception(f"Database error: {str(e)}")