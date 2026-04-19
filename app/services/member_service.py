import logging
from app.schemas.member_schema import MemberCreate

logger = logging.getLogger(__name__)


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
