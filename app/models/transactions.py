from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class TransactionCreate(BaseModel):
    member_id: int
    transaction_type: Literal['sweet', 'cattle_feed', 'bulk', 'borrow', 'repay']
    sweet_id: Optional[int] = None
    quantity: Optional[float] = None  # can be 1.5, 2, 5 etc.
    amount: float  # always required
    interest_percent: Optional[float] = None  # only if borrow
    description: Optional[str] = None

class TransactionResponse(BaseModel):
    id: int
    member_id: int
    transaction_type: str
    sweet_id: Optional[int]
    quantity: Optional[float]
    amount: float
    interest_percent: Optional[float]
    description: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
