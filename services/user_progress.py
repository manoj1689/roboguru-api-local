from models import UserTopicProgress

def calculate_chapter_progress(chapter, user_id, db):
    topics = db.query(UserTopicProgress).filter(
        UserTopicProgress.topic_id.in_([topic.id for topic in chapter.topics]),
        UserTopicProgress.user_id == user_id
    ).all()

    completed_topics = sum(1 for topic in topics if topic.is_completed)
    total_topics = len(chapter.topics)

    if total_topics == 0:
        return 0.0

    return (completed_topics / total_topics) * 100

def calculate_subject_progress(subject, user_id, db):
    total_chapters = len(subject.chapters)
    if total_chapters == 0:
        return 0.0

    chapter_progress_sum = sum(calculate_chapter_progress(chapter, user_id, db) for chapter in subject.chapters)
    return chapter_progress_sum / total_chapters







# # Helper Functions
# def calculate_chapter_progress(chapter, user_id, db):
#     topics = db.query(UserTopicProgress).filter(
#         UserTopicProgress.topic_id.in_([topic.id for topic in chapter.topics]),
#         UserTopicProgress.user_id == user_id
#     ).all()

#     completed_topics = sum(1 for topic in topics if topic.is_completed)
#     total_topics = len(chapter.topics)

#     if total_topics == 0:
#         return 0.0

#     return (completed_topics / total_topics) * 100

# def calculate_subject_progress(subject, user_id, db):
#     total_chapters = len(subject.chapters)
#     if total_chapters == 0:
#         return 0.0

#     chapter_progress_sum = sum(calculate_chapter_progress(chapter, user_id, db) for chapter in subject.chapters)
#     return chapter_progress_sum / total_chapters








# Helper Functions
# def calculate_chapter_progress(chapter, user_id, db):
#     topics = db.query(UserTopicProgress).filter(
#         UserTopicProgress.topic_id.in_([topic.id for topic in chapter.topics]),
#         UserTopicProgress.user_id == user_id
#     ).all()

#     completed_topics = sum(1 for topic in topics if topic.is_completed)
#     total_topics = len(chapter.topics)

#     if total_topics == 0:
#         return 0.0

#     return (completed_topics / total_topics) * 100

# def calculate_subject_progress(subject, user_id, db):
#     total_chapters = len(subject.chapters)
#     if total_chapters == 0:
#         return 0.0

#     chapter_progress_sum = sum(calculate_chapter_progress(chapter, user_id, db) for chapter in subject.chapters)
#     return chapter_progress_sum / total_chapters