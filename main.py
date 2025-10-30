"""
E-Commerce Shop API
==================

Supabase 기반 쇼핑몰 RESTful API 서버

주요 기능:
- 상품 관리
- 사용자 장바구니 및 즐겨찾기
- 통합 API 엔드포인트
- 실시간 데이터 동기화

Version: 1.0.0
"""

# ============================================================================
# Import
# ============================================================================

from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from supabase_client import get_supabase_client
from supabase import Client
import logging
import json
import uvicorn
from models import (
    Product, ProductCreate, ProductUpdate,
    QA, QACreate, QAUpdate,
    Review, ReviewCreate, ReviewUpdate,
    CartItem, CartItemCreate, CartItemUpdate
)

# ============================================================================
# Application Configuration
# ============================================================================

app = FastAPI(
    title="Shop API",
    description="Supabase 기반 E-Commerce API",
    version="1.0.0",
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CORS 설정 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ============================================================================
# Dependency Injection
# ============================================================================

def get_supabase() -> Client:
    """
    Supabase 클라이언트 의존성 주입
    
    Returns:
        Client: Supabase 클라이언트 인스턴스
        
    Raises:
        HTTPException: 데이터베이스 연결 실패 시
    """
    try:
        return get_supabase_client()
    except Exception as e:
        logger.error(f"Supabase 연결 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="데이터베이스 연결 실패")

# ============================================================================
# Utility Functions
# ============================================================================

def format_product_data(products: List[dict]) -> List[dict]:
    """
    상품 데이터 포맷팅 및 API URL 생성
    
    Args:
        products: 원본 상품 데이터 리스트
        
    Returns:
        List[dict]: 포맷팅된 상품 데이터 (가격, 할인율, API URLs 포함)
    """
    for product in products:
        product_id = product['id']
        
        # 가격 포맷팅 (천 단위 콤마)
        price = int(product['price']) if isinstance(product['price'], (int, float)) else int(product['price'])
        product['price'] = f"{price:,}원"
        
        # 할인율 포맷팅 (퍼센트)
        discount = int(product['discount']) if isinstance(product['discount'], (int, float)) else int(product['discount'])
        product['discount'] = f"{discount}%"
        
        # API URLs 생성
        product['api_urls'] = {
            "get": f"http://localhost:8001/api/get/{product_id}",
            "favorite": f"http://localhost:8001/api/favorite/{product_id}",
            "cart_add": f"http://localhost:8001/api/cart-add/{product_id}",
            "cart_remove": f"http://localhost:8001/api/cart-remove/{product_id}",
            "cart_update": f"http://localhost:8001/api/cart-update/{product_id}"
        }
    
    return products

def create_standard_response(data: any, message: str = "Success") -> Response:
    """
    API 응답 생성
    
    Args:
        data: 응답 데이터
        message: 응답 메시지
        
    Returns:
        Response: JSON 응답
    """
    response_data = {
        "header": {
            "content-type": "application/json; charset=utf-8",
            "server": "FastAPI",
            "date": datetime.now().isoformat() + "Z"
        },
        "body": {
            "code": "200",
            "message": message,
            "data": data
        }
    }
    
    json_str = json.dumps(response_data, ensure_ascii=False, indent=2)
    return Response(
        content=json_str,
        media_type="application/json; charset=utf-8",
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

# ============================================================================
# Core API Endpoints
# ============================================================================

@app.get("/")
async def health_check():
    """
    API 서버 상태 확인
    
    Returns:
        dict: 서버 상태 정보
    """
    return {"message": "Shop API 서버가 정상적으로 실행 중입니다!", "status": "healthy"}

# ============================================================================
# Product Management APIs
# ============================================================================

@app.get("/products")
async def get_products(
    offset: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
    supabase: Client = Depends(get_supabase)
):
    """
    상품 목록 조회 (페이지네이션 지원)
    
    Args:
        offset: 시작 인덱스 (기본값: 0)
        limit: 조회할 상품 수 (기본값: 20)
        category: 카테고리 필터 (선택사항)
        supabase: Supabase 클라이언트
        
    Returns:
        Response: 상품 목록
        
    Raises:
        HTTPException: 데이터베이스 조회 실패 시
    """
    try:
        logger.info(f"상품 목록 조회 - offset: {offset}, limit: {limit}, category: {category}")
        
        query = supabase.table("products").select("*")
        
        # 카테고리 필터링
        if category and category != "전체":
            query = query.eq("category", category)
        
        # 페이지네이션 및 정렬
        response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        # 데이터 포맷팅
        formatted_products = format_product_data(response.data)
        
        logger.info(f"상품 목록 조회 성공 - {len(formatted_products)}개 상품 반환")
        
        return create_standard_response(formatted_products)
        
    except Exception as e:
        logger.error(f"상품 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/all")
async def get_all_products(supabase: Client = Depends(get_supabase)):
    """
    전체 상품 조회 (페이지네이션 없음)
    
    Args:
        supabase: Supabase 클라이언트
        
    Returns:
        Response: 전체 상품 목록
    """
    try:
        logger.info("전체 상품 조회 요청")
        response = supabase.table("products").select("*").order("created_at", desc=True).execute()
        
        formatted_products = format_product_data(response.data)
        
        logger.info(f"전체 상품 조회 성공 - {len(formatted_products)}개 상품")
        
        return create_standard_response(formatted_products)
        
    except Exception as e:
        logger.error(f"전체 상품 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/{product_id}")
async def get_product(product_id: int, supabase: Client = Depends(get_supabase)):
    """
    특정 상품 상세 정보 조회
    
    Args:
        product_id: 상품 ID
        supabase: Supabase 클라이언트
        
    Returns:
        Response: 상품 상세 정보
        
    Raises:
        HTTPException: 상품을 찾을 수 없을 때 (404)
    """
    try:
        logger.info(f"상품 상세 조회 - product_id: {product_id}")
        
        response = supabase.table("products").select("*").eq("id", product_id).execute()
        
        if not response.data:
            logger.warning(f"상품을 찾을 수 없음 - product_id: {product_id}")
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
        
        product = response.data[0]
        formatted_products = format_product_data([product])
        
        logger.info(f"상품 상세 조회 성공 - {product['brand_name']} - {product['product_name']}")
        
        return create_standard_response(formatted_products[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"상품 상세 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Unified Product API - Lucy Studio 최적화
# ============================================================================

@app.get("/api/{action}/{product_id}")
async def unified_product_api(
    action: str, 
    product_id: int, 
    user_id: int = 1, 
    quantity: int = 1,
    supabase: Client = Depends(get_supabase)
):
    """
    통합 상품 API
    
    하나의 엔드포인트로 모든 상품 관련 액션을 처리합니다.
    모든 응답이 동일한 구조를 가지므로 일관된 처리가 가능합니다.
    
    지원하는 액션:
    - get: 상품 정보 조회
    - favorite: 즐겨찾기 토글
    - cart-add: 장바구니 추가
    - cart-remove: 장바구니 삭제
    - cart-update: 장바구니 수량 변경
    
    Args:
        action: 실행할 액션 (get, favorite, cart-add, cart-remove, cart-update)
        product_id: 상품 ID
        user_id: 사용자 ID (기본값: 1)
        quantity: 수량 (기본값: 1)
        supabase: Supabase 클라이언트
        
    Returns:
        Response: 통일된 형식의 응답
        
    Raises:
        HTTPException: 잘못된 액션 또는 데이터베이스 오류 시
    """
    try:
        logger.info(f"통합 API 호출 - action: {action}, product_id: {product_id}")
        
        message = ""
        
        # 액션별 비즈니스 로직 처리
        if action == "favorite":
            # 즐겨찾기 토글 로직
            current = supabase.table("products").select("is_favorite, likes").eq("id", product_id).execute()
            if not current.data:
                raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
            
            current_favorite = current.data[0]["is_favorite"]
            current_likes = int(current.data[0]["likes"] or "0")
            new_favorite = not current_favorite
            new_likes = current_likes + (1 if new_favorite else -1)
            new_likes = max(0, new_likes)
            
            supabase.table("products").update({
                "is_favorite": new_favorite,
                "likes": str(new_likes)
            }).eq("id", product_id).execute()
            
            message = "즐겨찾기가 토글되었습니다" if new_favorite else "즐겨찾기가 해제되었습니다"
            
        elif action == "cart-add":
            # 장바구니 추가 로직
            existing = supabase.table("cart_items").select("*").eq("user_id", user_id).eq("product_id", product_id).execute()
            if existing.data:
                current_qty = existing.data[0]["quantity"]
                new_qty = current_qty + quantity
                supabase.table("cart_items").update({"quantity": new_qty}).eq("user_id", user_id).eq("product_id", product_id).execute()
                message = f"장바구니 수량이 {new_qty}개로 업데이트되었습니다"
            else:
                supabase.table("cart_items").insert({
                    "user_id": user_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "selected_options": ""
                }).execute()
                message = "장바구니에 추가되었습니다"
                
        elif action == "cart-remove":
            # 장바구니 삭제 로직
            supabase.table("cart_items").delete().eq("user_id", user_id).eq("product_id", product_id).execute()
            message = "장바구니에서 삭제되었습니다"
            
        elif action == "cart-update":
            # 장바구니 수량 변경 로직
            supabase.table("cart_items").update({"quantity": quantity}).eq("user_id", user_id).eq("product_id", product_id).execute()
            message = f"수량이 {quantity}개로 변경되었습니다"
            
        elif action == "get":
            # 조회만 수행
            message = "상품 정보를 조회했습니다"
        else:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 액션: {action}")
        
        # 최신 상품 정보 조회
        product_response = supabase.table("products").select("*").eq("id", product_id).execute()
        if not product_response.data:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
        
        product = product_response.data[0]
        formatted_products = format_product_data([product])
        
        # 장바구니 상태 조회
        cart_response = supabase.table("cart_items").select("*").eq("user_id", user_id).eq("product_id", product_id).gt("quantity", 0).execute()
        in_cart = len(cart_response.data) > 0
        cart_quantity = cart_response.data[0]['quantity'] if cart_response.data else 0
        
        logger.info(f"통합 API 성공 - {action} 완료")
        
        # 통일된 응답 구조
        response_data = {
            "product": formatted_products[0],
            "is_favorite": product.get('is_favorite', False),
            "in_cart": in_cart,
            "cart_quantity": cart_quantity,
            "likes": int(product.get('likes', 0))
        }
        
        return create_standard_response(response_data, message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"통합 API 실패 - {action}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# User Data APIs
# ============================================================================

@app.get("/user/cart-and-favorites")
async def get_user_cart_and_favorites(user_id: int = 1, supabase: Client = Depends(get_supabase)):
    """
    사용자의 장바구니와 즐겨찾기 목록을 한 번에 조회
    
    Args:
        user_id: 사용자 ID (기본값: 1)
        supabase: Supabase 클라이언트
        
    Returns:
        Response: 사용자의 장바구니와 즐겨찾기 데이터
    """
    try:
        logger.info(f"사용자 데이터 조회 - user_id: {user_id}")
        
        # 장바구니 조회
        cart_response = supabase.table("cart_items").select("""
            *,
            products:product_id (*)
        """).eq("user_id", user_id).gt("quantity", 0).execute()
        
        # 즐겨찾기 조회
        favorites_response = supabase.table("products").select("*").eq("is_favorite", True).execute()
        
        # 데이터 포맷팅
        cart_items = []
        for item in cart_response.data:
            if item.get('products'):
                product = item['products'].copy()
                formatted_products = format_product_data([product])
                cart_items.append({
                    "cart_item_id": item['id'],
                    "quantity": item['quantity'],
                    "product": formatted_products[0]
                })
        
        favorites = format_product_data(favorites_response.data)
        
        logger.info(f"사용자 데이터 조회 성공 - 장바구니: {len(cart_items)}개, 즐겨찾기: {len(favorites)}개")
        
        response_data = {
            "user_id": user_id,
            "cart_items": cart_items,
            "favorites": favorites,
            "cart_count": len(cart_items),
            "favorites_count": len(favorites)
        }
        
        return create_standard_response(response_data)
        
    except Exception as e:
        logger.error(f"사용자 데이터 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Favorites & Cart APIs
# ============================================================================

@app.get("/products-favorites")
async def get_favorite_products(supabase: Client = Depends(get_supabase)):
    """
    즐겨찾기 상품 조회
    
    Args:
        supabase: Supabase 클라이언트
        
    Returns:
        Response: 즐겨찾기 상품 목록
    """
    try:
        logger.info("즐겨찾기 상품 조회")
        response = supabase.table("products").select("*").eq("is_favorite", True).order("created_at", desc=True).execute()
        
        formatted_products = format_product_data(response.data)
        
        logger.info(f"즐겨찾기 상품 조회 성공 - {len(formatted_products)}개 상품")
        
        return create_standard_response(formatted_products)
        
    except Exception as e:
        logger.error(f"즐겨찾기 상품 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cart-items")
async def get_cart_items(user_id: Optional[int] = None, supabase: Client = Depends(get_supabase)):
    """
    장바구니 아이템 조회
    
    Args:
        user_id: 사용자 ID (선택사항)
        supabase: Supabase 클라이언트
        
    Returns:
        Response: 장바구니 아이템 목록
    """
    try:
        logger.info(f"장바구니 아이템 조회 - user_id: {user_id}")
        
        query = supabase.table("cart_items").select("""
            *,
            products:product_id (*)
        """).gt("quantity", 0)
        
        if user_id:
            query = query.eq("user_id", user_id)
            
        response = query.order("created_at", desc=True).execute()
        
        # 상품 정보 포맷팅
        cart_items = []
        for item in response.data:
            if item.get('products'):
                product = item['products'].copy()
                formatted_products = format_product_data([product])
                cart_items.append({
                    "cart_item_id": item['id'],
                    "quantity": item['quantity'],
                    "user_id": item['user_id'],
                    "product": formatted_products[0]
                })
        
        logger.info(f"장바구니 아이템 조회 성공 - {len(cart_items)}개 아이템")
        
        return create_standard_response(cart_items)
        
    except Exception as e:
        logger.error(f"장바구니 아이템 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Recent Views API
# ============================================================================

@app.get("/products-recent-views")
async def get_recent_viewed_products(user_id: int = 1, limit: int = 50, supabase: Client = Depends(get_supabase)):
    """
    사용자가 최근에 조회한 상품 조회
    
    Args:
        user_id: 사용자 ID (기본값: 1)
        limit: 조회할 상품 수 (기본값: 50)
        supabase: Supabase 클라이언트
        
    Returns:
        Response: 최근 조회한 상품 목록
    """
    try:
        logger.info(f"최근 조회 상품 조회 - user_id: {user_id}, limit: {limit}")
        
        # quantity가 0인 기록들 (조회 기록)을 최근 순으로 가져오기
        response = supabase.table("cart_items").select("""
            *,
            products:product_id (*)
        """).eq("user_id", user_id).eq("quantity", 0).order("updated_at", desc=True).limit(limit).execute()
        
        # 상품 정보만 추출
        products = []
        for item in response.data:
            if 'products' in item and item['products']:
                product = item['products'].copy()
                formatted_products = format_product_data([product])
                products.append(formatted_products[0])
        
        # 최근 조회 데이터가 없으면 전체 상품에서 일부 반환
        if not products:
            logger.info("최근 조회 데이터 없음 - 전체 상품에서 일부 반환 (테스트용)")
            all_products_response = supabase.table("products").select("*").order("created_at", desc=True).limit(limit).execute()
            products = format_product_data(all_products_response.data)
        
        logger.info(f"최근 조회 상품 조회 성공 - {len(products)}개 상품")
        
        return create_standard_response(products)
        
    except Exception as e:
        logger.error(f"최근 조회 상품 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Search & Filter API
# ============================================================================

@app.get("/popular-search-terms")
async def get_popular_search_terms(limit: int = 10, supabase: Client = Depends(get_supabase)):
    """
    인기 검색어 조회
    
    Args:
        limit: 조회할 검색어 수 (기본값: 10)
        supabase: Supabase 클라이언트
        
    Returns:
        Response: 인기 검색어 목록
    """
    try:
        logger.info(f"인기 검색어 조회 - limit: {limit}")
        
        # 인기 검색어 목록 (임시로 하드코딩)
        popular_terms = [
            {"term": "나이키", "count": 156, "trend": "up"},
            {"term": "아디다스", "count": 134, "trend": "up"},
            {"term": "반팔티", "count": 98, "trend": "down"},
            {"term": "청바지", "count": 87, "trend": "up"},
            {"term": "운동화", "count": 76, "trend": "up"},
            {"term": "후드티", "count": 65, "trend": "down"},
            {"term": "가방", "count": 54, "trend": "up"},
            {"term": "시계", "count": 43, "trend": "up"},
            {"term": "신발", "count": 38, "trend": "down"},
            {"term": "액세서리", "count": 32, "trend": "up"}
        ]
        
        # limit만큼 반환
        result = popular_terms[:limit]
        
        logger.info(f"인기 검색어 조회 성공 - {len(result)}개 검색어")
        
        return create_standard_response(result)
        
    except Exception as e:
        logger.error(f"인기 검색어 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products-search")
async def search_products(q: str, supabase: Client = Depends(get_supabase)):
    """
    상품 검색
    
    Args:
        q: 검색어
        supabase: Supabase 클라이언트
        
    Returns:
        Response: 검색 결과 상품 목록
    """
    try:
        logger.info(f"상품 검색 - 검색어: '{q}'")

        q = (q or "").strip()
        if not q:
            logger.info("빈 검색어 요청 - 빈 목록 반환")
            return create_standard_response([], "검색어가 비어있습니다")
        
        response = supabase.table("products").select("*").or_(
            f"product_name.ilike.%{q}%,brand_name.ilike.%{q}%"
        ).order("created_at", desc=True).execute()
        
        formatted_products = format_product_data(response.data)
        
        logger.info(f"상품 검색 성공 - '{q}'에 대한 {len(formatted_products)}개 결과")
        
        return create_standard_response(formatted_products)
        
    except Exception as e:
        logger.error(f"상품 검색 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Ranking API
# ============================================================================

@app.get("/products-ranking")
async def get_products_ranking(supabase: Client = Depends(get_supabase)):
    """
    인기 상품 랭킹 조회 (좋아요 수 기준)
    Args:
        supabase: Supabase 클라이언트
        
    Returns:
        Response: 랭킹 상품 목록
    """
    try:
        logger.info("상품 랭킹 조회")
        response = supabase.table("products").select("*").order("likes", desc=True).limit(20).execute()
        
        formatted_products = format_product_data(response.data)
        
        logger.info(f"상품 랭킹 조회 성공 - {len(formatted_products)}개 상품")
        
        return create_standard_response(formatted_products)
        
    except Exception as e:
        logger.error(f"상품 랭킹 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    """
    서버 실행
    """
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8001, 
        log_level="info",
        reload=True
    )