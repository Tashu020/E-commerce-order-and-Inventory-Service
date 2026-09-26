from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import models
import schemas
import auth

from database import engine, Base, get_db


# Create database tables
Base.metadata.create_all(bind=engine)


# Create FastAPI application
app = FastAPI(title="Order & Inventory Service")


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Order & Inventory Service is running"
    }


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.post("/register", response_model=schemas.Token)
def register(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(models.User)
        .filter_by(username=user.username)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )

    hashed_password = auth.hash_password(
        user.password
    )

    new_user = models.User(
        username=user.username,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = auth.create_access_token(
        {"sub": str(new_user.id)}
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = (
        db.query(models.User)
        .filter_by(username=form_data.username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )

    if not auth.verify_password(
        form_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )

    token = auth.create_access_token(
        {"sub": str(user.id)}
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# --------------------------------------------------
# GET ALL PRODUCTS
# --------------------------------------------------

@app.get(
    "/products",
    response_model=list[schemas.ProductOut]
)
def list_products(
    db: Session = Depends(get_db)
):
    return db.query(models.Product).all()


# --------------------------------------------------
# GET SINGLE PRODUCT
# --------------------------------------------------

@app.get(
    "/products/{product_id}",
    response_model=schemas.ProductOut
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = (
        db.query(models.Product)
        .filter(models.Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


# --------------------------------------------------
# CREATE ORDER
# --------------------------------------------------

@app.post(
    "/orders",
    response_model=schemas.OrderOut
)
def create_order(
    order_req: schemas.OrderRequest,
    idempotency_key: str = Header(...),
    current_user: models.User = Depends(
        auth.get_current_user
    ),
    db: Session = Depends(get_db)
):

    # Check if this request was already processed
    existing = (
        db.query(models.Order)
        .filter_by(
            idempotency_key=idempotency_key
        )
        .first()
    )

    if existing:
        return existing

    try:

        # Get product IDs in a fixed order
        # This helps avoid deadlocks
        product_ids = sorted({
            item.product_id
            for item in order_req.items
        })

        # Lock product rows
        products = {
            product.id: product
            for product in (
                db.query(models.Product)
                .filter(
                    models.Product.id.in_(product_ids)
                )
                .order_by(models.Product.id)
                .with_for_update()
                .all()
            )
        }

        # Check stock
        for item in order_req.items:

            product = products.get(
                item.product_id
            )

            if not product:
                db.rollback()

                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Product "
                        f"{item.product_id} not found"
                    )
                )

            if product.stock < item.quantity:
                db.rollback()

                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Insufficient stock: "
                        f"product={item.product_id}, "
                        f"stock={product.stock}, "
                        f"requested={item.quantity}"
                    )
                )

        # Create the order
        new_order = models.Order(
            user_id=current_user.id,
            idempotency_key=idempotency_key,
            status="confirmed"
        )

        db.add(new_order)

        # Generate order ID
        db.flush()

        # Decrease stock and create order items
        for item in order_req.items:

            products[item.product_id].stock -= (
                item.quantity
            )

            order_item = models.OrderItem(
                order_id=new_order.id,
                product_id=item.product_id,
                quantity=item.quantity
            )

            db.add(order_item)

        # Save everything
        db.commit()

        # Get updated order from database
        db.refresh(new_order)

        return new_order

    except IntegrityError:

        # Roll back failed transaction
        db.rollback()

        # Check whether another request created
        # the order with the same idempotency key
        existing_order = (
            db.query(models.Order)
            .filter_by(
                idempotency_key=idempotency_key
            )
            .first()
        )

        if existing_order:
            return existing_order

        raise


# --------------------------------------------------
# GET ORDER
# --------------------------------------------------

@app.get(
    "/orders/{order_id}",
    response_model=schemas.OrderOut
)
def get_order(
    order_id: int,
    current_user: models.User = Depends(
        auth.get_current_user
    ),
    db: Session = Depends(get_db)
):

    order = (
        db.query(models.Order)
        .filter(
            models.Order.id == order_id
        )
        .first()
    )

    if (
        not order
        or order.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    return order