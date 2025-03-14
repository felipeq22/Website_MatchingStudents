class StudentCourseMatchingAlgorithm:
   """
   Main algorithm class for matching students to course sections.
   Implements the course allocation algorithm with all constraints and special case handling.
   """

   def __init__(self):
       # Initialize data structures
       self.students = {}              # Dict mapping student_id to Student object
       self.courses = {}               # Dict mapping course_id to Course object
       self.sections = {}              # Dict mapping section_id to Section object
       self.section_by_course = {}     # Dict mapping course_id to list of section_ids
       self.programs = {}              # Dict mapping program_id to Program object
       self.student_preferences = {}   # Dict mapping student_id to StudentPreference object
       self.completed_courses = {}     # Dict mapping student_id to list of CompletedCourse objects
       self.max_credits_per_semester = 18  # Default value, can be overridden
       
       # Output data structures
       self.enrollments = {}           # Dict mapping student_id to list of Enrollment objects
       self.alternative_suggestions = {} # Dict mapping student_id to list of AlternativeSuggestion objects
       self.unresolved_issues = {}     # Dict mapping student_id to list of issue descriptions
   
   def load_data(self, students, courses, sections, programs, student_preferences, completed_courses):
       """
       Load all necessary data into the algorithm.
       
       Args:
           students: List of Student objects
           courses: List of Course objects
           sections: List of Section objects
           programs: List of Program objects
           student_preferences: List of StudentPreference objects
           completed_courses: List of CompletedCourse objects
       """
       # Load students
       for student in students:
           self.students[student.id] = student
           self.enrollments[student.id] = []
           self.alternative_suggestions[student.id] = []
           self.unresolved_issues[student.id] = []
       
       # Load courses
       for course in courses:
           self.courses[course.id] = course
           self.section_by_course[course.id] = []
       
       # Load sections and organize by course
       for section in sections:
           self.sections[section.id] = section
           if section.course_id in self.section_by_course:
               self.section_by_course[section.course_id].append(section.id)
       
       # Load programs
       for program in programs:
           self.programs[program.id] = program
       
       # Load student preferences
       for pref in student_preferences:
           self.student_preferences[pref.student_id] = pref
       
       # Load completed courses and organize by student
       self.completed_courses = {}
       for completed in completed_courses:
           if completed.student_id not in self.completed_courses:
               self.completed_courses[completed.student_id] = []
           self.completed_courses[completed.student_id].append(completed)
   
   def run_matching(self):
       """
       Run the matching algorithm and return the generated enrollments.
       
       Returns:
           tuple: (enrollments, alternative_suggestions, unresolved_issues)
       """
       # 1. Student Prioritization - Sort students based on academic year and other factors
       prioritized_students = self._prioritize_students()
       
       # 2. For each student in priority order
       for student in prioritized_students:
           # Get mandatory courses for the student's program
           mandatory_courses = self._get_mandatory_courses(student.program)
           
           # Get student's course preferences
           student_prefs = self.student_preferences.get(student.id, None)
           preferred_courses = student_prefs.course_preferences if student_prefs else {}
           
           # Combine and prioritize courses to consider
           courses_to_consider = self._combine_course_lists(student.id, mandatory_courses, preferred_courses)
           
           # Track student's total credit enrollment for this semester
           current_credits = 0
           
           # 3. For each course in prioritized order
           for course_id, is_mandatory in courses_to_consider:
               # Skip if max credits would be exceeded
               course = self.courses.get(course_id)
               if not course:
                   continue
               
               if current_credits + course.credits > self.max_credits_per_semester:
                   if is_mandatory:
                       self.unresolved_issues[student.id].append(
                           f"Mandatory course {course_id} would exceed credit limit"
                       )
                   continue
               
               # Check if student has completed prerequisites
               if not self._has_prerequisites(student.id, course_id):
                   if is_mandatory:
                       self.unresolved_issues[student.id].append(
                           f"Missing prerequisites for mandatory course {course_id}"
                       )
                   continue
               
               # Find best section for this course
               best_section = self._find_best_section(student.id, course_id)
               
               if best_section:
                   # Enroll student in this section
                   self._enroll_student(student, best_section, course)
                   current_credits += course.credits
               elif is_mandatory:
                   # If mandatory course couldn't be assigned, record issue
                   self.unresolved_issues[student.id].append(
                       f"Could not assign mandatory course {course_id}"
                   )
               else:
                   # Try to find alternative course
                   self._suggest_alternative(student.id, course_id)
       
       # 4. Handle special cases
       self._handle_exchange_requests()
       self._handle_unresolved_issues()
       
       return (self.enrollments, self.alternative_suggestions, self.unresolved_issues)
   
   def _prioritize_students(self):
       """
       Prioritize students for course allocation.
       Currently prioritizes by academic year (higher years first).
       
       Returns:
           list: Prioritized list of Student objects
       """
       # Convert dict to list
       student_list = list(self.students.values())
       
       # Sort by academic year (higher years get priority)
       student_list.sort(key=lambda s: s.academic_year, reverse=True)
       
       return student_list
   
   def _get_mandatory_courses(self, program_id):
       """
       Get mandatory courses for a specific program.
       
       Args:
           program_id: ID of the program
           
       Returns:
           list: List of mandatory course IDs
       """
       mandatory_courses = []
       
       program = self.programs.get(program_id)
       if not program:
           return mandatory_courses
       
       # Look through all requirement categories
       for category, requirements in program.requirements.items():
           for course_id, details in requirements.items():
               if details.get('mandatory', False):
                   mandatory_courses.append(course_id)
       
       return mandatory_courses
   
   def _combine_course_lists(self, student_id, mandatory_courses, preferred_courses):
       """
       Combine mandatory courses and student preferences with proper prioritization.
       
       Args:
           student_id: ID of the student
           mandatory_courses: List of mandatory course IDs
           preferred_courses: Dict mapping course_id to priority
           
       Returns:
           list: List of tuples (course_id, is_mandatory) in priority order
       """
       result = []
       
       # Add mandatory courses first (with highest priority)
       for course_id in mandatory_courses:
           result.append((course_id, True))
       
       # Add preferred courses that aren't already in the list
       mandatory_set = set(mandatory_courses)
       for course_id, priority in sorted(preferred_courses.items(), key=lambda x: x[1]):
           if course_id not in mandatory_set:
               result.append((course_id, False))
       
       return result
   
   def _has_prerequisites(self, student_id, course_id):
       """
       Check if student has completed all prerequisites for a course.
       
       Args:
           student_id: ID of the student
           course_id: ID of the course to check
           
       Returns:
           bool: True if all prerequisites are satisfied, False otherwise
       """
       course = self.courses.get(course_id)
       if not course or not course.prerequisites:
           return True  # No prerequisites to check
       
       # Get list of completed course IDs for this student
       completed = self.completed_courses.get(student_id, [])
       completed_ids = {c.course_id for c in completed}
       
       # Check if all prerequisites are in the completed set
       for prereq_id in course.prerequisites:
           if prereq_id not in completed_ids:
               return False
       
       return True
   
   def _find_best_section(self, student_id, course_id):
       """
       Find the best available section for a course that meets all constraints.
       
       Args:
           student_id: ID of the student
           course_id: ID of the course
           
       Returns:
           Section: Best matching section or None if no suitable section is found
       """
       # Get all sections for this course
       section_ids = self.section_by_course.get(course_id, [])
       if not section_ids:
           return None
       
       # Get student's timing preferences
       timing_prefs = None
       if student_id in self.student_preferences:
           timing_prefs = self.student_preferences[student_id].timing_preferences
       
       candidate_sections = []
       
       # Check each section for constraints
       for section_id in section_ids:
           section = self.sections.get(section_id)
           
           # Skip if section is at capacity
           if section.current_enrollment >= section.capacity:
               continue
           
           # Skip if section has time conflicts with already enrolled sections
           if self._has_time_conflict(student_id, section):
               continue
           
           # If we get here, section is a valid candidate
           # Now score it based on timing preferences
           score = self._score_section_timing(section, timing_prefs)
           candidate_sections.append((section, score))
       
       # Sort candidates by score (higher is better)
       candidate_sections.sort(key=lambda x: x[1], reverse=True)
       
       # Return the highest-scoring section, or None if no candidates
       return candidate_sections[0][0] if candidate_sections else None
   
   def _has_time_conflict(self, student_id, new_section):
       """
       Check if a section conflicts with the student's existing enrollments.
       
       Args:
           student_id: ID of the student
           new_section: Section object to check
           
       Returns:
           bool: True if there's a conflict, False otherwise
       """
       # Get student's current enrollments
       current_enrollments = self.enrollments.get(student_id, [])
       
       # For each enrollment, check for time conflicts
       for enrollment in current_enrollments:
           enrolled_section = self.sections.get(enrollment.section_id)
           if not enrolled_section:
               continue
           
           # Check each time slot for conflicts
           for new_slot in new_section.time_slots:
               for existing_slot in enrolled_section.time_slots:
                   # If same day and times overlap, there's a conflict
                   if new_slot.day == existing_slot.day:
                       # Check for time overlap
                       if (new_slot.start_time < existing_slot.end_time and 
                           existing_slot.start_time < new_slot.end_time):
                           return True
       
       return False
   
   def _score_section_timing(self, section, timing_prefs):
       """
       Score how well a section matches student's timing preferences.
       
       Args:
           section: Section to evaluate
           timing_prefs: Dictionary of timing preferences
           
       Returns:
           float: Score (higher is better)
       """
       if not timing_prefs:
           return 0  # Neutral score if no preferences
       
       score = 0
       preferred_days = timing_prefs.get('days', [])
       preferred_times = timing_prefs.get('times', [])  # List of (start, end) tuples
       
       for slot in section.time_slots:
           # Boost score for preferred days
           if slot.day in preferred_days:
               score += 1
           
           # Boost score for preferred time ranges
           for pref_start, pref_end in preferred_times:
               # If time slot falls completely within preferred range
               if pref_start <= slot.start_time and slot.end_time <= pref_end:
                   score += 2
               # If time slot overlaps with preferred range
               elif pref_start < slot.end_time and slot.start_time < pref_end:
                   score += 1
       
       return score
   
   def _enroll_student(self, student, section, course):
       """
       Enroll a student in a section.
       
       Args:
           student: Student object
           section: Section object
           course: Course object
       """
       # Format timing info as string
       timing_info = self._format_timing_info(section)
       
       # Create enrollment record
       enrollment = Enrollment(
           student_id=student.id,
           student_name=student.name,
           section_id=section.id,
           course_id=course.id,
           course_name=course.name,
           timing_info=timing_info
       )
       
       # Add to enrollments list for this student
       self.enrollments[student.id].append(enrollment)
       
       # Update section enrollment count
       section.current_enrollment += 1
   
   def _format_timing_info(self, section):
       """
       Format time slots as a readable string.
       
       Args:
           section: Section object
           
       Returns:
           str: Formatted timing information
       """
       if not section.time_slots:
           return "No timing information"
       
       # Convert minutes to hours:minutes format
       def format_time(minutes):
           hours = minutes // 60
           mins = minutes % 60
           am_pm = "AM" if hours < 12 else "PM"
           if hours > 12:
               hours -= 12
           if hours == 0:
               hours = 12
           return f"{hours}:{mins:02d} {am_pm}"
       
       # Group time slots by day
       day_slots = {}
       for slot in section.time_slots:
           if slot.day not in day_slots:
               day_slots[slot.day] = []
           day_slots[slot.day].append(f"{format_time(slot.start_time)} - {format_time(slot.end_time)}")
       
       # Format result
       result = []
       for day, times in day_slots.items():
           result.append(f"{day}: {', '.join(times)}")
       
       return "; ".join(result)
   
   def _suggest_alternative(self, student_id, course_id):
       """
       Suggest an alternative course when the preferred course couldn't be assigned.
       
       Args:
           student_id: ID of the student
           course_id: ID of the original course
       """
       original_course = self.courses.get(course_id)
       if not original_course:
           return
       
       # Find similar courses based on department and prerequisites
       similar_courses = []
       for c_id, course in self.courses.items():
           if c_id == course_id:
               continue  # Skip the original course
           
           # Check if in same department
           if course.department == original_course.department:
               # Check if student has prerequisites for this course
               if self._has_prerequisites(student_id, c_id):
                   # Check if any sections available
                   for section_id in self.section_by_course.get(c_id, []):
                       section = self.sections.get(section_id)
                       if section and section.current_enrollment < section.capacity:
                           if not self._has_time_conflict(student_id, section):
                               similar_courses.append((c_id, course))
                               break
       
       # If we found alternatives, suggest the first one
       if similar_courses:
           alt_id, alt_course = similar_courses[0]
           suggestion = AlternativeSuggestion(
               student_id=student_id,
               original_course_id=course_id,
               suggested_course_id=alt_id,
               reason=f"Similar course in {alt_course.department} department"
           )
           self.alternative_suggestions[student_id].append(suggestion)
   
   def _handle_exchange_requests(self):
       """
       Process student exchange requests.
       This is a placeholder for the exchange request handling logic.
       In a real implementation, would take a list of exchange requests as input.
       """
       # Placeholder for exchange request processing
       # Would typically involve swapping enrollments between students
       # ensuring constraints are still satisfied
       pass
   
   def _handle_unresolved_issues(self):
       """
       Final pass to attempt to resolve any remaining issues.
       """
       # Placeholder for additional issue resolution logic
       # Could involve adjusting capacity limits, suggesting
       # alternative semesters, etc.
       pass
   
   def get_results(self):
       """
       Get the final results of the matching algorithm.
       
       Returns:
           tuple: (enrollments, alternative_suggestions, unresolved_issues)
       """
       return (self.enrollments, self.alternative_suggestions, self.unresolved_issues)