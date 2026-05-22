from typing import Any

from fastapi import APIRouter

from app.core.database import supabase

router = APIRouter()


@router.get("/supabase")
def test_supabase() -> list[Any]:
    response = supabase.table("organizaciones").select("*").execute()

    return list(response.data)
