import requests

# Base URL of your API
base_url = "http://127.0.0.1:8000"

# Function to send OTP
def send_otp(mobile_number):
    url = f"{base_url}/signin"
    params = {"mobile_number": mobile_number}
    response = requests.post(url, params=params)
    if response.status_code == 200:
        print("OTP sent successfully")
    else:
        print("Failed to send OTP")
        print(response.json())

# Function to verify OTP and get access token
def verify_otp(mobile_number, otp):
    url = f"{base_url}/verify_otp"
    params = {"mobile_number": mobile_number, "otp": otp}
    response = requests.post(url, params=params)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print("Failed to verify OTP")
        print(response.json())

# Function to create an entity (e.g., level, class, subject, etc.)
def create_entity(url, data, headers):
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        print(f"Successfully created {data['name']}")
    else:
        print(f"Failed to create {data['name']}, Reason: {response.content}")

# Function to create level
def create_level(level_data, token):
    url = f"{base_url}/level/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, json=level_data, headers=headers)
    if response.status_code == 200:
        print(f"Successfully created level: {level_data['name']}")
    else:
        print(f"Failed to create level: {level_data['name']}, Reason: {response.content}")

# Function to create class
def create_class(class_data, token):
    url = f"{base_url}/classes/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, json=class_data, headers=headers)
    if response.status_code == 200:
        print(f"Successfully created class: {class_data['name']}")
    else:
        print(f"Failed to create class: {class_data['name']}, Reason: {response.content}")

# Function to create subject
def create_subject(subject_data, token):
    url = f"{base_url}/subjects/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, json=subject_data, headers=headers)
    if response.status_code == 200:
        print(f"Successfully created subject: {subject_data['name']}")
    else:
        print(f"Failed to create subject: {subject_data['name']}, Reason: {response.content}")

# Function to create chapter
def create_chapter(chapter_data, token):
    url = f"{base_url}/chapters/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, json=chapter_data, headers=headers)
    if response.status_code == 200:
        print(f"Successfully created chapter: {chapter_data['name']}")
    else:
        print(f"Failed to create chapter: {chapter_data['name']}, Reason: {response.content}")

# Function to create topic
def create_topic(topic_data, token):
    url = f"{base_url}/topics/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, json=topic_data, headers=headers)
    if response.status_code == 200:
        print(f"Successfully created topic: {topic_data['name']}")
    else:
        print(f"Failed to create topic: {topic_data['name']}, Reason: {response.content}")

# Generate seed data
def generate_seed_data():
    levels = [{"name": f"Level {i}", "description": f"Description for level {i}"} for i in range(1, 21)]
    classes = [{"name": f"Class {i}", "tagline": f"Tagline for class {i}", "level_id": (i % 3) + 1, "image_link": f"http://example.com/class{i}.jpg"} for i in range(1, 21)]
    subjects = [{"name": f"Subject {i}", "tagline": f"Tagline for subject {i}", "class_id": (i % 3) + 1, "image_link": f"http://example.com/subject{i}.jpg"} for i in range(1, 21)]
    chapters = [{"name": f"Chapter {i}", "tagline": f"Tagline for chapter {i}", "subject_id": (i % 3) + 1, "image_link": f"http://example.com/chapter{i}.jpg"} for i in range(1, 21)]
    topics = [{"name": f"Topic {i}", "details": f"Details for topic {i}", "chapter_id": (i % 3) + 1, "tagline": f"Tagline for topic {i}", "image_link": f"http://example.com/topic{i}.jpg"} for i in range(1, 21)]
    return levels, classes, subjects, chapters, topics

# Main script
def main():
    mobile_number = "9708188606"
    otp = "1234"

    # Step 1: Send OTP
    send_otp(mobile_number)

    # Step 2: Verify OTP and get access token
    token = verify_otp(mobile_number, otp)
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Generate seed data
    levels, classes, subjects, chapters, topics = generate_seed_data()

    # Create entities using the generated data
    for level_data in levels:
        create_level(level_data, token)
    for class_data in classes:
        create_class(class_data, token)
    for subject_data in subjects:
        create_subject(subject_data, token)
    for chapter_data in chapters:
        create_chapter(chapter_data, token)
    for topic_data in topics:
        create_topic(topic_data, token)

if __name__ == "__main__":
    main()
