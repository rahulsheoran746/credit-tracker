from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime


class SweetItem(BaseModel):
    item_id: int
    name: str
    quantity_kg: float
    rate_per_kg: float
    amount: float


class TransactionBlock(BaseModel):
    transaction_type: str  # e.g. "sweets", "cattle_feed", etc.
    items: List[SweetItem]
    total_amount: float
    amount_given: float
    notes: Optional[str] = None  # Optional for cattle_feed or other types


class MemberInfo(BaseModel):
    name: str
    phone: str
    father_name: Optional[str] = None
    village: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None

class MemberQuery(BaseModel):
    name: str
    phone: str

class TransactionPayload(BaseModel):
    member: MemberInfo
    transactions: List[TransactionBlock]
    transaction_date: datetime
    description: Optional[str] = None

class ItemDetail(BaseModel):
    item_id: int
    name: str
    quantity_kg: float
    amount: float
    rate_per_kg: float

class TransactionDetail(BaseModel):
    transaction_id: int
    transaction_date: str  # or datetime
    total_amount: float
    amount_paid: float
    remaining_amount: float
    items: List[ItemDetail]

class MemberTransactionsResponse(BaseModel):
    name: str
    phone: str
    father_name: Optional[str] = None
    total_amount: float
    amount_paid: float
    remaining_amount: float
    transactions: List[TransactionDetail]