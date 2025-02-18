from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from models.chapter import Chapter
from models.topic import Topic
from utils.response import create_response

def fuzzy_search_with_trgm(db: Session, query: str, limit: int = 10):
    try:
        combined_results = []

        if len(query) == 3:
            chapter_results = db.query(Chapter.id, Chapter.name).filter(
                func.similarity(Chapter.name, query) > 0.3
            ).limit(limit).all()

            topic_results = db.query(Topic.id, Topic.name).filter(
                func.similarity(Topic.name, query) > 0.3
            ).limit(limit).all()
        else:
            chapter_results = db.query(Chapter.id, Chapter.name).filter(
                Chapter.name.ilike(f"%{query}%")
            ).limit(limit).all()

            topic_results = db.query(Topic.id, Topic.name).filter(
                Topic.name.ilike(f"%{query}%")
            ).limit(limit).all()

        for chapter in chapter_results:
            combined_results.append({
                "id": chapter.id,
                "name": chapter.name,
                "type": "chapter"
            })

        for topic in topic_results:
            combined_results.append({
                "id": topic.id,
                "name": topic.name,
                "type": "topic"
            })

        if not combined_results:
            return create_response(success=False, message="No results found for the search query.", data=[])

        combined_results = combined_results[:limit]

        return create_response(success=True, message="Results retrieved successfully.", data=combined_results)

    except HTTPException as e:
        raise e
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {str(e)}")