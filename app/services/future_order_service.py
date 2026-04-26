import logging
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)

ALLOWED_CATEGORIES = {"cattle_feed", "wholesale"}


def _row_to_dict(row, items=None):
    """row is the SELECT below joined to members."""
    (oid, member_id, member_name, member_phone, pickup_date, status,
     token_cash, token_upi, notes, cancel_reason, refund_due,
     fulfilled_transaction_id, created_at, updated_at) = row

    its = items or []
    items_total = round(sum(float(i["amount"]) for i in its), 2)
    tc = float(token_cash or 0)
    tu = float(token_upi  or 0)

    return {
        "id": oid,
        "member_id": member_id,
        "member_name": member_name,
        "member_phone": member_phone,
        "pickup_date": pickup_date.isoformat() if pickup_date else None,
        "status": status,
        "token_cash": tc,
        "token_upi":  tu,
        "token_total": round(tc + tu, 2),
        "notes": notes,
        "cancel_reason": cancel_reason,
        "refund_due": float(refund_due or 0),
        "fulfilled_transaction_id": fulfilled_transaction_id,
        "items": its,
        "items_total": items_total,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


_ORDER_SELECT = """
SELECT o.id, o.member_id, m.name, m.phone, o.pickup_date, o.status,
       o.token_cash, o.token_upi, o.notes, o.cancel_reason, o.refund_due,
       o.fulfilled_transaction_id, o.created_at, o.updated_at
FROM future_orders o
JOIN members m ON m.id = o.member_id
"""


class FutureOrderService:
    def __init__(self, conn):
        self.conn = conn

    # ── helpers ──────────────────────────────────────────────────

    def _fetch_items(self, order_id):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, product_id, category, name, unit, quantity, price, amount
                FROM future_order_items
                WHERE future_order_id = %s
                ORDER BY id ASC
                """,
                (order_id,),
            )
            rows = cur.fetchall()
        return [
            {
                "id": r[0], "product_id": r[1], "category": r[2], "name": r[3],
                "unit": r[4], "quantity": float(r[5]), "price": float(r[6]),
                "amount": float(r[7]),
            }
            for r in rows
        ]

    def _validate_items(self, items):
        if not items:
            raise ValueError("At least one item is required.")
        for it in items:
            if it.get("category") not in ALLOWED_CATEGORIES:
                raise ValueError(
                    f"Item '{it.get('name')}' is not eligible for future orders. "
                    "Only cattle feed and bulk items are supported."
                )
            if not (float(it.get("quantity", 0)) > 0):
                raise ValueError(f"Item '{it.get('name')}' must have a positive quantity.")
            if not (float(it.get("amount", 0)) > 0):
                raise ValueError(f"Item '{it.get('name')}' must have a positive amount.")

    def _insert_items(self, order_id, items):
        with self.conn.cursor() as cur:
            for it in items:
                cur.execute(
                    """
                    INSERT INTO future_order_items
                        (future_order_id, product_id, category, name, unit,
                         quantity, price, amount)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (order_id, it["product_id"], it["category"], it["name"], it["unit"],
                     it["quantity"], it["price"], it["amount"]),
                )

    # ── public API ───────────────────────────────────────────────

    def list_orders(self, status=None, pickup_from=None, pickup_to=None, member_id=None):
        clauses = []
        params  = []
        if status:
            clauses.append("o.status = %s"); params.append(status)
        if pickup_from:
            clauses.append("o.pickup_date >= %s"); params.append(pickup_from)
        if pickup_to:
            clauses.append("o.pickup_date <= %s"); params.append(pickup_to)
        if member_id is not None:
            clauses.append("o.member_id = %s"); params.append(member_id)

        sql = _ORDER_SELECT
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY o.pickup_date ASC, o.id ASC"

        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        results = []
        for row in rows:
            items = self._fetch_items(row[0])
            results.append(_row_to_dict(row, items))
        return results

    def get_order(self, order_id):
        with self.conn.cursor() as cur:
            cur.execute(_ORDER_SELECT + " WHERE o.id = %s", (order_id,))
            row = cur.fetchone()
        if not row:
            return None
        items = self._fetch_items(order_id)
        return _row_to_dict(row, items)

    def create_order(self, payload: dict):
        items = payload.get("items", [])
        self._validate_items(items)
        token_cash = float(payload.get("token_cash") or 0)
        token_upi  = float(payload.get("token_upi")  or 0)
        if token_cash < 0 or token_upi < 0:
            raise ValueError("Token amounts cannot be negative.")

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO future_orders
                    (member_id, pickup_date, token_cash, token_upi, notes)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (payload["member_id"], payload["pickup_date"],
                 token_cash, token_upi, payload.get("notes")),
            )
            order_id = cur.fetchone()[0]
        self._insert_items(order_id, items)
        self.conn.commit()
        return self.get_order(order_id)

    def cancel_order(self, order_id, reason=None):
        order = self.get_order(order_id)
        if not order:
            return None
        if order["status"] != "pending":
            raise ValueError(
                f"Order is already {order['status']} and cannot be cancelled."
            )
        # Token paid becomes refund due — handled offline by the worker.
        refund_due = order["token_total"]
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE future_orders
                SET status = 'cancelled',
                    cancel_reason = %s,
                    refund_due    = %s,
                    updated_at    = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (reason, refund_due, order_id),
            )
        self.conn.commit()
        return self.get_order(order_id)

    def fulfill_order(self, order_id, payload: dict):
        order = self.get_order(order_id)
        if not order:
            return None
        if order["status"] != "pending":
            raise ValueError(
                f"Order is already {order['status']} and cannot be fulfilled."
            )

        items = payload.get("items", [])
        self._validate_items(items)

        final_total = round(sum(float(i["amount"]) for i in items), 2)
        token_total = order["token_total"]
        token_cash  = order["token_cash"]
        token_upi   = order["token_upi"]

        fresh_cash = float(payload.get("cash_amount") or 0)
        fresh_upi  = float(payload.get("upi_amount")  or 0)
        if fresh_cash < 0 or fresh_upi < 0:
            raise ValueError("Payment amounts cannot be negative.")
        fresh_total = round(fresh_cash + fresh_upi, 2)

        # Customer cannot pay MORE than what's due today (token already covers part of it).
        due_now = max(0.0, round(final_total - token_total, 2))
        if fresh_total > due_now + 0.005:
            raise ValueError(
                f"Fresh payment ₹{fresh_total:.2f} exceeds amount due ₹{due_now:.2f}. "
                "Token already covers the rest." if token_total > 0 else
                f"Fresh payment ₹{fresh_total:.2f} exceeds order total ₹{final_total:.2f}."
            )

        # Sale transaction values: customer is billed final_total. We apply the
        # full collected amount up to final_total. The excess (if any) is refund_due,
        # tracked on the order row for the worker to hand back offline.
        total_collected = round(token_total + fresh_total, 2)
        applied  = min(total_collected, final_total)
        refund   = round(max(0.0, total_collected - final_total), 2)

        # Cash/UPI breakdown for the sale: proportional to total collected.
        if total_collected > 0 and refund > 0:
            ratio = applied / total_collected
            sale_cash = round((token_cash + fresh_cash) * ratio, 2)
            sale_upi  = round(applied - sale_cash, 2)
        else:
            sale_cash = round(token_cash + fresh_cash, 2)
            sale_upi  = round(token_upi  + fresh_upi,  2)

        # Build description noting the token application + refund (if any).
        descr_parts = [f"Fulfilled future order #{order_id}"]
        if token_total > 0:
            descr_parts.append(f"₹{token_total:.2f} token applied")
        if refund > 0:
            descr_parts.append(f"₹{refund:.2f} refund due")
        description = " — ".join(descr_parts)

        # Insert sale transaction + items via existing helpers, then update the order.
        # All inside the open connection so a failure rolls back atomically.
        try:
            txn_svc = TransactionService(self.conn)
            transaction_id = txn_svc.insert_transaction(
                order["member_id"], "sale", final_total, applied,
                cash_amount=sale_cash, upi_amount=sale_upi,
                description=description,
            )
            txn_svc.insert_transaction_items(
                transaction_id=transaction_id,
                items=[
                    {
                        "product_id": i["product_id"],
                        "category":   i["category"],
                        "name":       i["name"],
                        "unit":       i["unit"],
                        "quantity":   i["quantity"],
                        "price":      i["price"],
                        "amount":     i["amount"],
                    }
                    for i in items
                ],
                total_amount=final_total,
                amount_given=applied,
            )
            with self.conn.cursor() as cur:
                # Replace items with the (possibly edited) final list, then mark fulfilled.
                cur.execute(
                    "DELETE FROM future_order_items WHERE future_order_id = %s",
                    (order_id,),
                )
            self._insert_items(order_id, items)
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE future_orders
                    SET status = 'fulfilled',
                        fulfilled_transaction_id = %s,
                        refund_due = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (transaction_id, refund, order_id),
                )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            logger.exception("Future order fulfillment failed, rolled back")
            raise

        return self.get_order(order_id)
