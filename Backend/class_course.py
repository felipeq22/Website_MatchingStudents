class Course:
    def __init__(self, course_id, name, program_id, program_name, credits, capacity, time_slots, faculty, prerequisites=None):
        # Basic validation
        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("Capacity must be a positive integer")
            
        self.course_id = course_id # Unique identifier for the course
        self.name = name  # Course name
        self.program_id = program_id # ID of the program the course belongs to
        self.program_name = program_name # Name of the program
        self.credits = credits # Number of credits assigned to the course
        self.capacity = capacity # Maximum number of students allowed
        self.time_slots = time_slots # Available time slots for the course
        self.faculty = faculty # Instructor(s) teaching the course  
        self.prerequisites = prerequisites if prerequisites else [] # List of prerequisite course IDs
        self.enrolled_students = [] # List of enrolled student objects or IDs
    
    # Core capacity management - course class only manages the capacity of the course 
    def has_space(self):
        """Check if the course has space for more students."""
        return len(self.enrolled_students) < self.capacity
        
    def add_student(self, student):
        """Simply adds a student if space is available"""
        if self.has_space():
            self.enrolled_students.append(student)
            return True
        return False
        
    def remove_student(self, student):
        if student in self.enrolled_students:
            self.enrolled_students.remove(student)
            return True
        return False
    
    
    def get_prerequisites(self):
        """returns the list of prerequisite course IDs that are required before a student can take this course"""
        return self.prerequisites
        
    def get_schedule(self):
        """returns the time slots when the course is scheduled to meet"""
        return self.time_slots
        
    def get_capacity_info(self):
        """ creating and returning a dictionary containing capacity, enrolled, available"""
        return {
            "capacity": self.capacity,
            "enrolled": len(self.enrolled_students),
            "available": self.capacity - len(self.enrolled_students)
        }
        
    def __repr__(self):
        """formatted string containing -course ID, course name, enrollment status as a fraction (current number of students / maximum capacity)"""
        return f"Course({self.course_id}, {self.name}, Enrolled: {len(self.enrolled_students)}/{self.capacity})"