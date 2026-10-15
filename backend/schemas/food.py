from pydantic import BaseModel


class FoodAnalysisRequest(BaseModel):
    product_name: str | None = None
