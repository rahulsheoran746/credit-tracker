from app.db import get_connection

def get_all_sweets():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, name, rate_per_kg, description FROM sweets ORDER BY name")
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "name": row[1],
                "rate_per_kg": float(row[2]),
                "description": row[3]
            } for row in rows
        ]
    finally:
        cur.close()
        conn.close()
