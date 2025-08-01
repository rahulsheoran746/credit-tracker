import json
from typing import Optional
from app.schemas.transaction_schema import MemberQuery, MemberTransactionsResponse
class TransactionService:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()

    def get_or_create_member(self, member_info):
        name = member_info["name"]
        phone = member_info["phone"]
        village = member_info["village"]
        city = member_info["city"]
        state = member_info["state"]
        # Check if member already exists
        self.cursor.execute(
            "SELECT id FROM members WHERE name = %s AND phone = %s",
            (name, phone)
        )
        result = self.cursor.fetchone()

        if result:
            member_id = result[0]
            print(f"Member already exists with ID: {member_id}")
        else:
            self.cursor.execute(
                "INSERT INTO members (name, phone, village, city, state) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (name, phone, village, city, state)
            )
            member_id = self.cursor.fetchone()[0]
            print(f"Created new member with ID: {member_id}")
        return member_id

    def get_item_type_id(self, transaction_type):
        self.cursor.execute(
            "SELECT id FROM items WHERE name = %s",
            (transaction_type,)
        )
        result = self.cursor.fetchone()
        if not result:
            raise ValueError(f"Invalid transaction_type: {transaction_type}")
        return result[0]

    def insert_transaction(self, member_id, item_type_id, transaction_date, total_amount, amount_given, notes):
        
        # print("Inserting transaction:", member_id, item_type_id, transaction_date, total_amount, amount_given, notes)

        self.cursor.execute(
            """
            INSERT INTO transactions (member_id, item_type_id, transaction_date, total_amount, amount_given, notes)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (member_id, item_type_id, transaction_date, total_amount, amount_given, notes)
        )
        return self.cursor.fetchone()[0]

    def insert_transaction(self, member_id, total_amount, amount_paid, description=None):
        # print("Inserting transaction:", member_id, total_amount, amount_paid, description)
        self.cursor.execute(
            """
            INSERT INTO transactions (member_id, total_amount, amount_paid, description)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (member_id, total_amount, amount_paid, description)
        )
        transaction_id = self.cursor.fetchone()[0]
        print(f"Inserted Transaction with ID: {transaction_id}")
        self.conn.commit() 
        return transaction_id
    def insert_transaction_sweets(self, transaction_id, items, total_amount, amount_given, notes=None):
        remaining_amount = total_amount - amount_given
        items_json = json.dumps(items)

        self.cursor.execute(
            """
            INSERT INTO transaction_sweets (transaction_id, total_amount, amount_given, remaining_amount, items, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (transaction_id, total_amount, amount_given, remaining_amount, items_json, notes)
        )
        self.conn.commit()
        print(f"Inserted sweets transaction with ID: {transaction_id}")


    def process_transaction_payload(self, payload: dict):
        # print("Processing Transaction Payload:", payload)
        member_info = payload["member"]
        print("Member Info:", member_info)
        member_id = self.get_or_create_member(member_info)

        transaction_date = payload["transaction_date"]
        transactions = payload["transactions"]

        total_amount = sum(transaction["total_amount"] for transaction in transactions)
        print("Total Amount:", total_amount)
        amount_given = sum(transaction["amount_given"] for transaction in transactions)
        print("Amount Given:", amount_given)
        transaction_id = self.insert_transaction(
                    member_id,
                    total_amount,
                    amount_given,
                    payload['description']
                )
        for txn in transactions:
            # Currently only handling "sweets", extend for others later
            if txn['transaction_type'] == "sweets":
                self.insert_transaction_sweets(
                        transaction_id=transaction_id,
                        items=txn["items"],
                        total_amount=txn["total_amount"],
                        amount_given=txn["amount_given"],
                        notes=txn.get("notes")
                    )
            elif txn['transaction_type'] == "cattle_feed":
                pass
            elif txn['transaction_type'] == "other":
                pass

        return {"status": "success", "member_id": member_id, "transactions_processed": len(transactions)}


    def get_member_transactions(self, member_query: MemberQuery) -> Optional[MemberTransactionsResponse]:
        sql = """
        SELECT 
            m.name,
            m.phone,
            SUM(t.total_amount) AS total_amount,
            SUM(t.amount_paid) AS amount_paid,
            SUM(t.remaining_amount) AS remaining_amount,
            json_agg(
                json_build_object(
                    'transaction_id', t.id,
                    'transaction_date', t.created_at,
                    'total_amount', t.total_amount,
                    'amount_paid', t.amount_paid,
                    'remaining_amount', t.remaining_amount,
                    'items', ts.items
                )
            ) AS transactions
        FROM transactions t
        JOIN members m ON m.id = t.member_id
        JOIN transaction_sweets ts ON ts.transaction_id = t.id
        WHERE m.name = %s AND m.phone = %s
        GROUP BY m.name, m.phone
        """
        # print("Executing SQL:", sql)
        with self.conn.cursor() as cur:
            cur.execute(sql, (member_query.name, member_query.phone))
            row = cur.fetchone()
            if not row:
                return None

            # row is a tuple: (name, phone, total_amount, amount_paid, remaining_amount, transactions_json)
            name, phone, total_amount, amount_paid, remaining_amount, transactions_json = row
            
            # Construct and return Pydantic model
            return MemberTransactionsResponse(
                name=name,
                phone=phone,
                total_amount=total_amount,
                amount_paid=amount_paid,
                remaining_amount=remaining_amount,
                transactions=transactions_json
            )