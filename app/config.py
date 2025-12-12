import os
from dotenv import load_dotenv

load_dotenv()

LIVE_TEST_KEY = os.getenv("LIVE_TEST_KEY", "LIVE_TEST_KEY_ABC")

STRIPE_LIVE_SECRET_KEY = os.getenv("STRIPE_LIVE_SECRET_KEY", "")

BT_LIVE_MERCHANT_ID = os.getenv("BT_LIVE_MERCHANT_ID", "")
BT_LIVE_PUBLIC_KEY = os.getenv("BT_LIVE_PUBLIC_KEY", "")
BT_LIVE_PRIVATE_KEY = os.getenv("BT_LIVE_PRIVATE_KEY", "")

PAYPAL_CLIENT_ID_LIVE = os.getenv("PAYPAL_CLIENT_ID_LIVE", "")
PAYPAL_CLIENT_SECRET_LIVE = os.getenv("PAYPAL_CLIENT_SECRET_LIVE", "")
PAYPAL_BASE_LIVE = "https://api-m.paypal.com"


def _split_sites(value: str) -> list[str]:
    return [s.strip() for s in value.split(",") if s.strip()]


STRIPE_LIVE_SITES = _split_sites(
    os.getenv("STRIPE_LIVE_SITES", "stripe-live-test1.yourdomain.tld")
)
BRAINTREE_LIVE_SITES = _split_sites(
    os.getenv("BRAINTREE_LIVE_SITES", "b3-live-test1.yourdomain.tld")
)
PPCP_LIVE_SITES = _split_sites(
    os.getenv("PPCP_LIVE_SITES", "ppcp-live-test1.yourdomain.tld")
)
