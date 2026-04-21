from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.schemas.product_schema import ProductCreate, ProductUpdate
from app.services.product_service import ProductService
from app.services.audit_service import log_action
from app.auth.deps import get_current_user
from app.db import get_connection

router = APIRouter()


@router.get("/products")
def list_products(
    category: Optional[str] = Query(None, description="Filter by category (e.g. 'sweet', 'cattle_feed')"),
    user=Depends(get_current_user),
    conn=Depends(get_connection),
):
    return ProductService(conn).list_products(category)


@router.post("/products", status_code=201)
def create_product(
    product: ProductCreate,
    user=Depends(get_current_user),
    conn=Depends(get_connection),
):
    try:
        result = ProductService(conn).create(
            product.category, product.name, product.unit, product.price,
            product.unit_size, product.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        if 'unique' in str(e).lower():
            raise HTTPException(status_code=409, detail="A product with this name already exists in this category.")
        raise HTTPException(status_code=500, detail=str(e))
    log_action(conn, user, "create", "product", result["id"], {
        "category": product.category, "name": product.name, "price": product.price,
    })
    return result


@router.put("/products/{product_id}")
def update_product(
    product_id: int,
    product: ProductUpdate,
    user=Depends(get_current_user),
    conn=Depends(get_connection),
):
    try:
        result = ProductService(conn).update(
            product_id, product.price, product.unit_size, product.description,
        )
        if not result:
            raise HTTPException(status_code=404, detail="Product not found.")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    log_action(conn, user, "update", "product", product_id, product.model_dump(exclude_none=True))
    return result
