import logging
import re
from app.auth.security import hash_password, verify_password
from app.schemas.user_schema import ROLES

logger = logging.getLogger(__name__)


_PASS_UPPER   = re.compile(r"[A-Z]")
_PASS_DIGIT   = re.compile(r"\d")
_PASS_SPECIAL = re.compile(r"[^A-Za-z0-9\s]")


def _validate_password(p: str) -> None:
    """
    Enforce password strength rules. Lists ALL failing rules at once so the
    user fixes everything in one go instead of one rule per submit.
    """
    if not p:
        raise ValueError("Password is required")
    problems = []
    if len(p) < 8:
        problems.append("at least 8 characters")
    if not _PASS_UPPER.search(p):
        problems.append("at least one capital letter")
    if not _PASS_DIGIT.search(p):
        problems.append("at least one digit")
    if not _PASS_SPECIAL.search(p):
        problems.append("at least one special character (e.g. ! @ # $)")
    if problems:
        raise ValueError("Password must contain " + ", ".join(problems) + ".")


def _row_to_user(row, include_hash=False) -> dict:
    # row order: id, username, password_hash, name, phone, role, is_active,
    #            must_change_password, token_version, created_at, updated_at
    out = {
        "id": row[0],
        "username": row[1],
        "name": row[3],
        "phone": row[4],
        "role": row[5],
        "is_active": row[6],
        "must_change_password": row[7],
        "token_version": row[8],
        "created_at": row[9].isoformat() if row[9] else None,
        "updated_at": row[10].isoformat() if row[10] else None,
    }
    if include_hash:
        out["password_hash"] = row[2]
    return out


_SELECT = (
    "id, username, password_hash, name, phone, role, is_active, "
    "must_change_password, token_version, created_at, updated_at"
)


class UserService:
    def __init__(self, conn):
        self.conn = conn

    def get_by_username(self, username: str, include_hash=False):
        # Username is case-insensitive — normalise the input. Stored values are
        # already lowercase (enforced in create()), but LOWER() in the query
        # protects us if any legacy mixed-case rows exist.
        with self.conn.cursor() as cur:
            cur.execute(
                f"SELECT {_SELECT} FROM users WHERE username = LOWER(%s)",
                (username.strip(),),
            )
            row = cur.fetchone()
        return _row_to_user(row, include_hash=include_hash) if row else None

    def get_by_id(self, user_id: int):
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT {_SELECT} FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
        return _row_to_user(row) if row else None

    def list_users(self, include_inactive=False):
        with self.conn.cursor() as cur:
            if include_inactive:
                cur.execute(f"SELECT {_SELECT} FROM users ORDER BY created_at DESC")
            else:
                cur.execute(f"SELECT {_SELECT} FROM users WHERE is_active = TRUE ORDER BY created_at DESC")
            return [_row_to_user(r) for r in cur.fetchall()]

    def authenticate(self, username: str, password: str):
        user = self.get_by_username(username, include_hash=True)
        if not user or not user["is_active"]:
            return None
        if not verify_password(password, user["password_hash"]):
            return None
        user.pop("password_hash", None)
        return user

    def create(self, username, name, phone, role, password):
        if role not in ROLES:
            raise ValueError(f"Invalid role. Allowed: {sorted(ROLES)}")
        # Usernames are case-insensitive — store lowercased.
        username = (username or "").strip().lower()
        if not username:
            raise ValueError("Username is required")
        _validate_password(password)

        with self.conn.cursor() as cur:
            # Uniqueness check is also case-insensitive
            cur.execute("SELECT id FROM users WHERE username = LOWER(%s)", (username,))
            if cur.fetchone():
                raise ValueError("Username is already taken")

            cur.execute(
                """
                INSERT INTO users (username, password_hash, name, phone, role, must_change_password)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                RETURNING id
                """,
                (username, hash_password(password), name.strip(), phone, role),
            )
            new_id = cur.fetchone()[0]
        self.conn.commit()
        return self.get_by_id(new_id)

    def update(self, user_id, name=None, phone=None, role=None, is_active=None):
        if role is not None and role not in ROLES:
            raise ValueError(f"Invalid role. Allowed: {sorted(ROLES)}")

        updates, params = [], []
        if name is not None:     updates.append("name = %s");      params.append(name.strip())
        if phone is not None:    updates.append("phone = %s");     params.append(phone)
        if role is not None:     updates.append("role = %s");      params.append(role)
        if is_active is not None:updates.append("is_active = %s"); params.append(is_active)

        if not updates:
            return self.get_by_id(user_id)

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(user_id)
        with self.conn.cursor() as cur:
            cur.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = %s RETURNING id", params)
            row = cur.fetchone()
        if not row:
            return None
        self.conn.commit()
        return self.get_by_id(user_id)

    def reset_password(self, user_id, new_password, set_must_change=True):
        """
        Admin-initiated password reset. Bumps token_version so all of the
        target user's existing sessions (incl. the device they're on) are kicked
        out — they must log in fresh with the new temp password.
        """
        _validate_password(new_password)
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET password_hash = %s,
                    must_change_password = %s,
                    token_version = token_version + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s RETURNING id
                """,
                (hash_password(new_password), set_must_change, user_id),
            )
            row = cur.fetchone()
        if not row:
            return False
        self.conn.commit()
        return True

    def change_own_password(self, user_id, current_password, new_password):
        """
        User self-changes their password. Bumps token_version so OTHER devices
        get logged out. Returns the new token_version so the caller can mint a
        fresh JWT for the current device (keeping it logged in).
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        with self.conn.cursor() as cur:
            cur.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
        if not row or not verify_password(current_password, row[0]):
            raise ValueError("Current password is incorrect")
        _validate_password(new_password)
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET password_hash = %s,
                    must_change_password = FALSE,
                    token_version = token_version + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING token_version
                """,
                (hash_password(new_password), user_id),
            )
            new_tv = cur.fetchone()[0]
        self.conn.commit()
        return new_tv


def bootstrap_admin_if_empty(conn):
    """
    Called at app startup. If no users exist, create an admin from env vars:
      ADMIN_USERNAME (default 'admin')
      ADMIN_PASSWORD (default 'changeme123' — YOU MUST CHANGE THIS on first login)
      ADMIN_NAME     (default 'Admin')
    """
    import os
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
    if count > 0:
        return

    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "changeme123")
    name     = os.getenv("ADMIN_NAME", "Admin")

    UserService(conn).create(
        username=username, name=name, phone=None, role="admin", password=password,
    )
    logger.warning(
        "Bootstrapped admin user '%s'. CHANGE THE PASSWORD IMMEDIATELY after first login.",
        username,
    )
