import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

logger = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))


def _ist_today() -> date:
    return datetime.now(IST).date()


def _compute_balance(principal: Decimal, rate_monthly: Decimal, borrow_date: date,
                     repayments: list, as_of: date = None):
    """
    Reducing-balance simple interest.
    - Interest accrues on current principal.
    - Each repayment first clears accrued interest, then reduces principal.
    - Returns (current_principal, accrued_interest, total_repaid).

    `repayments` is a list of (amount, repay_date) tuples, sorted ascending by date.
    """
    if as_of is None:
        as_of = _ist_today()

    current_principal = Decimal(principal)
    interest_balance  = Decimal(0)
    total_repaid      = Decimal(0)
    rate              = Decimal(rate_monthly) / Decimal(100)  # 2% -> 0.02
    last_date         = borrow_date

    def accrue(until_date):
        nonlocal interest_balance
        if current_principal <= 0 or until_date <= last_date:
            return
        days = (until_date - last_date).days
        # monthly rate × months = rate × (days / 30)
        interest_balance += current_principal * rate * Decimal(days) / Decimal(30)

    for amount, repay_date in repayments:
        amount = Decimal(amount)
        accrue(repay_date)
        # Apply: interest first, then principal
        if amount <= interest_balance:
            interest_balance -= amount
        else:
            remaining = amount - interest_balance
            interest_balance = Decimal(0)
            current_principal -= remaining
            if current_principal < 0:
                # Overpayment — clamp. Extra is not refunded as credit here.
                current_principal = Decimal(0)
        last_date = repay_date

    # Accrue to as_of
    accrue(as_of)

    total_repaid = sum((Decimal(a) for a, _ in repayments), Decimal(0))

    return (
        float(current_principal.quantize(Decimal('0.01'))),
        float(interest_balance.quantize(Decimal('0.01'))),
        float(total_repaid.quantize(Decimal('0.01'))),
    )


def _loan_row_to_dict(row, repayments=None, include_repayments=False):
    (loan_id, member_id, member_name, member_phone, principal, rate, borrow_date,
     notes, created_at, updated_at) = row

    reps = repayments or []
    rep_tuples = [(r[1], r[2]) for r in reps]  # (amount, repay_date)
    cur_principal, accrued, total_repaid = _compute_balance(
        principal, rate, borrow_date, rep_tuples
    )
    total_owed = round(cur_principal + accrued, 2)

    out = {
        "id": loan_id,
        "member_id": member_id,
        "member_name": member_name,
        "member_phone": member_phone,
        "principal": float(principal),
        "interest_rate_monthly": float(rate),
        "borrow_date": borrow_date.isoformat() if borrow_date else None,
        "notes": notes,
        "total_repaid": total_repaid,
        "current_principal": cur_principal,
        "accrued_interest": accrued,
        "total_owed": total_owed,
        "is_closed": total_owed <= 0.005,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }
    if include_repayments:
        out["repayments"] = [
            {
                "id": r[0],
                "amount": float(r[1]),
                "repay_date": r[2].isoformat() if r[2] else None,
                "notes": r[3],
                "created_at": r[4].isoformat() if r[4] else None,
            }
            for r in reps
        ]
    return out


_LOAN_SELECT = """
SELECT l.id, l.member_id, m.name, m.phone,
       l.principal, l.interest_rate_monthly, l.borrow_date,
       l.notes, l.created_at, l.updated_at
FROM loans l
JOIN members m ON m.id = l.member_id
"""


class LoanService:
    def __init__(self, conn):
        self.conn = conn

    def _fetch_repayments(self, loan_id):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, amount, repay_date, notes, created_at
                FROM loan_repayments
                WHERE loan_id = %s
                ORDER BY repay_date ASC, id ASC
                """,
                (loan_id,),
            )
            return cur.fetchall()

    def list_loans(self, include_closed: bool = False):
        with self.conn.cursor() as cur:
            cur.execute(_LOAN_SELECT + " ORDER BY l.borrow_date ASC, l.id ASC")
            rows = cur.fetchall()
        results = []
        for row in rows:
            reps = self._fetch_repayments(row[0])
            data = _loan_row_to_dict(row, reps, include_repayments=True)
            if include_closed or not data["is_closed"]:
                results.append(data)
        return results

    def get_loan(self, loan_id: int, with_repayments: bool = True):
        with self.conn.cursor() as cur:
            cur.execute(_LOAN_SELECT + " WHERE l.id = %s", (loan_id,))
            row = cur.fetchone()
        if not row:
            return None
        reps = self._fetch_repayments(loan_id) if with_repayments else []
        return _loan_row_to_dict(row, reps, include_repayments=with_repayments)

    def get_loans_for_member(self, member_id: int, include_closed: bool = False):
        with self.conn.cursor() as cur:
            cur.execute(_LOAN_SELECT + " WHERE l.member_id = %s ORDER BY l.borrow_date ASC",
                        (member_id,))
            rows = cur.fetchall()
        results = []
        for row in rows:
            reps = self._fetch_repayments(row[0])
            data = _loan_row_to_dict(row, reps, include_repayments=True)
            if include_closed or not data["is_closed"]:
                results.append(data)
        return results

    def get_loan_balance_by_member(self):
        """Return {member_id: total_owed} for all members with open loans."""
        loans = self.list_loans(include_closed=False)
        totals = {}
        for l in loans:
            totals[l["member_id"]] = totals.get(l["member_id"], 0.0) + l["total_owed"]
        return totals

    def create_loan(self, member_id, principal, rate, borrow_date, notes=None):
        if principal is None or principal <= 0:
            raise ValueError("Principal must be greater than zero")
        if rate is None or rate < 0:
            raise ValueError("Interest rate cannot be negative")
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO loans (member_id, principal, interest_rate_monthly, borrow_date, notes)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (member_id, principal, rate, borrow_date, notes),
            )
            new_id = cur.fetchone()[0]
        self.conn.commit()
        logger.info("Loan created: id=%s member_id=%s principal=%s", new_id, member_id, principal)
        return self.get_loan(new_id)

    def add_repayment(self, loan_id, amount, repay_date, notes=None):
        if amount is None or amount <= 0:
            raise ValueError("Repayment amount must be greater than zero")
        # Verify loan exists
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM loans WHERE id = %s", (loan_id,))
            if not cur.fetchone():
                return None
            cur.execute(
                """
                INSERT INTO loan_repayments (loan_id, amount, repay_date, notes)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (loan_id, amount, repay_date, notes),
            )
            cur.execute(
                "UPDATE loans SET updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (loan_id,),
            )
        self.conn.commit()
        logger.info("Repayment recorded: loan_id=%s amount=%s", loan_id, amount)
        return self.get_loan(loan_id)
