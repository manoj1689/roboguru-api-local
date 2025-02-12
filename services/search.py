from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from models import Chapter, Topic
from services.classes import create_response

# Function to perform conditional fuzzy search or exact match
def fuzzy_search_with_trgm(db: Session, query: str, limit: int = 10):
    try:
        combined_results = []

        if len(query) == 3:
            # Trigram similarity for 3-letter queries
            chapter_results = db.query(Chapter.id, Chapter.name).filter(
                func.similarity(Chapter.name, query) > 0.3
            ).limit(limit).all()

            topic_results = db.query(Topic.id, Topic.name).filter(
                func.similarity(Topic.name, query) > 0.3
            ).limit(limit).all()
        else:
            # Exact match for 4 or more letters
            chapter_results = db.query(Chapter.id, Chapter.name).filter(
                Chapter.name.ilike(f"%{query}%")
            ).limit(limit).all()

            topic_results = db.query(Topic.id, Topic.name).filter(
                Topic.name.ilike(f"%{query}%")
            ).limit(limit).all()

        # Add chapter results
        for chapter in chapter_results:
            combined_results.append({
                "id": chapter.id,
                "name": chapter.name,
                "type": "chapter"
            })

        # Add topic results
        for topic in topic_results:
            combined_results.append({
                "id": topic.id,
                "name": topic.name,
                "type": "topic"
            })

        # If no results found
        if not combined_results:
            return create_response(success=False, message="No results found for the search query.", data=[])

        # Limit the combined results to the requested limit (overall limit)
        combined_results = combined_results[:limit]

        return create_response(success=True, message="Results retrieved successfully.", data=combined_results)

    except Exception as e:
        raise Exception(f"An unexpected error occurred: {str(e)}")