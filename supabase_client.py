from supabase import create_client, Client
from config import settings

def get_supabase_client() -> Client:
    """슈퍼베이스 클라이언트를 생성하고 반환합니다."""
    supabase: Client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY
    )
    return supabase
