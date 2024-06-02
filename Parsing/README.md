# Introduction
Some schools utilize the services of Ellucian Company to allow students to do several Registrar-related things, including viewing and searching for courses. The software these schools are using is *probably* called [Ellucian Banner](https://www.ellucian.com/solutions/ellucian-banner), which has several functionalities. The functionality this project is concerned about is the ability to view Course information like name, description, subject, etc.

The purpose of this part of the project was build an API to scrape and parse Course information in a nice and dynamic format. For bonus points, I added support for any school also using the same software for Course search and viewing. This was achieved by sending and parsing HTTP requests using the public API scheme the user uses, which is consistent across all schools using Ellucian Banner. *Please note that this project was tested on 3 different schools.*


The complete project has two parts:
1. [Parsing](../Parsing/) - The scraping and parsing of the Courses from Ellucian Banner API
2. [Displaying](../Displaying/) - Using DataTables to display results from Parsing

This project is licensed under the MIT license.

## Definitions
- **Calendar**: a term or semester where a set of Courses are offered
- **Course**: a college class offered during a particular Calendar (and its corresponding properties)

# Overview
I used Drew University, Georgia Tech University, and Purdue University as the case studies. Below I speak in the general case where I am applying the knowledge I collected from working with these 3 schools.

Schools utilizing Ellucian Banner might offer a way to view Course information publicly through a page called the "Dynamic Schedule." The Dynamic Schedule allows the user to select a  Calendar. Note that archived Calendars from prior years might also be available for searching.

After selecting a Calendar, the user can perform a "Class Schedule Search" to find Courses based on specific information like subject, instructor, class days, etc. The functionality for filtering is limited, which was an inspiration for the [second](../Displaying/) part of this project.

After a search is made, all the results are displayed as the "Class Schedule Listing" where all the information for every Course is displayed as a big table, except the following pieces of information: description, registration availability (capacity, number of students registered, number of students waitlisted). All of the results lack in aesthetic and functional appeal, which is addressed in the [second](../Displaying/) part of this project.

Each page and corresponding action can be represented through HTTP requests. All requests follow a structured format: they must have a Base Host (i.e., `selfservice.drew.edu`) and Base Path (ie., `/prod`). After appending the Base Host to the Base Path (i.e, `selfservice.drew.edu/prod`), the next appended path will determine the action. Together, this forms a complete URL. Below I list the most important paths, aside from the Base Path.

1. `/bwckschd.p_disp_dyn_sched` A GET request to load the Dynamic Schedule.
2. `bwckgens.p_proc_term_date` A POST request to determine which Calendar to select, which leads to loading the Class Schedule Search.
3. `bwckschd.p_get_crse_unsec` A POST request to search for a subset of Courses, which leads to loading the Class Schedule Listing.
4. `bwckschd.p_disp_detail_sched?...` A GET request to view the "Detailed Information Section" page of a Course, which shows information about registration availability for a particular Course.
5. `bwckctlg.p_display_courses?...` A GET request to view the "Catalog Entry" page of a Course, which shows information about the description of a particular Course.

For the most part, information displayed at each page is consistent and allows the ability to (somewhat) reliably scrape the necessary information. In the next section, I break down the key data structures of this part of the project.

**Note**: For each Course, there are 2 additional requests (Detailed Information Section, Catalog Entry) made to scrape additional information. Additionally, the number of requests to load all the Courses for any Calendar can vary. If $n$ is the number of subjects for a Calendar and `Chunk Load` is set to true in [profiles.json](#profilesjson), then the maximum number of requests is $3 + ceil(n / 5)$. Otherwise, it is $3$. Chunk Loading should be set to true for schools that typically offer a lot (5000+) Courses for a typical Calendar.

## Structure of Data
Every Calendar has a set of Courses, and each Course has properties. Calendars and Courses are fundamentally objects and below, I break down the properties of each object.

### Calendar
A Calendar has the following properties:
```
Calendar ID - Numeric ID
Calendar Name - Name of term or semester
Processing Time - How long it took (in seconds) to scrape and parse information for all Courses
Courses - A set of Course objects
```
I found these properties to be self-evident and the most important for a Calendar.

### Course
Describing the properties of a Course object forced me to make some design choices, like choosing the names of the properties. In some cases, I didn't follow the exact names used in the Class Schedule Listings, Detailed Information Section, or Catalog Entry pages. Additionally, some information from these pages is not captured as properties of a Course. Below are all the properties of a Course:
```
CRN - Course Registration Number
Section - Course section (001, 002, etc.)
Subject - Course subject (Mathematics, Physics, etc.)
Abbreviation - Subject abbreviation (MATH, PHYS, etc.)
Level - Couse level (100, 200, etc.)
Name - Course name
Description - Course description
Credits - Course credit-count (3, 1 TO 4, etc.)
Prerequisites - A set of prereqs for the Course, if any
Corequisites - A set of coreqs for the Course, if any
Mutual Exclusions - A set of mutual exclusions for the Course, if any
Cross List Courses - A set of cross-listed Courses of the Course, if any
Restrictions - A set of restrictions for the Course, if any
Attributes - A set of attributes associated with the Course, if any
Properties - A set of Properties of the Course
```

The Properties object refers to the "Scheduled Meeting Times" of a Course in the Class Schedule Listing. I made the choice of grouping them together as a "Properties" object, which has the following properties:
```
Type - Course type (Class, Internship, etc.)
Time - The time period of Course (9:00 AM - 11:15 AM, 6:00 - 8:00 PM, etc)
Days - A set of days when the Course is scheduled for ([Monday, Wednesday, Friday], [Tuesday, Thursday], etc.)
Location - Location of the Course
Period - Date period when course is being offered
Nature - The nature of Course (Lecture, Lab, etc.)
Instructors - A set of names of the instructors of the Course
```

## File Specifics
Below I will briefly highlight the purpose and functionality of the files in this folder. Since all the functions have documentation, I will not be going into the specifics here.

### [mappings.json](./mappings.json)
Contains a single object, where each key is the full name of the school (i.e., Drew University) and its value is an object. The object contains a set of subject mappings the school has utilized in prior Calendars or is utilizing. The values are the subjects (i.e., Mathematics) and their correspond keys are the abbreviated versions of the subjects (i.e., MATH). This data is used to determine the full subject associated with a Course from the Class Schedule Listing.

**Note**: This file is dynamically updated every time Courses are scraped and fetched using the [Parser](#parserpy) class. We keep a copy for each school as not all schools will use the same mappings.

### [profiles.json](./profiles.json)
Contains an array of objects, where each object is the information about a school using Ellucian Banner. All objects should have the following properties defined:
1. `School`
    Full name of the school. Used as a key in [mappings.json](#mappingsjson), if not present already.
2. `Chunk Load`
    Should be set to true for schools that offer a large (5000+) number of Courses for a typical Calendar. This helps with the overall processing time and ensures proper functionality.
3. `Base Host`
    The Base Host from the URL of the Dynamic Schedule page.
4. `Base Path`
    From the case studies, it will be either `/prod` or `/bprod`, which can be determined from the URL of the Dynamic Schedule.

### [CourseParser.py](./CourseParser.py)
Helper class that is associated with parsing all the individual information of a Course. This is used as an instance in the [Parser.py](#parserpy) class.

### [Parser.py](./Parser.py)
The main class that parses and processes everything. A Parser object has the following fields:
1. `profile`
    A dictionary type, which should be one of the objects from profile.json. This field is required.
2. `get_course_desc`
    Boolean that determines if an additional request for each Course should be made to scrape Course description. Defaults to true.
3. `get_extra_course_info`
    Boolean that determines if an additional request for each Course should be made to scrape Course registration availability. Defaults to true.

### [Tester.py](./Tester.py)
Shows example usage of Parser.py.

# Usage
First, the necessary packages can be installed by the following command:
```
pip install -r requirements.txt
```

Second, make sure the school you are interested is added into [profiles.json](./profiles.json). Again, the school should be using Ellucian Banner to show Course and Calendar information in a way described in the [Overview](#overview).

The following code from [Tester.py](./Tester.py) demonstrates how to use the [Parser.py](#parserpy) class.
```python
from json import loads, dumps
from Parser import Parser

# Load and select first profile.
with open('./profiles.json', 'r', encoding='UTF-8') as f: profiles = loads(f.read())
profile = profiles[0]

# Or, you could manually set a profile to use.
profile = {
    "School": "Drew University",
    "Chunk Load": False,
    "Base Host": "selfservice.drew.edu",
    "Base Path": "/prod"
}

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
```

The output would look something like the following:
```json
[
    {
        "Calendar ID": "202510",
        "Calendar Name": "Fall 2024",
        "Processing Time": 39,
        "Courses": [
            {
                "CRN": "10309",
                "Section": "001",
                "Subject": "Academic English",
                "Abbreviation": "EAP",
                "Level": "010",
                "Name": "Writing & Grammar 1",
                "Description": "An introduction to writing and grammar in the English language.\u00a0 Development of writing skills and grammatical accuracy using a communicative, proficiency-oriented approach. Designed for students at the mid-beginning level.",
                "Credits": "0.000",
                "Capacity": 16,
                "Registered": 0,
                "Remaining": 16,
                "Waitlisted": 0,
                "Prerequisites": null,
                "Corequisites": null,
                "Mutual Exclusions": null,
                "Cross List Courses": [
                    "EAP 020",
                    "EAP 030",
                    "EAP 040"
                ],
                "Restrictions": [
                    {
                        "Description": "Must be enrolled in one of the following Programs:",
                        "Requirements": [
                            "INTO Academic English",
                            "INTO Pathway Program"
                        ]
                    },
                    {
                        "Description": "Must be enrolled in one of the following Levels:",
                        "Requirements": [
                            "Undergraduate"
                        ]
                    }
                ],
                "Attributes": [],
                "Properties": [
                    {
                        "Type": "Classroom, In Person",
                        "Time": "1:30 PM - 3:45 PM",
                        "Days": [
                            "Tuesday",
                            "Thursday"
                        ],
                        "Location": "Tilghman House 206",
                        "Period": "Aug 26, 2024 - Dec 13, 2024",
                        "Nature": "Class",
                        "Instructors": [
                            "Stefanie Rose Shapiro"
                        ]
                    }
                ]
            },
            ...
            {
                "CRN": "10734",
                "Section": "001",
                "Subject": "Writing",
                "Abbreviation": "WRTG",
                "Level": "120",
                "Name": "Academic Writing",
                "Description": "Intended for students who have not fulfilled their first-year writing requirement through the Drew Seminar, and for those who have but want to continue to strengthen their writing skills. Engages in an intensive study of scholarly communication, including the construction and organization of arguments and the ethical and effective use of sources. Allows students to read and write in varying genres. Aids students in developing a metacognitive awareness of their own writing practices and how they intersect with the expectations of an academic readership through regular reflective writing.",
                "Credits": "4.000",
                "Capacity": 10,
                "Registered": 4,
                "Remaining": 6,
                "Waitlisted": 0,
                "Prerequisites": null,
                "Corequisites": null,
                "Mutual Exclusions": null,
                "Cross List Courses": null,
                "Restrictions": null,
                "Attributes": [],
                "Properties": [
                    {
                        "Type": "Classroom, In Person",
                        "Time": "11:50 AM - 1:05 PM",
                        "Days": [
                            "Tuesday",
                            "Thursday"
                        ],
                        "Location": "TBA",
                        "Period": "Aug 26, 2024 - Dec 13, 2024",
                        "Nature": "Seminar",
                        "Instructors": [
                            "Stefanie Rose Shapiro"
                        ]
                    }
                ]
            }
        ]
    }
]
```

# Notes
## Similar Project
This part of the project is similar to the following [project](https://github.com/alec-rabold/UnofficialEllucianBannerApi) by alec-rabold, which seems out-of-date. Though I do not provide code for creating a REST API, it can be very easily done. The main purpose of the code in this folder is to provide a thorough output that can be utilized to intuitively display the results in the [second](../Displaying/) part of the project.

##  Asynchronous Functionality and Progress Bars
Because of the number of paths to visit to get Course description and registration availability information can be large, using async functionality dramatically decreases the processing time. However, this feature is not perfect and I have attempted to mitigate errors as best as I could. One thing to note is that connection errors do happen (a request to a Course description or registration availability is simply was not able to me made). I incorporated the use of progress bars to help illustrate the progress of the program when it is processing a Calendar with a large number of Courses.
