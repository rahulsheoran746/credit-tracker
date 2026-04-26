from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime


class FutureOrderItemIn(BaseModel):
    product_id: int
    category: str         # 'cattle_feed' | 'wholesale' (sweet rejected by service)
    name: str
    unit: str
    quantity: float
    price: float          # locked at order creation
    amount: float         # price * quantity


class FutureOrderItemOut(FutureOrderItemIn):
    id: int


class FutureOrderCreate(BaseModel):
    member_id: int
    pickup_date: date
    items: List[FutureOrderItemIn]
    token_cash: float = 0
    token_upi:  float = 0
    notes: Optional[str] = None


class FutureOrderFulfill(BaseModel):
    """
    Pickup-day conversion to a Sale.
    `items` is the final list (worker may have edited qty / added / removed lines).
    `cash_amount` + `upi_amount` is the FRESH payment received today (excluding token).
    """
    items: List[FutureOrderItemIn]
    cash_amount: float = 0
    upi_amount:  float = 0


class FutureOrderCancel(BaseModel):
    reason: Optional[str] = None


class FutureOrderOut(BaseModel):
    id: int
    member_id: int
    member_name: str
    member_phone: str
    pickup_date: str
    status: str                              # 'pending' | 'fulfilled' | 'cancelled'
    token_cash: float
    token_upi:  float
    token_total: float                       # convenience: cash + upi
    notes: Optional[str] = None
    cancel_reason: Optional[str] = None
    refund_due: float = 0
    fulfilled_transaction_id: Optional[int] = None
    items: List[FutureOrderItemOut] = []
    items_total: float = 0                   # sum of item amounts (current order value)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
