import logging

logger = logging.getLogger(__name__)


def _row_to_sweet(row) -> dict:
    return {"id": row[0], "name": row[1], "rate_per_kg": float(row[2]), "description": row[3]}


class SweetService:
    def __init__(self, conn):
        self.conn = conn

    def get_all_sweets(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, name, rate_per_kg, description FROM sweets ORDER BY name")
            rows = cur.fetchall()
        return [_row_to_sweet(r) for r in rows]

    def get_sweet_by_id(self, sweet_id: int):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, rate_per_kg, description FROM sweets WHERE id = %s",
                (sweet_id,),
            )
            row = cur.fetchone()
        return _row_to_sweet(row) if row else None

    def create_sweet(self, name: str, rate_per_kg: float, description: str = ''):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO sweets (name, rate_per_kg, description) VALUES (%s, %s, %s) RETURNING id",
                (name.strip(), rate_per_kg, description.strip()),
            )
            new_id = cur.fetchone()[0]
        self.conn.commit()
        logger.info("Sweet created: id=%s name=%s", new_id, name)
        return self.get_sweet_by_id(new_id)

    def update_sweet(self, sweet_id: int, rate_per_kg: float, description: str = ''):
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE sweets SET rate_per_kg = %s, description = %s WHERE id = %s RETURNING id",
                (rate_per_kg, description.strip(), sweet_id),
            )
            row = cur.fetchone()
        if not row:
            return None
        self.conn.commit()
        logger.info("Sweet updated: id=%s", sweet_id)
        return self.get_sweet_by_id(sweet_id)
