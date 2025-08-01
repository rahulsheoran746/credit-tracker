from pydantic import BaseModel

class SweetOut(BaseModel):
    id: int
    name: str
    rate_per_kg: float
    description: str
