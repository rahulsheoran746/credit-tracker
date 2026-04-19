from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas.loan_schema import LoanCreate, LoanRepayCreate
from app.services.loan_service import LoanService
from app.db import get_connection

router = APIRouter()


@router.get("/loans")
def list_loans(
    include_closed: bool = Query(False, description="Include fully repaid loans"),
    member_id: int | None = Query(None, description="Filter by member id"),
    conn=Depends(get_connection),
):
    svc = LoanService(conn)
    if member_id is not None:
        return svc.get_loans_for_member(member_id, include_closed=include_closed)
    return svc.list_loans(include_closed=include_closed)


@router.get("/loans/balance-by-member")
def balance_by_member(conn=Depends(get_connection)):
    """Mapping of member_id -> total outstanding loan balance (incl. interest)."""
    return LoanService(conn).get_loan_balance_by_member()


@router.get("/loans/{loan_id}")
def get_loan(loan_id: int, conn=Depends(get_connection)):
    loan = LoanService(conn).get_loan(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loan


@router.post("/loans", status_code=201)
def create_loan(loan: LoanCreate, conn=Depends(get_connection)):
    try:
        return LoanService(conn).create_loan(
            loan.member_id, loan.principal, loan.interest_rate_monthly,
            loan.borrow_date, loan.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/loans/{loan_id}/repay", status_code=201)
def repay_loan(loan_id: int, repay: LoanRepayCreate, conn=Depends(get_connection)):
    try:
        result = LoanService(conn).add_repayment(
            loan_id, repay.amount, repay.repay_date, repay.notes,
        )
        if not result:
            raise HTTPException(status_code=404, detail="Loan not found")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
