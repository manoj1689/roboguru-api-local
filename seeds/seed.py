import json
import requests

# Load the seed JSON file
with open('seed.json', 'r') as seed_file:
    seed_data = json.load(seed_file)

# API base URL and headers

BASE_URL = "http://43.248.241.252:8095"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkaWxzaGFkQG1vYmlyaXplci5jb20iLCJleHAiOjE3Mzg5NjU5NzJ9.jvpHpQjkEcZYzIfRM4fU2QWN4gmEMDz_Lpr2B-iGos8"



# Endpoints
ENDPOINTS = {
    "create_level": "/level/create/",
    "create_class": "/classes/create/",
    "create_subject": "/subjects/create",
    "create_chapter": "/chapters/create",
    "create_topic": "/topics/create",
}

def post_data(endpoint, payload):
    try:
        response = requests.post(BASE_URL + endpoint, json=payload, headers=HEADERS)
        print(f"Request to {BASE_URL + endpoint} with payload: {payload}")
        print(f"Status Code: {response.status_code}")
        
        # Check for unauthorized status
        if response.status_code == 401:
            print("Error: Unauthorized. Check your token or permissions.")
            return {"error": "Unauthorized. Check your token or permissions."}
        
        # Raise an exception for HTTP errors (4xx, 5xx)
        response.raise_for_status()

        # Parse the response data
        response_data = response.json()
        
        # Print the success response and ID
        print(f"Success: {response_data}")
        
        # Access the ID from the response data
        if 'data' in response_data and 'id' in response_data['data']:
            # print("Response ID:", response_data['data']['id'])
            return response_data['data']['id']  # Return only the ID for further use
        else:
            print("ID not found in response data")
            return None
    
    except requests.exceptions.RequestException as e:
        # Catch all request exceptions and return error data
        print(f"Error: {e}")
        return {"error": str(e)}
    except ValueError as ve:
        # Handle JSON decoding errors
        print(f"JSON Decoding Error: {ve}")
        return {"error": "Failed to decode JSON response"}

# Insert the seed data into the database
for level in seed_data.get("levels", []):
    level_payload = {"name": level["name"]}
    level_response = post_data(ENDPOINTS["create_level"], level_payload)
    print("Level response:", level_response)
    
  
    
   
    # Iterate over classes within the level
    for cls in level.get("classes", []):
        class_payload = {
            "name": cls["name"],
            "tagline": cls.get("tagline", ""),
            "image_link": cls.get("image_prompt", ""),
            "level_id": level_response  # Pass the created level ID
        }
        class_response = post_data(ENDPOINTS["create_class"], class_payload)
        
        if class_response:
            class_id = class_response
        else:
            print("Skipping class creation due to missing class ID.")
            continue

        # Iterate over subjects within the class
        for subject in cls.get("subjects", []):
            subject_payload = {
                "name": subject["title"],
                "tagline": subject.get("tagline", ""),
                "image_link": subject.get("image_link", ""),
                "image_prompt": subject.get("image_prompt", ""),
                "class_id": class_id  # Pass the created class ID
            }
            subject_response = post_data(ENDPOINTS["create_subject"], subject_payload)
            
            if subject_response:
                subject_id = subject_response
            else:
                print("Skipping subject creation due to missing subject ID.")
                continue

            # Iterate over chapters within the subject
            for chapter in subject.get("chapters", []):
                chapter_payload = {
                    "name": chapter["title"],
                    "tagline": chapter.get("tagline", ""),
                    "image_link": chapter.get("image_prompt", ""),
                    "subject_id": subject_id  # Pass the created subject ID
                }
                chapter_response = post_data(ENDPOINTS["create_chapter"], chapter_payload)
                
                if chapter_response:
                    chapter_id = chapter_response
                else:
                    print("Skipping chapter creation due to missing chapter ID.")
                    continue

                # Iterate over topics within the chapter
                for topic in chapter.get("topics", []):
                    topic_payload = {
                        "name": topic["title"],
                        "tagline": chapter.get("tagline", ""),
                        "details": topic.get("details", ""),
                        "image_link": topic.get("image_prompt", ""),
                        "subtopics":topic.get("subtopics",[]),
                        "chapter_id": chapter_id  # Pass the created chapter ID
                    }
                    post_data(ENDPOINTS["create_topic"], topic_payload)

print("Data insertion completed.")
