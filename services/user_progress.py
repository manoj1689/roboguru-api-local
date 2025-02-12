from models import UserTopicProgress

def calculate_chapter_progress(chapter, user_id, db):
    all_topics = chapter.topics 
    total_topics = len(all_topics)

    if total_topics == 0:
        return 0.0  

    completed_topics = db.query(UserTopicProgress).filter(
        UserTopicProgress.user_id == user_id,
        UserTopicProgress.topic_id.in_([topic.id for topic in all_topics]),
        UserTopicProgress.is_completed == True  
    ).count()

    return (completed_topics / total_topics) * 100  

def calculate_subject_progress(subject, user_id, db):
    all_chapters = [chapter for chapter in subject.chapters if len(chapter.topics) > 0]  
    total_chapters = len(all_chapters)

    if total_chapters == 0:
        return 0.0  

    chapter_progress_sum = sum(calculate_chapter_progress(chapter, user_id, db) for chapter in all_chapters)
    return chapter_progress_sum / total_chapters
