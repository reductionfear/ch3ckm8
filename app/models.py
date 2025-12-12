from typing import Optional, Literal
from pydantic import BaseModel


GatewayStatus = Literal[
    "CHARGED",
    "APPROVED",
    "CCN MATCHED",
    "LIVE",
    "DEAD",
    "ERROR",
]


class SiteInfo(BaseModel):
    site: str
    proxy_ip: str = "N/A"
    product_id: Optional[str] = None
    charged_amount: str = "N/A"
    currency: str = "N/A"
    stripe_pk: Optional[str] = None
    stripe_pm_id: Optional[str] = None
    checkout_nonce: Optional[str] = None


class GatewayResponse(BaseModel):
    status: GatewayStatus
    code: str
    message: str
    receipt_url: Optional[str] = None
    vbv_status: Optional[str] = None
    bin_info: Optional[dict] = None
    site_info: SiteInfo
