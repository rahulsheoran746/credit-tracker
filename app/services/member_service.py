import logging
from app.schemas.member_schema import MemberCreate, MemberUpdate

logger = logging.getLogger(__name__)


def _title_case(text: str) -> str:
    return ' '.join(w.capitalize() for w in text.strip().split()) if text else ''


def _row_to_member(row) -> dict:
    return {
        "id": row[0], "name": row[1], "father_name": row[2], "phone": row[3],
        "village": row[4], "city": row[5], "state": row[6],
    }


_SELECT_COLS = "id, name, father_name, phone, village, city, state"


def search_members(conn, q: str) -> list:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT {_SELECT_COLS}
            FROM members
            WHERE name ILIKE %s OR father_name ILIKE %s OR phone ILIKE %s
            ORDER BY name
            LIMIT 10
            """,
            (f"%{q}%", f"%{q}%", f"%{q}%"),
        )
        return [_row_to_member(r) for r in cur.fetchall()]


def get_all_members(conn) -> list:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT m.id, m.name, m.father_name, m.phone, m.village, m.city, m.state,
                   COALESCE(SUM(t.remaining_amount), 0) AS outstanding_balance
            FROM members m
            LEFT JOIN transactions t ON t.member_id = m.id
            GROUP BY m.id
            ORDER BY m.name
            """
        )
        rows = cur.fetchall()
    return [
        {**_row_to_member(r), "outstanding_balance": float(r[7])}
        for r in rows
    ]


def create_or_get_member(conn, member: MemberCreate):
    if len(member.phone) != 10 or not member.phone.isdigit():
        raise ValueError("Phone number must be 10 digits long")
    if not member.name or len(member.name.strip()) == 0:
        raise ValueError("Name cannot be empty")

    with conn.cursor() as cur:
        # Phone is unique identity — look up by phone only
        cur.execute("SELECT id, name FROM members WHERE phone = %s", (member.phone,))
        row = cur.fetchone()
        if row:
            logger.info("Existing member returned: id=%s (stored name=%s)", row[0], row[1])
            return {
                "id": row[0],
                "message": f"Phone already registered as '{row[1]}' — using that record.",
            }

        cur.execute(
            """
            INSERT INTO members (name, father_name, phone, village, city, state)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                _title_case(member.name),
                _title_case(member.father_name) if member.father_name else None,
                member.phone,
                _title_case(member.village) if member.village else None,
                _title_case(member.city) if member.city else None,
                _title_case(member.state) if member.state else None,
            ),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        logger.info("New member created: id=%s", new_id)
        return {"id": new_id, "message": "New member created"}


def update_member(conn, member_id: int, member: MemberUpdate):
    if len(member.phone) != 10 or not member.phone.isdigit():
        raise ValueError("Phone number must be 10 digits long")
    if not member.name or len(member.name.strip()) == 0:
        raise ValueError("Name cannot be empty")

    with conn.cursor() as cur:
        # Ensure phone isn't already used by a different member
        cur.execute(
            "SELECT id FROM members WHERE phone = %s AND id <> %s",
            (member.phone, member_id),
        )
        if cur.fetchone():
            raise ValueError("Phone number is already registered to another member")

        cur.execute(
            """
            UPDATE members
            SET name = %s, father_name = %s, phone = %s,
                village = %s, city = %s, state = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
            """,
            (
                _title_case(member.name),
                _title_case(member.father_name) if member.father_name else None,
                member.phone,
                _title_case(member.village) if member.village else None,
                _title_case(member.city) if member.city else None,
                _title_case(member.state) if member.state else None,
                member_id,
            ),
        )
        row = cur.fetchone()
    if not row:
        return None
    conn.commit()
    logger.info("Member updated: id=%s", member_id)
    return {"id": member_id, "message": "Member updated"}
