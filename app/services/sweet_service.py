class SweetService:
    def __init__(self, conn):
        self.conn = conn
        self.cur = conn.cursor()

    def _close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def get_all_sweets(self):
        try:
            self.cur.execute("SELECT id, name, rate_per_kg, description FROM sweets ORDER BY name")
            rows = self.cur.fetchall()
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "rate_per_kg": float(row[2]),
                    "description": row[3]
                } for row in rows
            ]
        finally:
            self._close()

    def get_sweet_by_id(self, sweet_id: int):
        try:
            self.cur.execute("SELECT id, name, rate_per_kg, description FROM sweets WHERE id = %s", (sweet_id,))
            row = self.cur.fetchone()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "rate_per_kg": float(row[2]),
                    "description": row[3]
                }
            return None
        finally:
            self._close()
