
import json
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load the seed JSON file
with open("seed.json", "r") as seed_file:
    seed_data = json.load(seed_file)

# API base URL and headers
BASE_URL = "http://127.0.0.1:8000"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5NzA4MTg4NjA0Iiwicm9sZSI6Im5vcm1hbCIsImV4cCI6MTczNjA3MjI0MX0.VFi2xMDrKU58r95UxYYaDo2JpCDiy9IZxquik3ovGFU",  # Replace with a secure token source
}

# Endpoints
ENDPOINTS = {
    "create_level": "/level/create/",
    "create_class": "/classes/create/",
    "create_subject": "/subjects/create/",
    "create_chapter": "/chapters/create/",
    "create_topic": "/topics/create/",
}

# Function to send data to the API
def post_data(endpoint, payload):
    try:
        response = requests.post(BASE_URL + endpoint, json=payload, headers=HEADERS)
        logging.info(f"Request to {BASE_URL + endpoint} with payload: {payload}")
        logging.info(f"Status Code: {response.status_code}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error while posting to {endpoint}: {e}")
        return None

# Insert the seed data into the database
for level in seed_data.get("levels", []):
    level_payload = {"name": level["name"]}
    level_response = post_data(ENDPOINTS["create_level"], level_payload)
    level_id = level_response.get("id") if level_response else None
    if not level_id:
        logging.error("Failed to create level: %s", level["name"])
        continue

    for cls in level.get("classes", []):
        class_payload = {"name": cls["name"], "level_id": level_id}
        class_response = post_data(ENDPOINTS["create_class"], class_payload)
        class_id = class_response.get("id") if class_response else None
        if not class_id:
            logging.error("Failed to create class: %s", cls["name"])
            continue

        for subject in cls.get("subjects", []):
            subject_payload = {
                "title": subject["title"],
                "tagline": subject.get("tagline", ""),
                "image_link": subject.get("image_prompt", ""),
                "class_id": class_id,
            }
            subject_response = post_data(ENDPOINTS["create_subject"], subject_payload)
            subject_id = subject_response.get("id") if subject_response else None
            if not subject_id:
                logging.error("Failed to create subject: %s", subject["title"])
                continue

            for chapter in subject.get("chapters", []):
                chapter_payload = {
                    "title": chapter["title"],
                    "tagline": chapter.get("tagline", ""),
                    "subject_id": subject_id,
                }
                chapter_response = post_data(ENDPOINTS["create_chapter"], chapter_payload)
                chapter_id = chapter_response.get("id") if chapter_response else None
                if not chapter_id:
                    logging.error("Failed to create chapter: %s", chapter["title"])
                    continue

                for topic in chapter.get("topics", []):
                    topic_payload = {
                        "title": topic["title"],
                        "description": topic.get("description", ""),
                        "chapter_id": chapter_id,
                    }
                    topic_response = post_data(ENDPOINTS["create_topic"], topic_payload)
                    if not topic_response:
                        logging.error("Failed to create topic: %s", topic["title"])

logging.info("Data insertion completed.")
