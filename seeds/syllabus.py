import json

# Load the files
with open('chapters.json', 'r') as chapters_file, open('syllabus.json', 'r') as syllabus_file:
    chapters_data = json.load(chapters_file)
    syllabus_data = json.load(syllabus_file)

# Create a mapping of classes and subjects from chapters.json
chapter_mapping = {}
for cls in chapters_data['classes']:
    class_number = cls['class']
    for subject_name, subject_data in cls['subjects'].items():
        if subject_name not in chapter_mapping:
            chapter_mapping[(class_number, subject_name)] = subject_data.get('chapters', {})

# Update syllabus.json with chapters
for level in syllabus_data['levels']:
    for cls in level['classes']:
        class_number = int(cls['name'].split()[-1])  # Extract class number
        for subject in cls['subjects']:
            subject_title = subject['title']
            # Check if chapters exist for this class and subject
            chapters = chapter_mapping.get((class_number, subject_title))
            if chapters:
                subject['chapters'] = chapters

# Save the merged JSON
output_path = 'merged_syllabus.json'
with open(output_path, 'w') as output_file:
    json.dump(syllabus_data, output_file, indent=4)

print(f"Merged syllabus with chapters saved to {output_path}")
