# Checkmate Live API

Self-hosted FastAPI service providing **Live Test Mode** payment gateways for:

- Stripe (Auth + Charge)
- Braintree (B3) Charge
- PayPal Commerce Platform (PPCP) Charge

This API is designed to be used by the `reductionfear/ch3ckm8` client, which will call:

- `GET /stripe_live_test`
- `GET /stripe_charge_live_test`
- `GET /b3_live_test`
- `GET /ppcp_live_test`

Each endpoint performs a **live** (non-sandbox) transaction using your own payment credentials, with small amounts and optional auto-refund/void (you can enable this as needed).

> WARNING: These endpoints hit real Stripe/Braintree/PPCP environments. Use small amounts, your own merchant accounts, and cards you control.

---

## Quick start

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

- `LIVE_TEST_KEY` – API key that `ch3ckm8` will send as `?key=...`
- `STRIPE_LIVE_SECRET_KEY` – Stripe live (or live-test) secret key.
- `BT_LIVE_*` – Braintree live merchant credentials.
- `PAYPAL_CLIENT_ID_LIVE` / `PAYPAL_CLIENT_SECRET_LIVE` – PPCP live app credentials.

You can also adjust the live site pools via:

- `STRIPE_LIVE_SITES`
- `BRAINTREE_LIVE_SITES`
- `PPCP_LIVE_SITES`

These are used when `site=SIN-STRIPE-LIVE`, `SIN-B3-LIVE`, `SIN-PPCP-LIVE`.

### 3. Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### 4. Point `ch3ckm8` to this API

In `reductionfear/ch3ckm8`:

1. Set `api_base` to `http://localhost:8000` (or your deployed URL).
2. Set `api_key` to the same value as `LIVE_TEST_KEY` in `.env`.
3. Use the **Live Test** gateways:

   - `STRIPE AUTH (LIVE TEST)` → `/stripe_live_test`
   - `STRIPE CHARGE (LIVE TEST)` → `/stripe_charge_live_test`
   - `PPCP LIVE TEST` → `/ppcp_live_test`
   - `B3 LIVE TEST` → `/b3_live_test`

4. When prompted, type `LIVE` to confirm (as implemented in `checker.py`).

---

## Endpoints

### `GET /stripe_live_test`

Stripe auth-only live test:

- Query params:
  - `site` – either a domain or `SIN-STRIPE-LIVE`.
  - `cards` – `CC|MM|YY|CVV`.
  - `key` – must match `LIVE_TEST_KEY`.
  - `proxy` – optional, ignored for now.
- Behavior:
  - Creates a PaymentIntent with `capture_method="manual"` and small fixed amount (1.00 USD).
  - Maps the PaymentIntent status to `APPROVED`, `DEAD`, `LIVE`, or `ERROR`.

### `GET /stripe_charge_live_test`

Stripe charge live test:

- Same params as `/stripe_live_test`.
- Behavior:
  - Creates a PaymentIntent with `capture_method="automatic"`.
  - Maps `succeeded` to `CHARGED`, others accordingly.
  - Optional place to add auto-refund of successful charges.

### `GET /b3_live_test`

Braintree live test:

- Same params.
- Behavior:
  - Calls `transaction.sale` with amount `1.00` and `submit_for_settlement=True`.
  - Maps Braintree result to `CHARGED`, `APPROVED`, `DEAD`, or `ERROR`.

### `GET /ppcp_live_test`

PPCP (PayPal Commerce Platform) live test:

- Same params.
- Behavior:
  - Fetches OAuth token from `https://api-m.paypal.com/v1/oauth2/token`.
  - Creates an order via `/v2/checkout/orders` with `intent="CAPTURE"` and card funding source.
  - Maps PPCP status to `CHARGED`, `APPROVED`, `LIVE`, or `ERROR`.

---

## Response shape

All gateways return the same JSON shape, e.g.:

```json
{
  "status": "CHARGED",
  "code": "charged",
  "message": "Payment successful",
  "receipt_url": null,
  "vbv_status": null,
  "bin_info": null,
  "site_info": {
    "site": "stripe-live-test1.yourdomain.tld",
    "proxy_ip": "N/A",
    "product_id": null,
    "charged_amount": "1.00 USD",
    "currency": "USD",
    "stripe_pk": null,
    "stripe_pm_id": null,
    "checkout_nonce": null
  }
}
```

The `ch3ckm8` client only requires:

- `status`
- `code`
- `message`
- `site_info.proxy_ip` (will display `N/A` if not used).

---

## Safety recommendations

- Use **small test amounts** (1.00 or equivalent).
- Only call this API against:
  - Your own Stripe/Braintree/PPCP accounts.
  - Cards/accounts you are allowed to use for testing.
- Optionally implement **auto-refund/void** inside the handlers once you’re comfortable with the flows.
- Protect the API:
  - Keep `LIVE_TEST_KEY` secret.
  - Restrict access by IP / VPN / firewall if possible.
