from pydantic import BaseModel
from typing import Optional

VALID_CATEGORIES = {'sweet', 'cattle_feed', 'wholesale'}


class ProductCreate(BaseModel):
    category: str
    name: str
    unit: str
    price: float
    unit_size: Optional[float] = None
    description: Optional[str] = ''


class ProductUpdate(BaseModel):
    price: float
    unit_size: Optional[float] = None
    description: Optional[str] = ''


class ProductOut(BaseModel):
    id: int
    category: str
    name: str
    unit: str
    unit_size: Optional[float] = None
    price: float
    description: Optional[str] = ''
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
