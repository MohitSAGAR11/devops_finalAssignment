from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    category: str = Field(default="General", min_length=1, max_length=100)
    supplier: str = Field(default="Unspecified", min_length=1, max_length=120)
    quantity: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=10, ge=0)
    unit_price: float = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=40)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    category: str | None = Field(default=None, min_length=1, max_length=100)
    supplier: str | None = Field(default=None, min_length=1, max_length=120)
    quantity: int | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    unit_price: float | None = Field(default=None, ge=0)


class StockAdjustment(BaseModel):
    # Positive delta = stock received, negative delta = stock shipped/consumed.
    delta: int

    @field_validator("delta")
    @classmethod
    def delta_not_zero(cls, value: int) -> int:
        if value == 0:
            raise ValueError("delta must not be zero")
        return value


class ProductOut(ProductCreate):
    id: int
    low_stock: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class InventoryStatsOut(BaseModel):
    totalProducts: int
    totalUnits: int
    lowStock: int
    outOfStock: int
    inventoryValue: float
