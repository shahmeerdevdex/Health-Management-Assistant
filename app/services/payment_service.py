from app.core.config import settings
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

# Stripe Checkout Session Generator (called by FastAPI endpoint)
from app.core.config import settings
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_stripe_checkout(
    *,
    price_id: str,
    quantity: int,
    success_url: str,
    cancel_url: str
) -> str:
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price": price_id,
            "quantity": quantity,
        }],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url
