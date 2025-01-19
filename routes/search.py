from fastapi import Depends, APIRouter, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services.search import fuzzy_search_with_trgm
from services.classes import create_response
from services.auth import get_current_user  


router = APIRouter()


@router.get("/search/")
def search(
    query: str, 
    limit: int = 10, 
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),    
):
    try:
        # Get search results from the search service
        result = fuzzy_search_with_trgm(db, query, limit)
        return result

    except HTTPException as e:
        return create_response(success=False, message=e.detail)

    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")






















# FastAPI search endpoint
# @router.get("/search/")
# def search(query: str, db: Session = Depends(get_db)):
#     result = fuzzy_search_chapters_and_topics(db, query)
#     return result

# @router.get("/search/")
# def search(query: str, limit: int = 10, db: Session = Depends(get_db)):
#     results = fuzzy_search_with_trgm(db, query, limit)
#     if not results:
#         return {"success": False, "message": "No results found",}
#     return {"success": True, "message": "Results retrieved successfully", "data": results}

# @router.get("/search", response_model=None)
# def search_chapters_and_topics_endpoint(
#     query: str = Query(..., description="Search query"),
#     limit: int = Query(10, description="Number of results to retrieve"),
#     db: Session = Depends(get_db), 
# ):
#     try:
#         search_results = search_chapters_and_topics(db, query, limit)
#         if not search_results:
#             return create_response(success=True, message="No results found",)
        
#         return create_response(success=True, message="Results retrieved successfully", data=search_results)
    
#     except Exception as e:
#         return create_response(success=False, message=f"An unexpected error occurred: {e}",)
