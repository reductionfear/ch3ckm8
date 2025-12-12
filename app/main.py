import stripe
import braintree
import requests

from typing import Optional
from fastapi import FastAPI, Query, HTTPException

from .config import (
    LIVE_TEST_KEY,
    STRIPE_LIVE_SECRET_KEY,
    BT_LIVE_MERCHANT_ID,
    BT_LIVE_PUBLIC_KEY,
    BT_LIVE_PRIVATE_KEY,
    PAYPAL_CLIENT_ID_LIVE,
    PAYPAL_CLIENT_SECRET_LIVE,
    PAYPAL_BASE_LIVE,
    STRIPE_LIVE_SITES,
    BRAINTREE_LIVE_SITES,
    PPCP_LIVE_SITES,
)
from .models import GatewayResponse, SiteInfo
from .utils_common import validate_api_key, parse_card, pick_site
from .utils_stripe import map_stripe_intent_to_status, map_stripe_error_to_status
from .utils_braintree import map_braintree_result
from .utils_ppcp import map_ppcp_response

app = FastAPI(title="Checkmate Live API")

# Configure Stripe live
stripe.api_key = STRIPE_LIVE_SECRET_KEY

# Configure Braintree live
bt_live_gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        environment=braintree.Environment.Production,
        merchant_id=BT_LIVE_MERCHANT_ID,
        public_key=BT_LIVE_PUBLIC_KEY,
        private_key=BT_LIVE_PRIVATE_KEY,
    )
)


