import logging
from app.schemas.member_schema import MemberCreate

logger = logging.getLogger(__name__)


def _row_to_member(row) -> dict:
    return {
        "id": row[0], "name": row[1], "phone": row[2],
        "village": row[3], "city": row[4], "state": row[5],
    }


def search_members(conn, q: str) -> list:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, name, phone, village, city, state
            FROM members
            WHERE name ILIKE %s
            ORDER BY name
            LIMIT 10
            """,
            (f"%{q}%",),
        )
        return [_row_to_member(r) for r in cur.fetchall()]


def get_all_members(conn) -> list:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT m.id, m.name, m.phone, m.village, m.city, m.state,
                   COALESCE(SUM(t.remaining_amount), 0) AS outstanding_balance
            FROM members m
            LEFT JOIN transactions t ON t.member_id = m.id
            GROUP BY m.id, m.name, m.phone, m.village, m.city, m.state
            ORDER BY m.name
            """
        )
        rows = cur.fetchall()
    return [
        {**_row_to_member(r), "outstanding_balance": float(r[6])}
        for r in rows
    ]


def create_or_get_member(conn, member: MemberCreate):
    if len(member.phone) != 10 or not member.phone.isdigit():
        raise ValueError("Phone number must be 10 digits long")
    if not member.name or len(member.name.strip()) == 0:
        raise ValueError("Name cannot be empty")

    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM members WHERE name = %s AND phone = %s",
            (member.name, member.phone),
        )
        row = cur.fetchone()
        if row:
            logger.info("Existing member returned: id=%s", row[0])
            return {"id": row[0], "message": "Existing member returned"}

        cur.execute(
            """
            INSERT INTO members (name, phone, village, city, state)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (member.name, member.phone, member.village, member.city, member.state),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        logger.info("New member created: id=%s", new_id)
        return {"id": new_id, "message": "New member created"}
