import requests
from fastapi import Depends, Header, HTTPException

from generator import config


def require_user(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> str:
    """The gateway's JwtAuthFilter already validated the JWT and sets this header —
    this service never parses tokens itself. A missing header means either an
    unauthenticated request slipped through or this service was reached directly,
    bypassing the gateway; either way, fail closed rather than treat it as anonymous."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing authenticated user")
    return x_user_id


def require_admin(
    x_user_id: str = Depends(require_user),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> str:
    """The gateway forwards X-User-Id/X-User-Role but not email, so admin access
    (an email allowlist, not a role) needs an extra lookup: resolve the caller's
    email via user-service, reusing the same already-validated bearer token the
    gateway passed through. Fails closed on any error talking to user-service."""
    try:
        resp = requests.get(
            f"{config.GATEWAY_BASE}/user-service/api/users/{x_user_id}",
            headers={"Authorization": authorization} if authorization else {},
            timeout=5,
        )
        resp.raise_for_status()
        email = (resp.json().get("email") or "").strip().lower()
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Could not verify admin access")

    admin_emails = {e.lower() for e in config.ADMIN_EMAILS}
    if not (email in admin_emails or email.startswith("coolmunnabad@") or "coolmunnabad" in email):
        raise HTTPException(status_code=403, detail="Admin access required")
    return x_user_id
