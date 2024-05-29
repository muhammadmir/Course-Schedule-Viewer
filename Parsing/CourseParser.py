from re import findall, sub
import logging

REQUIRED_FIELDS = ['Prerequisites:', 'Corequisites:', 'Mutual Exclusions:', 'Mutual Exclusion:', 'Cross List Courses:', 'Restrictions:']
UNNECESSARY_FIELDS = ['Search', 'Associated Term:', 'Capacity', 'Actual', 'Remaining', 'Seats', 'Waitlist Seats', 'Cross List Seats']

LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    filename = 'Logs.log',
    encoding = 'UTF-8',
    format = '=' * 150 + '\n[%(asctime)s | File: %(filename)s | Fn: %(funcName)s | Line: %(lineno)s]\nLevel: %(levelname)s\n%(message)s\n' + '=' * 150 + '\n\n',
    datefmt = '%Y-%m-%dT%H:%M:%SZ',
    level = logging.INFO
)

# Silence other loggers | https://stackoverflow.com/a/71193599
for module in ['httpx']:
    logging.getLogger(module).setLevel(logging.WARNING)

class CourseParser:
    def __init__(self, mappings: dict) -> None:
        """Initialize a CourseParser Object

        Args:
            mappings (dict): Associated subject mappings of a particular school.
        """
        self.extra_course_info_paths = []
        self.desc_paths = []
        self.mappings = mappings
    
    def reset_paths(self) -> None:
        """Reset all the saved paths of a CourseParser object, for the next Calendar iteration.
        """
        self.extra_course_info_paths = []
        self.desc_paths = []
        
    def _format_time(self, t: str) -> str:
        """An internal function to correctly format time of a Course.

        Args:
            t (str): The time of the Course.

        Returns:
            str: Formatted time of the Course.
        """
        # Unicode annoyance
        try: t = t.upper().replace(' - ', ' - ')
        except Exception as e: t = 'TBA'
        
        return t

    def _format_days(self, days: str) -> list[str]:
        """An internal function to format the notation of what days a Course is held on into a list of full day names.

        Args:
            days (str): Shorthand notation of days.

        Returns:
            list[str]: List of full day names when Course is held on.
        """
        final_days = []
    
        if len(days.strip()) < 1: days = 'TBA' # If class meeting days are not set
        
        for day in days:
            if day == 'M': day = 'Monday'
            elif day == 'T': day = 'Tuesday'
            elif day == 'W': day = 'Wednesday'
            elif day == 'R': day = 'Thursday'
            elif day == 'F': day = 'Friday'
            elif day == 'S': day = 'Saturday'
            final_days.append(day)

        return final_days

    def _format_instructors(self, instructors: str) -> list[str]:
        """An internal function that formats the instructors to a list of instructors by name.

        Args:
            instructors (str): Instructors string.

        Returns:
            list[str]: List of instructor names.
        """
        try: final_instructors = ' '.join(instructors.strip().replace(' (P)', '').split()).split(', ')
        except Exception as e: final_instructors = ['TBA']
        
        return final_instructors
        
    def parse_courses(self, rows: list) -> list[dict]:
        """Extract all Courses from the rows of the HTML table as Course objects.

        Args:
            rows (list): List of Soup tags corresponding to the rows of the HTML table.

        Returns:
            list[dict]: List of Course objects.
        """
        rows = iter(rows)
        
        courses = []
        course = {}

        while True:
            try:
                row = next(rows)
                if row.find('th') and row.find('th')['class'][0] in ['ddtitle', 'ddlabel']:
                    item = row.text.strip().split(' - ')
                    while len(item) != 4: # Instance when Course Name has ' - '
                        item[0] = item[0] + ' - ' + item[1]
                        del item[1]
                                                
                    course = {
                        'CRN': item[1],
                        'Section': item[3],
                        'Subject': self.mappings[item[2].split(' ')[0]],
                        'Abbreviation': item[2].split(' ')[0],
                        'Level': item[2].split(' ')[1],
                        'Name': item[0],
                        'Description': None,
                        'Credits': None,
                        'Capacity': None,
                        'Registered': None,
                        'Remaining': None,
                        'Waitlisted': None,
                        'Prerequisites': None,
                        'Corequisites': None,
                        'Mutual Exclusions': None,
                        'Cross List Courses': None,
                        'Restrictions': None,
                        'Attributes': [],
                        'Properties': []
                    }

                    # Path is typically "/prod/bwckctlg.p_display_courses?..." and hence splitting
                    # by "prod" will get correct path, as "prod" is in the Base Path already
                    # Note: Also works for "bprod"
                    extra_info_path = row.find('a')['href'].split('prod')[-1]
                    self.extra_course_info_paths.append(extra_info_path)
                    
                    # Get Course-specific information (description, attributes, meeting times)
                    row = next(rows)
                    
                    # See two comments above
                    desc_path = row.find('a')['href'].split('prod')[-1]
                    self.desc_paths.append(desc_path)
                    
                    course['Credits'] = findall(r'\d\.\d\d\d.*(?= )', row.text)[0].replace(' TO        ', ' - ')                    
                    course['Attributes'] = findall(r'(?<=Attributes\: )(.*?)(?= \n)', row.text)[0].split(', ') if 'Attributes' in row.text else []

                    # All the "Scheduled Meeting Times"
                    rendezvous = row.find_all('tr')
                    
                    if len(rendezvous) != 0: # Handle if no meeting times have been created yet.
                        del rendezvous[0] # Contains column headers
                        
                        for rende in rendezvous:
                            sub_rows = rende.find_all('td')
                            if len(sub_rows) < 6: continue
                            
                            course['Properties'].append({ # Courses can have multiple meeting locations/times
                                'Type': sub_rows[0].text,
                                'Time': self._format_time(sub_rows[1].text),
                                'Days': self._format_days(sub_rows[2].text),
                                'Location': sub_rows[3].text,
                                'Period': sub_rows[4].text,
                                'Nature': sub_rows[5].text,
                                'Instructors': self._format_instructors(sub_rows[6].text)
                            })
                    else: # Handling required for DataTables orthogonal data                        
                        course['Properties'].append({
                            'Type': 'TBA',
                            'Time': 'TBA',
                            'Days': 'TBA',
                            'Location': 'TBA',
                            'Period': 'TBA',
                            'Nature': 'TBA',
                            'Instructors': 'TBA'
                        })
                            
                    courses.append(course)
            except StopIteration: break
            except Exception as e: LOGGER.exception(f'{type(e)} | {e}\nRow: {row}\nCourse: {course}')
        return courses
    
    def parse_extra_course_info(self, source: str) -> dict:
        """Parse the registration availability information of a Course.

        Args:
            source (str): HTML as text from the Detailed Information Section page of a Course.

        Returns:
            dict: Information about registration avaiblity of the Course.
        """
        source = sub(r'<a href="([^"]*)">(.*?)</a>', r'\2', source).replace('\n', '').replace('&nbsp;', '')
        
        # Get all the fields on the page. Remove all the unncessary ones.
        fields = [field.strip() for field in findall(r'(?<=class\="fieldlabeltext"\>)(.*?)(?=\<\/SPAN)', source)] # Remove trailing spaces
        fields = list(set(fields) - set(UNNECESSARY_FIELDS))
        
        stuff = {'Prerequisites': None, 'Corequisites': None, 'Mutual Exclusions': None, 'Cross List Courses': None, 'Restrictions': None}
                
        for field in fields:
            if field not in REQUIRED_FIELDS: LOGGER.debug(f'New Field: {field}')
            else:
                sub_parse = findall(r'(?<=' + field + r')(.*?)(?=\<SPAN|\<\/TD)', source)[0]
                
                # Removes the empty lines
                items = [
                    stripped_item for item in findall(r'(?<=<br />)(.*?)(?=<br />)', sub_parse)
                    if (stripped_item := item.strip()) and stripped_item != '<br />'
                ]
                #items = [item.strip() for item in findall(r'(?<=<br />)(.*?)(?=<br />)', sub_parse) if len(item.strip()) > 0 and item.strip() != '<br />']
                  
                #with open(f'temp/{field}.txt', 'a') as f: f.write(str(items) + '\n') 
                
                if field in ['Corequisites:',  'Cross List Courses:']: stuff[field.strip(':')] = items
                elif field in ['Mutual Exclusions:', 'Mutual Exclusion:']:
                    del item[0] # Firste entry should just be description
                    stuff[field.strip(':')] = items
                elif field in ['Prerequisites:']:
                    items = [
                        item.replace('  ', ' ').replace('( ', '(').replace('Undergraduate level', '').replace('  ', ' ').replace('( ', '(').strip()
                        for item in items
                    ]
                    stuff['Prerequisites'] = items
                elif field in ['Restrictions:']:
                    new_items = []
                    for item in items:
                        if 'following' in item:
                            if 'req' in locals(): new_items.append(req) # Initial
                            req = {'Description': item, 'Requirements': []}
                        else: req['Requirements'].append(item)
                    
                    new_items.append(req)
                    stuff['Restrictions'] = new_items
        return stuff    