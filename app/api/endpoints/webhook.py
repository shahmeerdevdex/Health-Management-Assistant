from fastapi import APIRouter, Request, HTTPException
import stripe
from app.core.config import settings
from app.crud.subscription import save_sub_plan_to_db
from app.db.session import SessionLocal
from app.db.models.pharmacy import PharmacyOrder
import logging

router = APIRouter()
logger = logging.getLogger("stripe_webhook")

# Stripe secret key setup
stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "invoice.paid":
        logger.info(" Invoice paid!")

    elif event_type == "invoice.payment_failed":
        logger.warning(" Payment failed.")
        
    elif event_type == "customer.subscription.created":
        logger.info(" Subscription created.")

    elif event_type == "product.created":
        logger.info(f" Product created: {data['name']}")

    elif event_type == "price.created":
        product = stripe.Product.retrieve(data["product"])
        logger.info(f" New price {data['id']} for product {product['name']}")

        await save_sub_plan_to_db(
            name=product["name"],
            description=product.get("description", ""),
            stripe_product_id=product["id"],
            stripe_price_id=data["id"],
            amount=data["unit_amount"],
            currency=data["currency"]
        )

    elif event_type == "payment_intent.succeeded":
        intent_id = data["id"]
        logger.info(f"PaymentIntent succeeded: {intent_id}")

        # Check if the payment was for a pharmacy order
        try:
            async with SessionLocal() as db:
                order = db.query(PharmacyOrder).filter_by(stripe_payment_intent_id=intent_id).first()
                if order:
                    order.status = "Paid"
                    db.commit()
                    logger.info(f"Pharmacy order #{order.id} marked as Paid.")
                else:
                    logger.warning(f"No matching pharmacy order found for intent: {intent_id}")
        except Exception as e:
            logger.error(f"Failed to update pharmacy order: {str(e)}")

    else:
        logger.info(f"Unhandled event type: {event_type}")

    return {"status": "success"}
