from pydantic import BaseModel

class Sweet(BaseModel):
    name: str
    price_per_unit: float
    available: bool = True
