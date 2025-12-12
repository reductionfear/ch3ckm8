from typing import Tuple
from .models import GatewayStatus
import requests


def map_ppcp_response(resp: requests.Response) -> Tuple[GatewayStatus, str, str]:
    if not resp.ok:
        try:
            err = resp.json()
            name = err.get("name", "")
            message = err.get("message", "") or f"HTTP {resp.status_code}"
            if name == "CREDIT_CARD_REFUSED":
                return "DEAD", "declined", message
            if name in ("INVALID_REQUEST", "UNPROCESSABLE_ENTITY"):
                return "ERROR", "invalid_request", message
            if name == "INTERNAL_SERVER_ERROR":
                return "ERROR", "gateway_error", message
            return "ERROR", "ppcp_error", message
        except Exception:
            return "ERROR", "gateway_error", f"HTTP {resp.status_code}"

    data = resp.json()
    status = data.get("status", "")

    if status == "COMPLETED":
        return "CHARGED", "charged", "Payment successful"
    if status == "APPROVED":
        return "APPROVED", "authorized", "Payment approved, pending capture"
    if status == "PAYER_ACTION_REQUIRED":
        return "LIVE", "payer_action", "Payer action required"

    return "ERROR", "unknown_status", f"Unexpected PPCP status: {status}"
