import stripe
from typing import Tuple
from .models import GatewayStatus


def map_stripe_intent_to_status(
    intent: stripe.PaymentIntent, for_charge: bool
) -> Tuple[GatewayStatus, str, str]:
    s = intent.status
    if not for_charge:
        if s in ("requires_capture", "succeeded"):
            return "APPROVED", "approved", "Card authorized"
        if s == "requires_payment_method":
            return "DEAD", "declined", "Payment failed, new card required"
        if s == "requires_action":
            return "LIVE", "3ds_required", "3D Secure authentication required"
        if s == "processing":
            return "ERROR", "processing", "Payment is still processing"
        if s == "canceled":
            return "DEAD", "canceled", "Payment was canceled"
        return "ERROR", "unknown_status", f"Unexpected Stripe status: {s}"
    else:
        if s == "succeeded":
            return "CHARGED", "charged", "Payment successful"
        if s == "requires_capture":
            return "APPROVED", "authorized", "Authorized, pending capture"
        if s == "requires_payment_method":
            return "DEAD", "declined", "Payment failed, new card required"
        if s == "requires_action":
            return "LIVE", "3ds_required", "3D Secure authentication required"
        if s == "processing":
            return "ERROR", "processing", "Payment is still processing"
        if s == "canceled":
            return "DEAD", "canceled", "Payment was canceled"
        return "ERROR", "unknown_status", f"Unexpected Stripe status: {s}"


def map_stripe_error_to_status(e: Exception) -> Tuple[GatewayStatus, str, str]:
    if isinstance(e, stripe.error.CardError):
        code = e.code or "declined"
        user_msg = e.user_message or "Card declined"
        ccn_codes = {"insufficient_funds", "incorrect_cvc", "do_not_honor"}
        dead_codes = {
            "invalid_number",
            "incorrect_number",
            "invalid_expiry_month",
            "invalid_expiry_year",
            "expired_card",
        }
        if code in ccn_codes:
            return "CCN MATCHED", code, user_msg
        elif code in dead_codes:
            return "DEAD", code, user_msg
        else:
            return "DEAD", "declined", user_msg

    if isinstance(e, stripe.error.RateLimitError):
        return "ERROR", "rate_limited", "Gateway rate limited"
    if isinstance(e, stripe.error.InvalidRequestError):
        return "ERROR", "invalid_request", "Invalid request to gateway"
    if isinstance(e, stripe.error.AuthenticationError):
        return "ERROR", "gateway_auth_failed", "Gateway authentication failed"
    if isinstance(e, stripe.error.APIConnectionError):
        return "ERROR", "gateway_connection_error", "Gateway connection error"
    if isinstance(e, stripe.error.StripeError):
        return "ERROR", "stripe_error", str(e)

    return "ERROR", "exception", str(e)
