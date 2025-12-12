import braintree
from typing import Tuple
from .models import GatewayStatus


def map_braintree_result(
    result: braintree.Result, for_charge: bool
) -> Tuple[GatewayStatus, str, str]:
    tx = result.transaction if hasattr(result, "transaction") else None

    if result.is_success:
        if not tx:
            return "ERROR", "unknown_status", "Missing transaction object on success"
        s = tx.status
        if for_charge:
            if s in (
                braintree.Transaction.Status.SubmittedForSettlement,
                braintree.Transaction.Status.Settled,
            ):
                return "CHARGED", "charged", "Payment successful"
            if s == braintree.Transaction.Status.Authorized:
                return "APPROVED", "authorized", "Authorized, pending settlement"
        else:
            if s == braintree.Transaction.Status.Authorized:
                return "APPROVED", "approved", "Card authorized"
            if s in (
                braintree.Transaction.Status.SubmittedForSettlement,
                braintree.Transaction.Status.Settled,
            ):
                return "APPROVED", "approved", "Card authorized/settled"
        return "ERROR", "unknown_status", f"Unexpected Braintree status: {s}"

    if tx is not None:
        s = tx.status
        resp_text = tx.processor_response_text
        if s == braintree.Transaction.Status.ProcessorDeclined:
            return "DEAD", "declined", resp_text
        if s == braintree.Transaction.Status.GatewayRejected:
            reason = tx.gateway_rejection_reason
            return "DEAD", "gateway_rejected", f"Gateway rejected: {reason}"
        if s == braintree.Transaction.Status.Failed:
            return "ERROR", "gateway_error", resp_text
        if s == braintree.Transaction.Status.SettlementDeclined:
            return "DEAD", "settlement_declined", resp_text
        return "ERROR", "unknown_status", f"{s}: {resp_text}"

    if result.errors.deep_errors:
        msg = "; ".join(e.message for e in result.errors.deep_errors)
        return "ERROR", "invalid_request", msg

    return "ERROR", "braintree_error", "Unknown Braintree error"
