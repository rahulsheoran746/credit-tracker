from pydantic import BaseModel
from typing import Optional

class MemberCreate(BaseModel):
    name: str
    phone: str
    village: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None

class MemberOut(BaseModel):
    id: int
    name: str
    phone: str
    village: Optional[str]
    city: Optional[str]
    state: Optional[str]
