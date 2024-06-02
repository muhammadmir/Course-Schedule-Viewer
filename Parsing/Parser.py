from CourseParser import CourseParser
from bs4 import BeautifulSoup
from httpx import Client, AsyncClient, Response
from urllib.parse import urlencode
from re import findall
from time import time
from json import dumps, loads
from math import ceil
from tqdm.asyncio import tqdm
import asyncio
import logging

LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    filename = 'Logs.log',
    encoding = 'UTF-8',
    format = '=' * 150 + '\n[%(asctime)s | File: %(filename)s | Fn: %(funcName)s | Line: %(lineno)s]\nLevel: %(levelname)s\n%(message)s\n' + '=' * 150 + '\n\n',
    datefmt = '%Y-%m-%dT%H:%M:%SZ',
    level = logging.INFO
)

# Silence other loggers | https://stackoverflow.com/a/71193599
for module in ['httpx']: logging.getLogger(module).setLevel(logging.WARNING)

class Parser:
    def __init__(self, profile: dict, get_course_desc: bool = True, get_extra_course_info: bool = True) -> None:
        """Intialize a Parser object.

        Args:
            profile (dict): Profile of school.
            get_course_desc (bool, optional): Whether or not to send an additional request for each Course to scrape Course description. Defaults to True.
            get_extra_course_info (bool, optional): Whether or not to send an additional request for each Course to scrape Course registration availability. Defaults to True.
        """
        self.profile = profile
        self.get_course_desc = get_course_desc
        self.get_extra_course_info = get_extra_course_info
        
        # Define necessary sessions beforehand, so no need to constantly pass a dict of headers.
        self.session = Client(
            base_url='https://' + self.profile['Base Host'] + self.profile['Base Path'],
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://' + self.profile['Base Host'],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15'
            },
            verify=False,
            timeout=120
        )
   
        self.course_desc = [] # List of strings
        self.extra_course_info = [] # List of dict

        # Load and utilize mappings of the school matching the profile only.
        with open('./mappings.json', 'r', encoding='UTF-8') as f: self.mappings = loads(f.read())        
        self.mappings = {} if self.profile['School'] not in self.mappings else self.mappings[self.profile['School']]

        # Load the mappings for the school into the CourseParser.
        self.course_parser = CourseParser(self.mappings)
    
    def _get_async_session(self):
        """Create a new async session.

        Returns:
            AsyncClient: An initalized client for async requests
        """
        return AsyncClient(
            base_url='https://' + self.profile['Base Host'] + self.profile['Base Path'],
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://' + self.profile['Base Host'],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15'
            },
            verify=False,
            timeout=120
        )
    
    def _split_n_chunks(self, large_list: list, n: int) -> list[list]:
        """An internal function that splits a large list into n different chunks. Generated via ChatGPT.

        Args:
            large_list (list): The large list.
            n (int): The n different chunks.

        Returns:
            list[list]: List of length n, where item is also a list.
        """
        # Calculate the size of each sublist
        avg_size = len(large_list) // n
        remainder = len(large_list) % n
        
        # Create the sublists
        sublists = []
        start = 0
        for i in range(n):
            # Calculate the end index for the current sublist
            end = start + avg_size + (1 if i < remainder else 0)
            # Append the sublist to the result
            sublists.append(large_list[start:end])
            # Update the start index for the next sublist
            start = end
        
        return sublists
    
    def _split_n_per_chunk(self, large_list: list, n: int) -> list[list]:
        """An internal function that split a large list into chunk so that each chunk has n elements.

        Args:
            large_list (list): The large list.
            n (int): The n elements per chunk.

        Returns:
            list[list]: List of lists where each list has length n.
        """
        # Via ChatGPT
        return [large_list[i:i + n] for i in range(0, len(large_list), n)]
    
    def _update_mappings(self, mappings: dict) -> None:
        """An internal function that update mappings.json for the current profile with new subject mappings.

        Args:
            mappings (dict): The new subject mappings.
        """
        update = False
        
        for key, value in mappings.items():
            if key not in self.mappings:
                update = True
                self.mappings[key] = value
                LOGGER.info(f'[{self.profile["School"]}] | New Mapping Added {key} --> {value}')
        
        if update:
            # Sort alphabetically by full subject name.
            self.mappings = dict(sorted(self.mappings.items(), key = lambda x : x[1]))
            
            # Load full mappings, sort alphabetically by school name, and overwrite changes.
            with open('./mappings.json', 'r', encoding='UTF-8') as f: og_mappings = loads(f.read()) 
            og_mappings[self.profile['School']] = self.mappings
            og_mappings = dict(sorted(og_mappings.items(), key = lambda x : x[0]))
            with open('./mappings.json', 'w', encoding='UTF-8') as f: f.write(dumps(og_mappings, indent=4))
    
    def _get_calendar_page(self) -> Response:
        """An internal function that sends a request to load the Dynamic Schedule page.

        Returns:
            Response: Response object that should load the Dynamic Schedule Page.
        """
        try: return self.session.get('/bwckschd.p_disp_dyn_sched')
        except Exception as e: LOGGER.exception(f'Type: {type(e)} | Error: {e}')
    
    def _select_calendar(self, calendar: dict) -> Response:
        """An internal function that selects a particular Calendar from the Dynamic Schedule Page and loads the Class Schedule Search page.

        Args:
            calendar (dict): Calendar object containing Calendar ID. 

        Returns:
            Response: Respone object that should load the Class Schedule Search Page.
        """
        try:
            response = self._get_calendar_page()
            LOGGER.info(f'[{self.profile["School"]}] | Successfully loaded Dynamic Schedule.')
            
            self.session.headers['Referer'] = str(self.session.base_url) + '/bwckschd.p_disp_dyn_sched'
            data = {'p_term': calendar['Calendar ID']}
            
            # Since some schools might have more select options, we dynamically determine payload that is necessary when
            # selecting a Calendar. The payload parameters and data are assumed to be in the input tags (either hidden or
            # text types).
            soup = BeautifulSoup(response.content, features='html.parser')
            inputs = soup.find_all(lambda tag: tag.name == 'input' and (tag['type'] == 'hidden' or tag['type'] == 'text'))
            for x in inputs: data[x['name']] = '' if 'value' not in x.attrs else x['value']
            
            return self.session.post('/bwckgens.p_proc_term_date', data=data)
        except Exception as e: LOGGER.exception(f'Type: {type(e)} | Error: {e}')
    
    def _search_all_courses(self, calendar: dict = None, response: Response = None, abbreviations: list = None) -> Response:
        """An internal function that selects all Courses from the Class Schedule Search page to load the Class Schedule Listing page.

        Args:
            calendar (dict, optional): A Calendar object. If None, then response must be provided.
            response (Response, optional): A Response object from _select_calendar function. If calendar is provided, then this is optional.
            abbreviations (list, optional): List of subjects (by abbreviation) to load Courses for. Used for chunk loading only.

        Raises:
            Exception: When both calendar and response are not provided.

        Returns:
            Response: Response object that should load the Class Schedule Listing page.
        """
        try:
            if calendar: response = self._select_calendar(calendar)
            elif not response: raise Exception
            
            if '>Class Schedule Search<' in response.text:
                # If chunk loading, then we don't need to see this message be spammed.
                if not abbreviations: LOGGER.info(f'[{self.profile["School"]}] | Successfully Class Schedule Search page.')
                
                self.session.headers['Referer'] = str(self.session.base_url) + '/bwckgens.p_proc_term_date'
                data = {}
                
                # Much like how there can be different options when selecting a Calendar, we also dynamically determine the payload
                # for navigating the Course search page of a Calendar. The payload is built in a different order as to what is
                # seen in the original HTTP request.
                soup = BeautifulSoup(response.content, features='html.parser')
                
                # Since subjects have abbreviations (MATH --> Mathematics), we keep track of this across all Calendars for a school.
                subjects = soup.find('select', {'name': 'sel_subj'}).find_all('option')
                mappings = {subject['value']: subject.text for subject in subjects}
                self._update_mappings(mappings) 
                
                # First, we handle all the hidden and text inputs.
                inputs = soup.find_all(lambda tag: tag.name == 'input' and (tag['type'] == 'hidden' or tag['type'] == 'text'))
                for x in inputs: data[x['name']] = '' if 'value' not in x.attrs else x['value']
                
                # Second, we handle all the select inputs. The value "%" for a parameter in this input type indicates select all options
                # available. This option is usually (assumed) the first option for all select input types where applicable (like Instructor,
                # Attribute Type, etc.). We insert "%" for sel_subj to force-select all subjects.
                #
                # Note: For select input types like Start Time and End Time, the first option selected is the default one.
                inputs = soup.find_all('select')
                for x in inputs: data[x['name']] = x.find('option')['value']
                data['sel_subj'] = '%'
                
                # Create payload, and determine if we want to get all subjects or a subset
                modified_data = {key: data[key] for key in data.keys() if key not in {'sel_subj'}} # to avoid double-adding of sel_subj to payload
                payload = urlencode(modified_data) + '&'
                payload += 'sel_subj=%25' if abbreviations is None else '&'.join([f'sel_subj={abbr}' for abbr in abbreviations])
                
                # Note: For some reason, there are a fixed set of "dummy" parameters with defaults values of "dummy" that must be sent in the
                # payload. However, these parameters are subject to modification via selecting different options on the Course search page.
                # Additionally, not all of these parameters may be configurable on the Course search page. As a result, if a parameter is
                # modified, it must be added again to the payload. All the "modified" versions of these "dummy" variables are stored in the
                # variable data. Since it's a dict, we have to take some extra steps to correctly send the entire payload.                            
                dummy_params = ['sel_subj', 'sel_day', 'sel_schd', 'sel_insm', 'sel_camp', 'sel_levl', 'sel_sess', 'sel_instr', 'sel_ptrm', 'sel_attr']
                dummy_postfix = '&'.join([f'{dummy}=dummy' for dummy in dummy_params if data[dummy] != 'dummy']) 
                
                payload = dummy_postfix + '&' + payload
                            
                return self.session.post('/bwckschd.p_get_crse_unsec', data=payload)
        except Exception as e: LOGGER.exception(f'Type: {type(e)} | Error: {e}')
    
    def _chunk_load_all_courses(self, calendar: dict) -> Response:
        """An internal function to load all Courses as a single Response object in chunks.

        Args:
            calendar (dict): A Calendar object.

        Returns:
            Response: A Response object that has all the Courses in the table.
        """
        soup, table = None, None
        response = self._select_calendar(calendar) # To avoid constantly selecting Calendar again in _search_all_courses.
        
        abbreviations = list(self.mappings.keys())
        chunks = self._split_n_chunks(abbreviations, 5)
        for chunk in chunks:
            try:
                resp = self._search_all_courses(None, response, chunk)
                if chunks.index(chunk) == 0:
                    soup = BeautifulSoup(resp.content, features='html.parser')
                    table = soup.find('table', {'class': 'datadisplaytable'})
                else:
                    temp_soup = BeautifulSoup(resp.content, features='html.parser')
                    temp_table = temp_soup.find('table', {'class': 'datadisplaytable'})
                    
                    for new_row in temp_table.find_all('tr'): table.append(new_row)
            except Exception as e: LOGGER.exception(f'Type: {type(e)} | Error: {e}')
            LOGGER.info(f'[{self.profile["School"]}] | Finished Course Chunk Loading {chunks.index(chunk)}/{len(chunks)}.')
            
        return Response(200, html=str(soup))
             
    def get_calendars(self, all_calendars: bool = False) -> list[dict]:
        try:
            response = self._get_calendar_page()
            if any([key in response.text for key in ['>Dynamic Schedule<', '>Select Term or Date Range<']]):
                calendars = []
                
                soup = BeautifulSoup(response.content, features='html.parser')
                terms = soup.find('select', {'name': 'p_term'})                
                for term in terms.find_all('option'):
                    if term['value'] is None or len(term['value']) == 0: continue
                    calendars.append(
                        {
                            'Calendar ID': term['value'],
                            'Calendar Name': term.text.replace(' (View only)', ''),
                            'Processing Time': 0,
                            'Courses': []
                        }
                    )
                    
                return [calendars[0]] if not all_calendars else calendars
        except Exception as e: LOGGER.exception(f'Type: {type(e)} | Error: {e}')
    
    def get_courses(self, calendars: list[dict]) -> list[dict]:
        """Parse all Courses for a list of Calendars.

        Args:
            calendars (list[dict]): A list of Calendar objects.

        Returns:
            list[dict]: A list contanining all the Calendars and their corresponding Courses.
        """
        for calendar in calendars:
            start_time = time()
            logger_prefix = f'[{self.profile["School"]}] | Calendar: {calendar["Calendar Name"]}'
            
            try:
                response = self._chunk_load_all_courses(calendar) if self.profile['Chunk Load'] else self._search_all_courses(calendar)
                if '>Class Schedule Listing<' in response.text:
                    LOGGER.info(f'{logger_prefix} | Successfully Loaded All Courses.')
                    soup = BeautifulSoup(response.content, features='html.parser')
                    
                    table = soup.find('table', {'class': 'datadisplaytable'})
                    rows = table.find_all('tr')
                                        
                    # Parse all Course information like Title, Subject, etc.
                    courses = self.course_parser.parse_courses(rows)
                    LOGGER.info(f'{logger_prefix} | Successfully Parsed All Course Information.')
                    
                    # If descriptions and extra info are being parsed, then visit all their saved path's and append info.
                    if self.get_course_desc or self.get_extra_course_info:
                        LOGGER.info(f'{logger_prefix} | Total Paths Count: {2 * len(self.course_parser.desc_paths)}')
                        asyncio.run(self._visit_paths(logger_prefix))
                        LOGGER.info(f'{logger_prefix} | Successfully Parsed Course Descriptions and Registration Availability.')
                    
                        for course, desc, extra_info in zip(courses, self.course_desc, self.extra_course_info): # Unpacking
                            course['Description'] = desc

                            course['Capacity'] = extra_info['Capacity']
                            course['Registered'] = extra_info['Registered']
                            course['Remaining'] = extra_info['Remaining']
                            course['Waitlisted'] = extra_info['Waitlisted']
                            
                            extra = extra_info['Extra']
                            course['Prerequisites'] = extra['Prerequisites']
                            course['Corequisites'] = extra['Corequisites']
                            course['Mutual Exclusions'] = extra['Mutual Exclusions']
                            course['Cross List Courses'] = extra['Cross List Courses']
                            course['Restrictions'] = extra['Restrictions']
                            
                    calendar['Processing Time'] = round(time() - start_time)
                    calendar['Courses'] = courses
                    self.course_parser.reset_paths()
                    
                    LOGGER.info(f'{logger_prefix} | Finished in {calendar["Processing Time"]} seconds.')
            except Exception as e: LOGGER.exception(f'Type: {type(e)} | Error: {e}')
        #with open('table.json', 'w', encoding='UTF-8') as f: f.write(dumps(calendars, indent=4))
        return calendars
            
    async def _visit_paths(self, logger_prefix: str) -> None:
        """An internal async function that visits all the Course description and registration availability paths.
        """   
        # Main Problem: Too many coroutines/futures to evaluate (at once) and timeouts occur as a result.
        # Solution: Evaluate in chunks. Using Semaphores was not that helpful.
        
        # Get new async session everytime (as session closes after this function)
        async with self._get_async_session() as async_session:
            # If evaluating all paths at once, setting a timeout (as function of number of paths) will help avoid timeout errors
            if self.profile['Chunk Load']: async_session.timeout = ceil(60 * (len(self.course_parser.desc_paths) / 20))
            
            try:
                # Course Descriptions
                if not self.profile['Chunk Load']:                    
                    tasks = [self._get_desc(async_session, path) for path in self.course_parser.desc_paths]
                    self.course_desc = await tqdm.gather(*tasks, desc=f'{logger_prefix}| Course Descriptions')
                else:
                    chunks = self._split_n_per_chunk(self.course_parser.desc_paths, 2000)
                    for chunk in chunks:
                        tasks = [self._get_desc(async_session, path) for path in chunk]
                        self.course_desc += await tqdm.gather(*tasks, desc=f'{logger_prefix} | Course Descriptions (Chunk {chunks.index(chunk) + 1})')
                LOGGER.info(f'{logger_prefix} | Finished Scraping Course Description.')

                # Extra Course Infos
                if not self.profile['Chunk Load']:
                    tasks = [self._get_extra_course_info(async_session, path) for path in self.course_parser.extra_course_info_paths]
                    self.extra_course_info = await tqdm.gather(*tasks, desc=f'{logger_prefix} | Registration Availability')
                else:
                    chunks = self._split_n_per_chunk(self.course_parser.extra_course_info_paths, 2000)
                    for chunk in chunks:
                        tasks = [self._get_extra_course_info(async_session, path) for path in chunk]
                        self.extra_course_info += await tqdm.gather(*tasks, desc=f'{logger_prefix} | Registration Availability (Chunk {chunks.index(chunk) + 1})')
                LOGGER.info(f'{logger_prefix} | Finished Scraping Registration Availability.')
            except Exception as e: LOGGER.exception(f'Type: {type(e)} | Error: {e}')
    
    async def _get_desc(self, async_session: AsyncClient, path: str) -> str:
        """An internal async function to get description of a Course.

        Args:
            async_session (AsyncClient): Async session.
            path (str): Path to Catalog Entry page of a Course.

        Returns:
            str: Course description.
        """
        try:
            async_session.headers['Referer'] = str(async_session.base_url) + '/bwckschd.p_get_crse_unsec'
            a = await async_session.get(path)
            if '>Catalog Entries<' in a.text:
                soup = BeautifulSoup(a.content, features='html.parser')
                selection = soup.find('td', {'class': 'ntdefault'})
                    
                return findall(r'(?<=class="ntdefault"\>)(.*?)(?=\<)', str(selection).replace('\n', ''))[0].strip()
        except Exception as e: LOGGER.exception(f'Type: {type(e)} | Error: {e}')
        return ''
    
    async def _get_extra_course_info(self, async_session: AsyncClient, path: str) -> dict: 
        """An internal async function to get registration availability of a Course.

        Args:
            async_session (AsyncClient): Async session.
            path (str): Path to Detailed Information Section page of a Course.

        Returns:
            dict: Registration availbility information of a Course.
        """
        try:
            async_session.headers['Referer'] = str(async_session.base_url) + '/bwckschd.p_get_crse_unsec'
            a = await async_session.get(path)
            if '>Detailed Class Information<' in a.text:
                soup = BeautifulSoup(a.content, features='html.parser')
                    
                table = soup.find('table', {'class': 'datadisplaytable', 'summary': 'This layout table is used to present the seating numbers.'})
                rows = table.find_all('tr')
                    
                seats = rows[1].find_all('td')
                capacity, registered, remaining = int(seats[0].text), int(seats[1].text), int(seats[2].text)
                waitlisted = int(rows[2].find_all('td')[1].text)
                    
                # Though we could account for cross-list seats, I will not
                extra = self.course_parser.parse_extra_course_info(a.text)
                                
                return {'Capacity': capacity, 'Registered': registered, 'Remaining': remaining, 'Waitlisted': waitlisted, 'Extra': extra}             
        except Exception as e: LOGGER.exception(f'Type: {type(e)} | Error: {e}')
        
        extra = {'Prerequisites': None, 'Corequisites': None, 'Mutual Exclusions': None, 'Cross List Courses': None, 'Restrictions': None}
        return {'Capacity': 0, 'Registered': 0, 'Remaining': 0, 'Waitlisted': 0, 'Extra': extra}
