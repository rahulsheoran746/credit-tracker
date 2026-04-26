from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class LoanCreate(BaseModel):
    member_id: int
    principal: float
    interest_rate_monthly: float       # e.g. 2.0 = 2% per month
    borrow_date: date
    cash_amount: float = 0             # cash + upi must equal principal
    upi_amount: float = 0
    notes: Optional[str] = None


class LoanRepayCreate(BaseModel):
    amount: float
    repay_date: date
    cash_amount: float = 0             # cash + upi must equal amount
    upi_amount: float = 0
    notes: Optional[str] = None


class RepaymentOut(BaseModel):
    id: int
    amount: float
    repay_date: str
    cash_amount: Optional[float] = None
    upi_amount:  Optional[float] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None


class LoanOut(BaseModel):
    id: int
    member_id: int
    member_name: str
    member_phone: str
    principal: float
    interest_rate_monthly: float
    borrow_date: str
    cash_amount: Optional[float] = None
    upi_amount:  Optional[float] = None
    notes: Optional[str] = None
    # Derived balance fields
    total_repaid: float
    current_principal: float
    accrued_interest: float
    total_owed: float                   # current_principal + accrued_interest
    is_closed: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class LoanDetailOut(LoanOut):
    repayments: List[RepaymentOut] = []
