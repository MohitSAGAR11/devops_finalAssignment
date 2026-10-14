from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    category: str = Field(default="General", min_length=1, max_length=100)
    supplier: str = Field(default="Unspecified", min_length=1, max_length=120)
    quantity: int = Field(default=0, ge=0)

class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    category: str | None = Field(default=None, min_length=1, max_length=100)
    supplier: str | None = Field(default=None, min_length=1, max_length=120)
    quantity: int | None = Field(default=None, ge=0)

class ProductOut(ProductCreate):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class InventoryStatsOut(BaseModel):
    total: int
    totalQuantity: int
    lowStock: int
