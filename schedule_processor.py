"""
Schedule processor for class schedule finder.
Parses Excel file and generates valid schedule combinations.
"""
import pandas as pd
import re
from itertools import product
from typing import List, Dict, Tuple, Set


class ScheduleProcessor:
    """Process class schedules and find valid combinations."""
    
    def __init__(self, excel_file: str):
        """Initialize with Excel file path."""
        self.excel_file = excel_file
        self.df = None
        self.courses = {}
        self.load_data()
    
    def load_data(self):
        """Load and parse Excel data."""
        self.df = pd.read_excel(self.excel_file)
        # Clean the dataframe - remove empty rows
        self.df = self.df.dropna(subset=['Asignatura'])
        self._organize_courses()
    
    def _organize_courses(self):
        """Organize courses by code and sections."""
        for _, row in self.df.iterrows():
            course_code = row['Asignatura']
            section = row['Sección']
            
            if course_code not in self.courses:
                self.courses[course_code] = {
                    'name': row['Nombre Asig.'],
                    'credits': row['Créditos Asignatura'],
                    'sections': {}
                }
            
            if section not in self.courses[course_code]['sections']:
                self.courses[course_code]['sections'][section] = {
                    'events': [],
                    'package': row['Paquete'],
                    'vacancies': row['Vac. Paquete']
                }
            
            # Add event to section
            event = {
                'type': row['Descrip. Evento'],
                'schedule': row['Horario'],
                'professor': row['Profesor'] if pd.notna(row['Profesor']) else '',
                'campus': row['Sede']
            }
            self.courses[course_code]['sections'][section]['events'].append(event)
    
    def get_courses_list(self) -> List[Dict]:
        """Get list of all courses."""
        courses_list = []
        for code, info in self.courses.items():
            courses_list.append({
                'code': code,
                'name': info['name'],
                'credits': info['credits'],
                'sections_count': len(info['sections'])
            })
        return sorted(courses_list, key=lambda x: x['code'])
    
    def get_course_sections(self, course_code: str) -> List[Dict]:
        """Get all sections for a specific course."""
        if course_code not in self.courses:
            return []
        
        sections = []
        for section_name, section_info in self.courses[course_code]['sections'].items():
            sections.append({
                'section': section_name,
                'events': section_info['events'],
                'package': section_info['package'],
                'vacancies': section_info['vacancies']
            })
        return sections
    
    def get_all_professors(self) -> List[str]:
        """Get list of all unique professors sorted alphabetically."""
        professors = set()
        for course_info in self.courses.values():
            for section_info in course_info['sections'].values():
                for event in section_info['events']:
                    professor = event.get('professor', '').strip()
                    if professor:
                        professors.add(professor)
        return sorted(list(professors))
    
    def parse_schedule(self, schedule_str: str) -> List[Tuple[str, int, int]]:
        """
        Parse schedule string into list of (day, start_minutes, end_minutes).
        Example: "MA JU 10:00 - 11:20" -> [('MA', 600, 680), ('JU', 600, 680)]
        """
        if pd.isna(schedule_str) or not schedule_str:
            return []
        
        # Day abbreviations
        days_map = {
            'LU': 'Lunes',
            'MA': 'Martes', 
            'MI': 'Miércoles',
            'JU': 'Jueves',
            'VI': 'Viernes',
            'SA': 'Sábado'
        }
        
        # Extract days and time
        parts = schedule_str.split()
        days = []
        time_str = None
        
        for i, part in enumerate(parts):
            if part in days_map:
                days.append(part)
            elif ':' in part and i > 0 and parts[i-1] not in ['-']:
                # This is the start time
                time_idx = i
                break
        
        # Extract time range
        time_pattern = r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})'
        time_match = re.search(time_pattern, schedule_str)
        
        if not time_match or not days:
            return []
        
        start_time = time_match.group(1)
        end_time = time_match.group(2)
        
        # Convert to minutes from midnight
        def time_to_minutes(time_str):
            hours, minutes = map(int, time_str.split(':'))
            return hours * 60 + minutes
        
        start_minutes = time_to_minutes(start_time)
        end_minutes = time_to_minutes(end_time)
        
        # Create schedule entries for each day
        schedule_entries = []
        for day in days:
            schedule_entries.append((day, start_minutes, end_minutes))
        
        return schedule_entries
    
    def is_optional_event(self, event_type: str) -> bool:
        """Check if an event is an optional ayudantía."""
        return 'OPCIONAL' in event_type.upper() if event_type else False
    
    def extract_campus_location(self, campus: str) -> str:
        """Extract the main location from campus string."""
        if not campus or pd.isna(campus):
            return 'UNKNOWN'
        # Extract location (e.g., "S-SANTIAGO" -> "SANTIAGO", "H-HUECHURABA" -> "HUECHURABA")
        campus_upper = str(campus).upper()
        if 'SANTIAGO' in campus_upper:
            return 'SANTIAGO'
        elif 'HUECHURABA' in campus_upper:
            return 'HUECHURABA'
        else:
            return campus_upper
    
    def check_conflict(self, event1: Dict, schedule1: List[Tuple], 
                       event2: Dict, schedule2: List[Tuple]) -> bool:
        """
        Check if two events have conflicts considering:
        - Optional ayudantías can overlap
        - Different campuses need 50 min separation
        """
        # Optional ayudantías can overlap with anything
        if self.is_optional_event(event1.get('type', '')) or \
           self.is_optional_event(event2.get('type', '')):
            return False
        
        # Check time overlaps
        for day1, start1, end1 in schedule1:
            for day2, start2, end2 in schedule2:
                if day1 == day2:
                    # Check for time overlap
                    if not (end1 <= start2 or end2 <= start1):
                        return True
                    
                    # Check campus separation (50 minutes minimum)
                    campus1 = self.extract_campus_location(event1.get('campus', ''))
                    campus2 = self.extract_campus_location(event2.get('campus', ''))
                    
                    if campus1 != campus2 and campus1 != 'UNKNOWN' and campus2 != 'UNKNOWN':
                        # Calculate time between classes
                        time_gap = min(abs(start2 - end1), abs(start1 - end2))
                        if time_gap < 50:  # Less than 50 minutes
                            return True
        return False
    
    def calculate_schedule_score(self, schedule_data: Dict, optimization: str = 'morning') -> float:
        """
        Calculate a score for a schedule based on optimization preference.
        
        Args:
            schedule_data: Schedule combination
            optimization: 'morning', 'afternoon', or 'gaps'
        
        Returns:
            Score (lower is better for ranking)
        """
        if optimization == 'morning':
            # For morning preference, calculate average start time (lower is better)
            total_start = 0
            count = 0
            for course_code, course_info in schedule_data.items():
                for event in course_info['events']:
                    if not self.is_optional_event(event['type']):
                        for _, start, _ in event['parsed_schedule']:
                            total_start += start
                            count += 1
            return total_start / count if count > 0 else float('inf')
        
        elif optimization == 'afternoon':
            # For afternoon preference, calculate average start time (higher is better, so negate)
            total_start = 0
            count = 0
            for course_code, course_info in schedule_data.items():
                for event in course_info['events']:
                    if not self.is_optional_event(event['type']):
                        for _, start, _ in event['parsed_schedule']:
                            total_start += start
                            count += 1
            return -total_start / count if count > 0 else float('inf')
        
        elif optimization == 'gaps':
            # Calculate total gap time per day (sum of empty times between classes)
            day_schedules = {}  # day -> [(start, end), ...]
            
            for course_code, course_info in schedule_data.items():
                for event in course_info['events']:
                    if not self.is_optional_event(event['type']):
                        for day, start, end in event['parsed_schedule']:
                            if day not in day_schedules:
                                day_schedules[day] = []
                            day_schedules[day].append((start, end))
            
            total_gap = 0
            for day, times in day_schedules.items():
                if len(times) > 1:
                    # Sort by start time
                    times.sort()
                    # Calculate span from first class to last class
                    day_start = times[0][0]
                    day_end = times[-1][1]
                    day_span = day_end - day_start
                    
                    # Calculate actual class time
                    class_time = sum(end - start for start, end in times)
                    
                    # Gap is the difference
                    gap = day_span - class_time
                    total_gap += gap
            
            return total_gap
        
        return 0
    
    def generate_schedules(self, selected_courses: List[str], max_results: int = 100, 
                          optimization: str = None, exclude_professors: str = None) -> List[Dict]:
        """
        Generate valid schedule combinations for selected courses.
        
        Args:
            selected_courses: List of course codes
            max_results: Maximum number of results to return
            optimization: 'morning', 'afternoon', 'gaps', or None for unordered
            exclude_professors: Comma-separated string of professor names to exclude
        
        Returns:
            List of valid schedule combinations
        """
        if not selected_courses:
            return []
        
        # Parse excluded professors
        excluded_profs = set()
        if exclude_professors:
            excluded_profs = {name.strip().lower() for name in exclude_professors.split(',')}
        
        # Get all sections for each selected course
        course_sections = {}
        for course_code in selected_courses:
            if course_code in self.courses:
                sections = self.get_course_sections(course_code)
                
                # Filter out sections with excluded professors
                if excluded_profs:
                    filtered_sections = []
                    for section in sections:
                        has_excluded_prof = False
                        for event in section['events']:
                            prof = event.get('professor', '')
                            if prof and prof.lower().strip() in excluded_profs:
                                has_excluded_prof = True
                                break
                        if not has_excluded_prof:
                            filtered_sections.append(section)
                    course_sections[course_code] = filtered_sections
                else:
                    course_sections[course_code] = sections
        
        # Generate all possible combinations
        section_combinations = []
        for course_code in selected_courses:
            if course_code in course_sections:
                section_combinations.append([(course_code, section) for section in course_sections[course_code]])
        
        # Get all combinations
        all_combinations = list(product(*section_combinations))
        
        valid_schedules = []
        
        for combination in all_combinations:
            # Check for conflicts
            all_events = []
            schedule_data = {}
            
            has_conflict = False
            
            for course_code, section_info in combination:
                section_events = []
                for event in section_info['events']:
                    parsed_schedule = self.parse_schedule(event['schedule'])
                    
                    event_dict = {
                        'type': event['type'],
                        'schedule': event['schedule'],
                        'professor': event['professor'],
                        'campus': event['campus']
                    }
                    
                    # Check conflicts with existing events
                    for existing_event, existing_schedule in all_events:
                        if self.check_conflict(event_dict, parsed_schedule, 
                                             existing_event, existing_schedule):
                            has_conflict = True
                            break
                    
                    if has_conflict:
                        break
                    
                    section_events.append({
                        'type': event['type'],
                        'schedule': event['schedule'],
                        'parsed_schedule': parsed_schedule,
                        'professor': event['professor'],
                        'campus': event['campus']
                    })
                    all_events.append((event_dict, parsed_schedule))
                
                if has_conflict:
                    break
                
                schedule_data[course_code] = {
                    'name': self.courses[course_code]['name'],
                    'section': section_info['section'],
                    'events': section_events,
                    'package': section_info['package']
                }
            
            if not has_conflict:
                valid_schedules.append(schedule_data)
        
        # Apply optimization if specified
        if optimization and valid_schedules:
            # Calculate scores and sort
            schedules_with_scores = [
                (schedule, self.calculate_schedule_score(schedule, optimization))
                for schedule in valid_schedules
            ]
            schedules_with_scores.sort(key=lambda x: x[1])
            valid_schedules = [schedule for schedule, _ in schedules_with_scores]
        
        # Return up to max_results
        return valid_schedules[:max_results]
