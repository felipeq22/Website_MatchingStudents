
class Student:
    def __init__(self, student_id: int, name: str, major: str, year: int):
        """
        Initialize a Student object.

        :param student_id: Student ID
        :param name: Student name
        :param major: Major (MDS, MPP, MIA, or EMPA)
        :param year: Academic year (1st or 2nd year)
        """
        self.student_id = student_id
        self.name = name
        self.major = major
        self.year = year
        self.preferences = []  # List to store preferred courses
        self.assigned_courses = []  # List to store assigned courses

    def __str__(self):
        """
        String representation of the Student object.
        """
        return f"Student({self.student_id}, {self.name}, {self.major}, Year {self.year})"

# Example:
Dominik = Student(232487, "Dominik Allen", "Public Policy", 2)

print(Dominik)

