import logging
from app.schemas.product_schema import VALID_CATEGORIES

logger = logging.getLogger(__name__)


def _row_to_product(row) -> dict:
    return {
        "id":          row[0],
        "category":    row[1],
        "name":        row[2],
        "unit":        row[3],
        "unit_size":   float(row[4]) if row[4] is not None else None,
        "price":       float(row[5]),
        "description": row[6] or '',
        "created_at":  row[7].isoformat() if row[7] else None,
        "updated_at":  row[8].isoformat() if row[8] else None,
    }


_SELECT = "id, category, name, unit, unit_size, price, description, created_at, updated_at"


class ProductService:
    def __init__(self, conn):
        self.conn = conn

    def list_products(self, category: str = None):
        with self.conn.cursor() as cur:
            if category:
                cur.execute(
                    f"SELECT {_SELECT} FROM products WHERE category = %s ORDER BY name",
                    (category,),
                )
            else:
                cur.execute(f"SELECT {_SELECT} FROM products ORDER BY category, name")
            return [_row_to_product(r) for r in cur.fetchall()]

    def get_by_id(self, product_id: int):
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT {_SELECT} FROM products WHERE id = %s", (product_id,))
            row = cur.fetchone()
        return _row_to_product(row) if row else None

    def create(self, category: str, name: str, unit: str, price: float,
               unit_size: float = None, description: str = ''):
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category. Allowed: {sorted(VALID_CATEGORIES)}")
        if not name or not name.strip():
            raise ValueError("Name cannot be empty")
        if price is None or price <= 0:
            raise ValueError("Price must be greater than zero")

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO products (category, name, unit, unit_size, price, description)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (category, name.strip(), unit, unit_size, price, (description or '').strip()),
            )
            new_id = cur.fetchone()[0]
        self.conn.commit()
        logger.info("Product created: id=%s category=%s name=%s", new_id, category, name)
        return self.get_by_id(new_id)

    def update(self, product_id: int, price: float, unit_size: float = None, description: str = ''):
        if price is None or price <= 0:
            raise ValueError("Price must be greater than zero")

        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE products
                SET price = %s, unit_size = %s, description = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id
                """,
                (price, unit_size, (description or '').strip(), product_id),
            )
            row = cur.fetchone()
        if not row:
            return None
        self.conn.commit()
        logger.info("Product updated: id=%s", product_id)
        return self.get_by_id(product_id)
