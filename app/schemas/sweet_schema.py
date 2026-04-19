from pydantic import BaseModel

class SweetOut(BaseModel):
    id: int
    name: str
    rate_per_kg: float
    description: str

class SweetCreate(BaseModel):
    name: str
    rate_per_kg: float
    description: str = ''

class SweetUpdate(BaseModel):
    rate_per_kg: float
    description: str = ''
