from pydantic import BaseModel
from typing import Optional

class Member(BaseModel):
    name: str
    phone: Optional[str] = None