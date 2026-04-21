import logging
from app.auth.security import hash_password, verify_password
from app.schemas.user_schema import ROLES

logger = logging.getLogger(__name__)


def _row_to_user(row, include_hash=False) -> dict:
    # row order: id, username, password_hash, name, phone, role, is_active, must_change_password, created_at, updated_at
    out = {
        "id": row[0],
        "username": row[1],
        "name": row[3],
        "phone": row[4],
        "role": row[5],
        "is_active": row[6],
        "must_change_password": row[7],
        "created_at": row[8].isoformat() if row[8] else None,
        "updated_at": row[9].isoformat() if row[9] else None,
    }
    if include_hash:
        out["password_hash"] = row[2]
    return out


_SELECT = "id, username, password_hash, name, phone, role, is_active, must_change_password, created_at, updated_at"


class UserService:
    def __init__(self, conn):
        self.conn = conn

    def get_by_username(self, username: str, include_hash=False):
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT {_SELECT} FROM users WHERE username = %s", (username,))
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
        if not username.strip():
            raise ValueError("Username is required")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")

        with self.conn.cursor() as cur:
            # Check unique username
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                raise ValueError("Username is already taken")

            cur.execute(
                """
                INSERT INTO users (username, password_hash, name, phone, role, must_change_password)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                RETURNING id
                """,
                (username.strip(), hash_password(password), name.strip(), phone, role),
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
        if len(new_password) < 6:
            raise ValueError("Password must be at least 6 characters")
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users SET password_hash = %s, must_change_password = %s, updated_at = CURRENT_TIMESTAMP
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
        user = self.get_by_id(user_id)
        if not user:
            return False
        # Pull the hash
        with self.conn.cursor() as cur:
            cur.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
        if not row or not verify_password(current_password, row[0]):
            raise ValueError("Current password is incorrect")
        if len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters")
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users SET password_hash = %s, must_change_password = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (hash_password(new_password), user_id),
            )
        self.conn.commit()
        return True


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
