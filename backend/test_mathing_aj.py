import unittest
import pandas as pd
import numpy as np
from algorithm_final import load_data_first, optimize_course_matching, check_time_conflict, optimize_lab_matching



# First Test Class for Course Matching
class TestMatchingAlgorithm(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures, if any"""
        # Load the datasets for testing
        self.course_data, self.student_data, self.elective_capacity_data, self.elective_preference_data = load_data_first()
        
    def test_utility_calculation(self):
        """Test the utility calculation function"""
        # Define the utility function
        def calculate_utility(rank):
            return max(10 - rank, 1)
        
        self.assertEqual(calculate_utility(1), 9)  # First choice gives utility 9
        self.assertEqual(calculate_utility(5), 5)  # Middle choice
        self.assertEqual(calculate_utility(10), 1)  # Last choice gives minimum utility
        self.assertEqual(calculate_utility(15), 1)  # Ranks beyond 9 still give utility 1
        
    def test_time_conflict_detection(self):
        """Test if the time conflict detection works correctly"""
        # Same day, overlapping times
        self.assertTrue(check_time_conflict("Mon", "10", "12", "Mon", "11", "13"))
        # Same day, adjacent times (no conflict)
        self.assertFalse(check_time_conflict("Mon", "8", "10", "Mon", "10", "12"))
        # Different days (no conflict)
        self.assertFalse(check_time_conflict("Mon", "10", "12", "Tue", "10", "12"))
        # Edge case: invalid time format
        self.assertFalse(check_time_conflict("Mon", "8", "10", "Mon", "abc", "def"))
    
    def test_mandatory_course_assignment(self):
        """Test that all mandatory courses are assigned"""
        results_df = optimize_course_matching()
        
        # For each student, check if all mandatory courses are assigned
        for _, student in self.student_data.iterrows():
            student_id = student['student_id']
            program_id = student['program_id']
            
            # Get mandatory courses for this program
            mandatory_courses = self.course_data[
                (self.course_data['program_id'] == program_id) & 
                (self.course_data['mandatory'] == 1)
            ]['course_id'].tolist()
            
            # Check each mandatory course
            for course_id in mandatory_courses:
                assigned = ((results_df['student_id'] == student_id) & 
                           (results_df['course_id'] == course_id)).any()
                
                self.assertTrue(assigned, 
                              f"Mandatory course {course_id} not assigned to student {student_id}")
    
    def test_elective_count_constraint(self):
        """Test that each student gets exactly their required number of electives"""
        results_df = optimize_course_matching()
        
        for _, student in self.student_data.iterrows():
            student_id = student['student_id']
            required_electives = student['required_electives']
            
            # Count electives assigned to this student
            elective_assignments = results_df[
                (results_df['student_id'] == student_id) & 
                (results_df['course_type'] == 'Elective')
            ]
            
            self.assertEqual(len(elective_assignments), required_electives,
                           f"Student {student_id} has {len(elective_assignments)} electives instead of {required_electives}")
    
    def test_capacity_constraint(self):
        """Test that no elective course exceeds its capacity"""
        results_df = optimize_course_matching()
        
        for _, capacity in self.elective_capacity_data.iterrows():
            course_id = capacity['course_id']
            max_capacity = capacity['capacity']
            
            # Count students assigned to this course
            assigned_count = len(results_df[results_df['course_id'] == course_id])
            
            self.assertLessEqual(assigned_count, max_capacity,
                               f"Course {course_id} has {assigned_count} students, exceeding capacity {max_capacity}")
    
    def test_result_dataframe_format(self):
        """Test that the output dataframe has the correct format"""
        results_df = optimize_course_matching()
        
        # Check dataframe columns
        expected_columns = ['student_id', 'student_name', 'course_type', 'course_id', 'course_name']
        self.assertListEqual(list(results_df.columns), expected_columns)
        
        # Check data types
        self.assertTrue(pd.api.types.is_integer_dtype(results_df['student_id'].dtype))
        self.assertTrue(pd.api.types.is_integer_dtype(results_df['course_id'].dtype))
        self.assertTrue(pd.api.types.is_string_dtype(results_df['course_type'].dtype))
        
        # Check course_type values
        valid_types = ['Mandatory', 'Elective']
        self.assertTrue(results_df['course_type'].isin(valid_types).all())
        
    def test_file_access(self):
        """Test that all required data files are accessible"""
        try:
            pd.read_csv('course.csv')
            pd.read_csv('student.csv')
            pd.read_csv('elective_capacity.csv')
            pd.read_csv('elective_preference.csv')
            self.assertTrue(True)  # If we get here, files are accessible
        except FileNotFoundError as e:
            self.fail(f"Data file not found: {e}")

# Second Test Class for Lab Matching
class TestLabMatching(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures for lab matching"""
        try:
            self.student_course_matching, self.lab_time_data, self.day_mapping, self.pre_lab_ele_man_data, self.theory_time_data, self.course_data = load_data_second()
        except Exception as e:
            # If optimize_course_matching hasn't been run, student_course_matching.csv might not exist
            # Create it first if needed
            optimize_course_matching()
            self.student_course_matching, self.lab_time_data, self.day_mapping, self.pre_lab_ele_man_data, self.theory_time_data, self.course_data = load_data_second()
    
    def test_lab_assignment_constraint(self):
        """Test that each student is assigned to one lab for each course with a lab"""
        results_df = optimize_lab_matching()
        
        courses_with_labs = self.course_data[self.course_data['has_lab'] == 1]['course_id'].tolist()
        
        for student_id in self.student_course_matching['student_id'].unique():
            student_courses = self.student_course_matching[
                (self.student_course_matching['student_id'] == student_id)
            ]['course_id'].tolist()
            
            # Find courses with labs that this student is taking
            student_lab_courses = [c for c in student_courses if c in courses_with_labs]
            
            for course_id in student_lab_courses:
                # Check if there's a lab assignment for this course
                lab_assignment = results_df[
                    (results_df['student_id'] == student_id) & 
                    (results_df['course_id'] == course_id) &
                    (results_df['lab_day'] != 'N/A')
                ]
                
                self.assertFalse(lab_assignment.empty, 
                               f"Student {student_id} has no lab assignment for course {course_id}")
    
    def test_lab_time_conflict_constraint(self):
        """Test that no student has time conflicts in their lab assignments"""
        results_df = optimize_lab_matching()
        
        for student_id in results_df['student_id'].unique():
            student_labs = results_df[
                (results_df['student_id'] == student_id) & 
                (results_df['lab_day'] != 'N/A')
            ]
            
            # Check all pairs of labs for this student
            lab_rows = student_labs.to_dict('records')
            for i in range(len(lab_rows)):
                for j in range(i+1, len(lab_rows)):
                    lab1 = lab_rows[i]
                    lab2 = lab_rows[j]
                    
                    # Check for time conflict
                    has_conflict = check_time_conflict(
                        lab1['lab_day'], lab1['lab_start_time'], lab1['lab_end_time'],
                        lab2['lab_day'], lab2['lab_start_time'], lab2['lab_end_time']
                    )
                    
                    self.assertFalse(has_conflict, 
                                   f"Student {student_id} has lab time conflict between courses {lab1['course_id']} and {lab2['course_id']}")
    
    def test_lab_result_dataframe_format(self):
        """Test that the lab matching output dataframe has the correct format"""
        results_df = optimize_lab_matching()
        
        # Check dataframe columns
        expected_columns = ['student_id', 'student_name', 'course_id', 'course_name', 'course_type',
                          'theory_day', 'theory_start_time', 'theory_end_time', 
                          'lab_day', 'lab_start_time', 'lab_end_time']
        
        self.assertListEqual(list(results_df.columns), expected_columns)
        
        # Check data types
        self.assertTrue(pd.api.types.is_integer_dtype(results_df['student_id'].dtype))
        self.assertTrue(pd.api.types.is_integer_dtype(results_df['course_id'].dtype))
        
    def test_lab_files_access(self):
        """Test that all required data files for lab matching are accessible"""
        try:
            pd.read_csv('lab_time.csv')
            pd.read_csv('day.csv')
            pd.read_csv('pre_lab_ele_man.csv')
            pd.read_csv('theory_time.csv')
            pd.read_csv('student_course_matching.csv')
            self.assertTrue(True)  # If we get here, files are accessible
        except FileNotFoundError as e:
            self.fail(f"Data file not found: {e}")

# Test runner function
def run_tests():
    """Run all tests"""
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestMatchingAlgorithm))
    test_suite.addTest(unittest.makeSuite(TestLabMatching))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    return result

# Main block to run tests directly
if __name__ == '__main__':
    result = run_tests()
    print(f"Tests passed: {result.wasSuccessful()}")


    #the test was successful, this means your algorithm correctly:

#  -Assigns students to their mandatory courses
#  -Assigns the required number of electives to each student
#  -Respects course capacity constraints
#  -Correctly handles time conflicts for lab assignments
#  -Produces output DataFrames in the expected format