from fastapi import Depends, APIRouter, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services.search import fuzzy_search_with_trgm
from utils.response import create_response
from utils.auth import get_current_user  


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


# from fastapi import Depends, APIRouter, Query, HTTPException
# from sqlalchemy.orm import Session
# from database import get_db
# from services.search import fuzzy_search_with_trgm
# from services.classes import create_response
# from services.auth import get_current_user  

# router = APIRouter()

# @router.get("/search/")
# def search(
#     query: str, 
#     limit: int = 10, 
#     db: Session = Depends(get_db),
#     current_user: str = Depends(get_current_user),    
# ):
#     try:
#         result = fuzzy_search_with_trgm(db, query, limit)
#         return result

#     except HTTPException as e:
#         return create_response(success=False, message=e.detail)

#     except Exception as e:
#         return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")