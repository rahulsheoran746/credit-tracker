from app.db import get_connection
from app.schemas.member_schema import MemberCreate

def create_or_get_member(member: MemberCreate):
    conn = get_connection()
    cur = conn.cursor()
    try:
        if len(member.phone) != 10 or not member.phone.isdigit():
            return {"message": "Phone number must be 10 digits long"}
        if not member.name or len(member.name) == 0:
            return {"message": "Name cannot be empty"}
        # Check if member exists based on name and phone
        cur.execute("SELECT id FROM members WHERE name = %s AND phone = %s", (member.name, member.phone))
        row = cur.fetchone()
        if row:
            return {"id": row[0], "message": "Existing member returned"}

        # Insert new member
        cur.execute(
            """
            INSERT INTO members (name, phone, village, city, state)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (member.name, member.phone, member.village, member.city, member.state)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        return {"id": new_id, "message": "New member created"}
    finally:
        cur.close()
        conn.close()
