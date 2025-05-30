from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
import stripe
from app.core.config import settings
from app.crud.subscription import (
    save_sub_plan_to_db,
    update_subscription_status,
    get_user_subscription
)
from app.db.session import SessionLocal
from app.db.models.pharmacy import PharmacyOrder
from app.services.notification_service import send_notification
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger("stripe_webhook")

# Stripe secret key setup
stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

@router.post("/webhook")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    event_type = event["type"]
    data = event["data"]["object"]

    try:
        async with SessionLocal() as db:
            if event_type == "invoice.paid":
                # Handle successful payment
                subscription_id = data.get("subscription")
                if subscription_id:
                    await update_subscription_status(db, subscription_id, "active")
                    # Send payment confirmation notification
                    subscription = await get_user_subscription(db, subscription_id)
                    if subscription:
                        await send_notification(
                            user_id=subscription.user_id,
                            title="Payment Successful",
                            message="Your subscription payment was processed successfully.",
                            notification_type="payment_success"
                        )

            elif event_type == "invoice.payment_failed":
                # Handle failed payment
                subscription_id = data.get("subscription")
                if subscription_id:
                    await update_subscription_status(db, subscription_id, "past_due")
                    # Send payment failure notification
                    subscription = await get_user_subscription(db, subscription_id)
                    if subscription:
                        await send_notification(
                            user_id=subscription.user_id,
                            title="Payment Failed",
                            message="Your subscription payment failed. Please update your payment method.",
                            notification_type="payment_failed"
                        )

            elif event_type == "customer.subscription.created":
                # Handle new subscription
                await update_subscription_status(db, data["id"], data["status"])
                logger.info(f"New subscription created: {data['id']}")

            elif event_type == "customer.subscription.updated":
                # Handle subscription update
                await update_subscription_status(db, data["id"], data["status"])
                logger.info(f"Subscription updated: {data['id']}")

            elif event_type == "customer.subscription.deleted":
                # Handle subscription cancellation
                await update_subscription_status(db, data["id"], "canceled")
                logger.info(f"Subscription canceled: {data['id']}")

            elif event_type == "customer.subscription.trial_will_end":
                # Handle trial ending soon
                subscription_id = data["id"]
                subscription = await get_user_subscription(db, subscription_id)
                if subscription:
                    await send_notification(
                        user_id=subscription.user_id,
                        title="Trial Ending Soon",
                        message="Your trial period will end in 3 days. Add a payment method to continue your subscription.",
                        notification_type="trial_ending"
                    )

            elif event_type == "product.created":
                logger.info(f"Product created: {data['name']}")

            elif event_type == "price.created":
                product = stripe.Product.retrieve(data["product"])
                logger.info(f"New price {data['id']} for product {product['name']}")

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
                order = await db.query(PharmacyOrder).filter_by(stripe_payment_intent_id=intent_id).first()
                if order:
                    order.status = "Paid"
                    await db.commit()
                    logger.info(f"Pharmacy order #{order.id} marked as Paid.")
                else:
                    logger.warning(f"No matching pharmacy order found for intent: {intent_id}")

            else:
                logger.info(f"Unhandled event type: {event_type}")

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success"}