def get_paypal_live_token() -> str:
    resp = requests.post(
        f"{PAYPAL_BASE_LIVE}/v1/oauth2/token",
        auth=(PAYPAL_CLIENT_ID_LIVE, PAYPAL_CLIENT_SECRET_LIVE),
        data={"grant_type": "client_credentials"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def validate_live_key(key: str):
    validate_api_key(key, [LIVE_TEST_KEY])


@app.get("/health")
def health():
    return {
        "status": "online",
        "gateways": [
            "stripe_live_test",
            "stripe_charge_live_test",
            "b3_live_test",
            "ppcp_live_test",
        ],
    }


@app.get("/stripe_live_test", response_model=GatewayResponse)
def stripe_live_test(
    site: str = Query(...),
    cards: str = Query(...),
    key: str = Query(...),
    proxy: Optional[str] = Query(default=None),
):
    validate_live_key(key)
    real_site = pick_site(site, "SIN-STRIPE-LIVE", STRIPE_LIVE_SITES)

    try:
        cc, mm, yy, cvv = parse_card(cards)
    except HTTPException as e:
        return GatewayResponse(
            status="ERROR",
            code="invalid_format",
            message=str(e.detail),
            site_info=SiteInfo(site=real_site),
        )

    try:
        intent = stripe.PaymentIntent.create(
            amount=100,  # 1.00 USD
            currency="usd",
            payment_method_data={
                "type": "card",
                "card": {
                    "number": cc,
                    "exp_month": int(mm),
                    "exp_year": int(yy),
                    "cvc": cvv,
                },
            },
            confirm=True,
            capture_method="manual",
        )
        status, code, message = map_stripe_intent_to_status(intent, for_charge=False)
    except Exception as e:
        status, code, message = map_stripe_error_to_status(e)

    return GatewayResponse(
        status=status,
        code=code,
        message=message,
        site_info=SiteInfo(
            site=real_site,
            charged_amount="N/A",
            currency="USD",
        ),
    )


@app.get("/stripe_charge_live_test", response_model=GatewayResponse)
def stripe_charge_live_test(
    site: str = Query(...),
    cards: str = Query(...),
    key: str = Query(...),
    proxy: Optional[str] = Query(default=None),
):
    validate_live_key(key)
    real_site = pick_site(site, "SIN-STRIPE-LIVE", STRIPE_LIVE_SITES)

    try:
        cc, mm, yy, cvv = parse_card(cards)
    except HTTPException as e:
        return GatewayResponse(
            status="ERROR",
            code="invalid_format",
            message=str(e.detail),
            site_info=SiteInfo(site=real_site),
        )

    intent = None
    try:
        intent = stripe.PaymentIntent.create(
            amount=100,  # 1.00 USD
            currency="usd",
            payment_method_data={
                "type": "card",
                "card": {
                    "number": cc,
                    "exp_month": int(mm),
                    "exp_year": int(yy),
                    "cvc": cvv,
                },
            },
            confirm=True,
            capture_method="automatic",
        )
        status, code, message = map_stripe_intent_to_status(intent, for_charge=True)

        # Optional TODO: auto-refund successful charges if desired
        # if status == "CHARGED":
        #     stripe.Refund.create(payment_intent=intent.id)
        #     message += " (auto-refund initiated)"
    except Exception as e:
        status, code, message = map_stripe_error_to_status(e)

    charged_amount = "N/A"
    currency = "USD"
    if status == "CHARGED" and intent is not None:
        charged_amount = f"{intent.amount/100:.2f} {intent.currency.upper()}"
        currency = intent.currency.upper()

    return GatewayResponse(
        status=status,
        code=code,
        message=message,
        site_info=SiteInfo(
            site=real_site,
            charged_amount=charged_amount,
            currency=currency,
        ),
    )


@app.get("/b3_live_test", response_model=GatewayResponse)
def b3_live_test(
    site: str = Query(...),
    cards: str = Query(...),
    key: str = Query(...),
    proxy: Optional[str] = Query(default=None),
):
    validate_live_key(key)
    real_site = pick_site(site, "SIN-B3-LIVE", BRAINTREE_LIVE_SITES)

    try:
        cc, mm, yy, cvv = parse_card(cards)
    except HTTPException as e:
        return GatewayResponse(
            status="ERROR",
            code="invalid_format",
            message=str(e.detail),
            site_info=SiteInfo(site=real_site),
        )

    try:
        result = bt_live_gateway.transaction.sale(
            {
                "amount": "1.00",
                "credit_card": {
                    "number": cc,
                    "expiration_month": mm,
                    "expiration_year": yy,
                    "cvv": cvv,
                },
                "options": {
                    "submit_for_settlement": True,
                },
            }
        )
        status, code, message = map_braintree_result(result, for_charge=True)

        # Optional TODO: auto-void/refund if desired, using result.transaction.id
    except Exception as e:
        status, code, message = "ERROR", "exception", str(e)

    charged_amount = "1.00 USD" if status == "CHARGED" else "N/A"

    return GatewayResponse(
        status=status,
        code=code,
        message=message,
        site_info=SiteInfo(
            site=real_site,
            charged_amount=charged_amount,
            currency="USD",
        ),
    )


@app.get("/ppcp_live_test", response_model=GatewayResponse)
def ppcp_live_test(
    site: str = Query(...),
    cards: str = Query(...),
    key: str = Query(...),
    proxy: Optional[str] = Query(default=None),
):
    validate_live_key(key)
    real_site = pick_site(site, "SIN-PPCP-LIVE", PPCP_LIVE_SITES)

    try:
        cc, mm, yy, cvv = parse_card(cards)
    except HTTPException as e:
        return GatewayResponse(
            status="ERROR",
            code="invalid_format",
            message=str(e.detail),
            site_info=SiteInfo(site=real_site),
        )

    try:
        token = get_paypal_live_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        body = {
            "intent": "CAPTURE",
            "purchase_units": [
                {"amount": {"value": "1.00", "currency_code": "USD"}}
            ],
            "payment_source": {
                "card": {
                    "number": cc,
                    "expiry": f"{yy}-{mm}",
                    "security_code": cvv,
                }
            },
        }
        resp = requests.post(
            f"{PAYPAL_BASE_LIVE}/v2/checkout/orders",
            json=body,
            headers=headers,
            timeout=30,
        )
        status, code, message = map_ppcp_response(resp)

        # Optional TODO: auto-refund based on capture id in resp.json()
    except Exception as e:
        status, code, message = "ERROR", "exception", str(e)

    charged_amount = "1.00 USD" if status == "CHARGED" else "N/A"

    return GatewayResponse(
        status=status,
        code=code,
        message=message,
        site_info=SiteInfo(
            site=real_site,
            charged_amount=charged_amount,
            currency="USD",
        ),
    )
