import logging
from typing import Optional
from psycopg2.extras import Json
from app.schemas.transaction_schema import MemberQuery, MemberTransactionsResponse

logger = logging.getLogger(__name__)


class TransactionService:
    def __init__(self, conn):
        self.conn = conn

    def get_or_create_member(self, member_info):
        def tc(s):
            return ' '.join(w.capitalize() for w in s.strip().split()) if s else None

        name        = tc(member_info.get("name"))
        father_name = tc(member_info.get("father_name"))
        phone       = member_info["phone"]
        village     = tc(member_info.get("village"))
        city        = tc(member_info.get("city"))
        state       = tc(member_info.get("state"))

        with self.conn.cursor() as cur:
            # Phone is the unique identity — look up by phone alone
            cur.execute("SELECT id FROM members WHERE phone = %s", (phone,))
            result = cur.fetchone()
            if result:
                return result[0]

            cur.execute(
                """
                INSERT INTO members (name, father_name, phone, village, city, state)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (name, father_name, phone, village, city, state),
            )
            member_id = cur.fetchone()[0]
            return member_id

    def insert_transaction(self, member_id, txn_type, total_amount, amount_paid,
                           cash_amount=0, upi_amount=0,
                           description=None, transaction_date=None):
        """
        transaction_date: optional datetime to override DB default CURRENT_TIMESTAMP.
        Used for backdated entries (e.g. a paper-ledger entry being digitised at night).

        cash_amount + upi_amount must equal amount_paid for new entries; backend
        accepts whatever the caller sends (no constraint enforced at DB level so
        legacy rows with NULL still work).
        """
        with self.conn.cursor() as cur:
            if transaction_date is not None:
                cur.execute(
                    """
                    INSERT INTO transactions (member_id, type, total_amount, amount_paid,
                                              cash_amount, upi_amount, description, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (member_id, txn_type, total_amount, amount_paid,
                     cash_amount, upi_amount, description, transaction_date),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO transactions (member_id, type, total_amount, amount_paid,
                                              cash_amount, upi_amount, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (member_id, txn_type, total_amount, amount_paid,
                     cash_amount, upi_amount, description),
                )
            transaction_id = cur.fetchone()[0]
        return transaction_id

    def insert_transaction_items(self, transaction_id, items, total_amount, amount_given, notes=None):
        remaining_amount = total_amount - amount_given
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO transaction_items (transaction_id, total_amount, amount_given, remaining_amount, items, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (transaction_id, total_amount, amount_given, remaining_amount, Json(items), notes),
            )

    def process_transaction_payload(self, payload: dict):
        try:
            member_id = self.get_or_create_member(payload["member"])

            transactions = payload["transactions"]
            # One "entry" always maps to one transactions row.
            # Pick the type from the first block (current UI only sends one block per save).
            txn_type = transactions[0].get("type", "sale") if transactions else "sale"

            total_amount = amount_given = 0
            cash_total = upi_total = 0
            for t in transactions:
                total_amount += t["total_amount"]
                amount_given += t["amount_given"]
                cash_total   += t.get("cash_amount", 0) or 0
                upi_total    += t.get("upi_amount",  0) or 0

            transaction_id = self.insert_transaction(
                member_id,
                txn_type,
                total_amount,
                amount_given,
                cash_amount=cash_total,
                upi_amount=upi_total,
                description=payload.get("description"),
                transaction_date=payload.get("transaction_date"),
            )

            # Only sales have line items; repayments don't create a transaction_items row.
            for txn in transactions:
                if txn.get("type", "sale") == "sale" and txn.get("items"):
                    self.insert_transaction_items(
                        transaction_id=transaction_id,
                        items=txn["items"],
                        total_amount=txn["total_amount"],
                        amount_given=txn["amount_given"],
                        notes=txn.get("notes"),
                    )

            self.conn.commit()
            return {"status": "success", "member_id": member_id, "transactions_processed": len(transactions)}

        except Exception:
            self.conn.rollback()
            logger.exception("Transaction failed, rolled back")
            raise

    def get_member_transactions(self, member_query: MemberQuery) -> Optional[MemberTransactionsResponse]:
        # Lookup by phone (the unique identity). Name is accepted for compatibility
        # but ignored — the stored name in the DB is the source of truth.
        sql = """
        SELECT
            m.name,
            m.phone,
            m.father_name,
            SUM(t.total_amount)     AS total_amount,
            SUM(t.amount_paid)      AS amount_paid,
            SUM(t.remaining_amount) AS remaining_amount,
            json_agg(
                json_build_object(
                    'transaction_id',   t.id,
                    'transaction_date', t.created_at,
                    'type',             t.type,
                    'total_amount',     t.total_amount,
                    'amount_paid',      t.amount_paid,
                    'remaining_amount', t.remaining_amount,
                    'cash_amount',      t.cash_amount,
                    'upi_amount',       t.upi_amount,
                    'items',            COALESCE(ts.items, '[]'::jsonb)
                )
                ORDER BY t.created_at DESC
            ) AS transactions
        FROM transactions t
        JOIN members m ON m.id = t.member_id
        LEFT JOIN transaction_items ts ON ts.transaction_id = t.id
        WHERE m.phone = %s
        GROUP BY m.name, m.phone, m.father_name
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (member_query.phone,))
            row = cur.fetchone()
            if not row:
                return None

            name, phone, father_name, total_amount, amount_paid, remaining_amount, transactions_json = row
            return MemberTransactionsResponse(
                name=name,
                phone=phone,
                father_name=father_name,
                total_amount=total_amount,
                amount_paid=amount_paid,
                remaining_amount=remaining_amount,
                transactions=transactions_json,
            )
