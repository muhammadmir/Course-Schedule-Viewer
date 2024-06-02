from json import loads, dumps
from Parser import Parser

# Load and select first profile.
with open('./profiles.json', 'r', encoding='UTF-8') as f: profiles = loads(f.read())
profile = profiles[2]

# Initialize Parser object.
parser = Parser(profile)

# Get list of Calendar objects.
calendars = parser.get_calendars(all_calendars=True)

# Select Calendar(s) that match a specific name.
calendars = [calendar for calendar in calendars if calendar['Calendar Name'] == 'Fall 2024']

# Get Courses.
courses = parser.get_courses(calendars) # Expects a list of Calendar objects.

# Output as JSON.
with open('./Output.json', 'w', encoding='UTF-8') as f: f.write(dumps(courses, indent=4))