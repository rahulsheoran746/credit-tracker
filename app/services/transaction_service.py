from fastapi import HTTPException
from psycopg2.extras import RealDictCursor
from app.db import get_connection
from app.models.transactions import TransactionCreate

def create_transaction_service(txn: TransactionCreate):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Validate required input
        if txn.transaction_type == "sweet":
            if not txn.sweet_id:
                raise HTTPException(status_code=400, detail="Sweet ID is required for sweet transaction.")

            # Fetch sweet price
            cur.execute("SELECT price_per_kg FROM sweets WHERE id = %s", (txn.sweet_id,))
            sweet = cur.fetchone()
            if not sweet:
                raise HTTPException(status_code=404, detail="Sweet item not found.")

            price_per_kg = float(sweet['price_per_kg'])

            if txn.quantity:
                # Calculate amount using quantity
                amount = price_per_kg * txn.quantity
            elif txn.amount:
                # Use provided amount
                amount = txn.amount
            else:
                raise HTTPException(status_code=400, detail="Either quantity or amount must be provided.")
        else:
            raise HTTPException(status_code=400, detail="Only 'sweet' transaction type is implemented.")

        # Insert transaction
        cur.execute("""
            INSERT INTO transactions (member_id, transaction_type, sweet_id, quantity, amount, description)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            txn.member_id,
            txn.transaction_type,
            txn.sweet_id,
            txn.quantity,
            amount,
            txn.description
        ))

        transaction_id = cur.fetchone()["id"]
        conn.commit()

        return {"transaction_id": transaction_id, "message": "Transaction created successfully", "amount": amount}

    finally:
        cur.close()
        conn.close()
