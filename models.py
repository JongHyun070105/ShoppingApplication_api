from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Products 모델
class ProductBase(BaseModel):
    brand_name: str
    product_name: str
    image_url: str
    price: str
    discount: str
    likes: str
    reviews: str
    is_favorite: bool
    category: str

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    brand_name: Optional[str] = None
    product_name: Optional[str] = None
    image_url: Optional[str] = None
    price: Optional[str] = None
    discount: Optional[str] = None
    likes: Optional[str] = None
    reviews: Optional[str] = None
    is_favorite: Optional[bool] = None
    category: Optional[str] = None

class Product(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
    
    def __init__(self, **data):
        # 숫자 필드를 문자열로 변환
        if 'price' in data and isinstance(data['price'], (int, float)):
            data['price'] = str(data['price'])
        if 'discount' in data and isinstance(data['discount'], (int, float)):
            data['discount'] = str(data['discount'])
        super().__init__(**data)

# Q&A 모델
class QABase(BaseModel):
    product_id: int
    question: str
    answer: str
    user_name: str

class QACreate(QABase):
    pass

class QAUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    user_name: Optional[str] = None

class QA(QABase):
    id: int
    created_at: datetime
    answered_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Reviews 모델
class ReviewBase(BaseModel):
    product_id: int
    user_name: str
    rating: int
    content: str

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    user_name: Optional[str] = None
    rating: Optional[int] = None
    content: Optional[str] = None

class Review(ReviewBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Cart Items 모델
class CartItemBase(BaseModel):
    user_id: int
    product_id: int
    quantity: int
    selected_options: str

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: Optional[int] = None
    selected_options: Optional[str] = None

class CartItem(CartItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
