import stripe
from sqlalchemy.orm import Session
from app.schemas.fraud_detection import FraudDetectionRequest, FraudDetectionResponse, FraudInsight
from app.core.config import settings
import logging

logger = logging.getLogger("fraud_detection")

stripe.api_key = settings.STRIPE_SECRET_KEY

async def process_fraud_detection(request: FraudDetectionRequest, db: Session) -> FraudDetectionResponse:
    """
    Uses Stripe Radar to analyze transaction risk and generate fraud insights.
    """
    insights = []
    flagged = False
    recommendation = "Transaction appears normal. No further action required."

    try:
        # Retrieve Stripe charge or payment intent
        payment_intent = stripe.PaymentIntent.retrieve(request.transaction_id)
        charge = payment_intent.charges.data[0] if payment_intent.charges.data else None

        if charge and charge.outcome:
            risk_level = charge.outcome.get("risk_level", "unknown")
            risk_score = charge.outcome.get("risk_score", 0)
            reason = charge.outcome.get("reason", "Not specified")

            insights.append(FraudInsight(insight=f"Stripe Radar risk level: {risk_level}"))
            insights.append(FraudInsight(insight=f"Risk score: {risk_score}"))
            insights.append(FraudInsight(insight=f"Outcome reason: {reason}"))

            if risk_level in ["highest", "elevated"] or risk_score >= 75:
                flagged = True
                recommendation = "Transaction flagged by Stripe Radar. Manual review recommended."

        else:
            insights.append(FraudInsight(insight="Could not retrieve Radar outcome from Stripe."))

    except stripe.error.StripeError as e:
        logger.error(f"[Stripe Radar] Error: {e.user_message or str(e)}")
        insights.append(FraudInsight(insight="Stripe API error occurred. Could not retrieve risk data."))
        recommendation = "Manual review recommended due to API issue."
        flagged = True

    return FraudDetectionResponse(
        user_id=request.user_id,
        transaction_id=request.transaction_id,
        flagged=flagged,
        insights=insights,
        recommendation=recommendation
    )
