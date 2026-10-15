from pydantic import BaseModel


class ComplaintCreate(BaseModel):
    description: str
    category: str | None = None
    location: str | None = None
