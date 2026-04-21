import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from dotenv import load_dotenv
from jose import JWTError, jwt

# Load the .env file even if it hasn't been loaded by another module yet.
# load_dotenv is idempotent and a no-op when env is already populated.
load_dotenv()

# JWT config — read from env so we don't commit secrets
JWT_SECRET    = os.getenv("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION")
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_DAYS = int(os.getenv("JWT_EXPIRES_DAYS", "30"))

# bcrypt has a 72-byte input cap; truncating on input avoids a ValueError
# for unusually long passwords without silently ignoring trailing chars.
_MAX_PW_BYTES = 72


def _encode_pw(plain: str) -> bytes:
    return plain.encode("utf-8")[:_MAX_PW_BYTES]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_encode_pw(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_encode_pw(plain), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: int, username: str, role: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRES_DAYS)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": expires_at,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None
