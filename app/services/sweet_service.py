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
