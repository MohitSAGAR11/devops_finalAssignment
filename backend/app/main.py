from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db
from .models import Product
from .schemas import (
    InventoryStatsOut,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    StockAdjustment,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Production containers run Alembic before Uvicorn; create_all keeps tests self-contained.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


def to_out(product: Product) -> ProductOut:
    data = {c.name: getattr(product, c.name) for c in Product.__table__.columns}
    return ProductOut(**data, low_stock=product.quantity <= product.reorder_level)


def get_or_404(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def commit_or_409(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A product with this SKU already exists")


@app.get("/")
def root():
    return {"service": settings.app_name, "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "UP"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    db.execute(select(func.count(Product.id)))
    return {"status": "READY"}


@app.get("/api/products", response_model=list[ProductOut])
def list_products(category: str | None = None, db: Session = Depends(get_db)):
    query = select(Product).order_by(Product.id.desc())
    if category:
        query = query.where(Product.category == category)
    return [to_out(p) for p in db.scalars(query)]


@app.get("/api/products/stats", response_model=InventoryStatsOut)
def product_stats(db: Session = Depends(get_db)):
    total, units, low, out, value = db.execute(
        select(
            func.count(Product.id),
            func.coalesce(func.sum(Product.quantity), 0),
            func.count(Product.id).filter(Product.quantity <= Product.reorder_level),
            func.count(Product.id).filter(Product.quantity == 0),
            func.coalesce(func.sum(Product.quantity * Product.unit_price), 0),
        )
    ).one()
    return InventoryStatsOut(
        totalProducts=total,
        totalUnits=units,
        lowStock=low,
        outOfStock=out,
        inventoryValue=round(float(value), 2),
    )


@app.get("/api/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return to_out(get_or_404(db, product_id))


@app.post("/api/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**payload.model_dump())
    db.add(product)
    commit_or_409(db)
    db.refresh(product)
    return to_out(product)


@app.put("/api/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = get_or_404(db, product_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    commit_or_409(db)
    db.refresh(product)
    return to_out(product)


@app.post("/api/products/{product_id}/adjust", response_model=ProductOut)
def adjust_stock(product_id: int, payload: StockAdjustment, db: Session = Depends(get_db)):
    product = get_or_404(db, product_id)
    if product.quantity + payload.delta < 0:
        raise HTTPException(status_code=400, detail="Not enough stock for this adjustment")
    product.quantity += payload.delta
    db.commit()
    db.refresh(product)
    return to_out(product)


@app.delete("/api/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db.delete(get_or_404(db, product_id))
    db.commit()
