from pydantic import BaseModel
from typing import Optional

class SweetOut(BaseModel):
    id: int
    name: str
    rate_per_kg: float
    description: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class SweetCreate(BaseModel):
    name: str
    rate_per_kg: float
    description: str = ''

class SweetUpdate(BaseModel):
    rate_per_kg: float
    description: str = ''
