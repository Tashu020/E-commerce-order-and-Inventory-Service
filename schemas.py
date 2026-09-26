from pydantic import BaseModel
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProductOut(BaseModel):
    id: int
    name: str
    price: float
    stock: int

    class Config:
        from_attributes = True


class OrderItemRequest(BaseModel):
    product_id: int
    quantity: int


class OrderRequest(BaseModel):
    items: list[OrderItemRequest]


class OrderItemOut(BaseModel):
    product_id: int
    quantity: int

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    status: str
    created_at: datetime
    items: list[OrderItemOut]

    class Config:
        from_attributes = True