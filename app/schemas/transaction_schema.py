from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class LineItem(BaseModel):
    product_id: int
    category: str            # 'sweet' | 'cattle_feed'
    name: str
    unit: str                # 'kg' | 'bag'
    quantity: float
    price: float             # price per unit
    amount: float


class TransactionBlock(BaseModel):
    items: List[LineItem]
    total_amount: float
    amount_given: float
    notes: Optional[str] = None


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
    # Supports both the new schema and legacy sweet rows (quantity_kg/rate_per_kg)
    product_id: Optional[int] = None
    item_id: Optional[int] = None
    category: Optional[str] = None
    name: str
    unit: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    amount: float
    quantity_kg: Optional[float] = None
    rate_per_kg: Optional[float] = None


class TransactionDetail(BaseModel):
    transaction_id: int
    transaction_date: str
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
