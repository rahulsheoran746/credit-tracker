"""
Audit trail via Python logging (not DB).

All mutation + auth events emit a structured log line on the 'audit' logger.

Grep tips:
    docker logs shiv-app | grep audit
    docker logs shiv-app | grep "login_failed"
    docker logs shiv-app | grep "user=rohit"
"""

import json
import logging

audit_logger = logging.getLogger("audit")


def log_action(conn, user, action, entity_type=None, entity_id=None, details=None, commit=True):
    """
    `conn` / `commit` are kept for backwards-compat with the previous DB-backed
    implementation. They are ignored — audit is now purely log-based.
    """
    user_id  = user.get("id")       if user else None
    username = user.get("username") if user else "anonymous"

    parts = [f"user={username}({user_id}) action={action}"]
    if entity_type:
        parts.append(f"entity={entity_type}")
    if entity_id is not None:
        parts.append(f"id={entity_id}")
    if details:
        try:
            parts.append("details=" + json.dumps(details, default=str, separators=(',', ':')))
        except Exception:
            parts.append(f"details={details!r}")

    summary = " ".join(parts)

    # Elevate security-relevant events to WARNING so they stand out during grepping
    if action == "login_failed":
        audit_logger.warning(summary)
    else:
        audit_logger.info(summary)
