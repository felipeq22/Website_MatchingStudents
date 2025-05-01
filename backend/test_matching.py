import unittest
import pandas as pd
from algorithm_final import load_data, optimize_course_matching, check_time_conflict, optimize_lab_matching

class TestMatchingCode(unittest.TestCase):

    def test_load_data_structure(self):
        """Check that load_data returns DataFrames with expected columns"""
        course_data, student_data, elective_capacity_data, elective_preference_data = load_data()
        self.assertIn('course_id', course_data.columns)
        self.assertIn('student_id', student_data.columns)
        self.assertFalse(elective_capacity_data.empty)
        self.assertFalse(elective_preference_data.empty)

    def test_optimize_course_matching_output(self):
        """Ensure course matching returns a non-empty DataFrame with expected columns"""
        result_df = optimize_course_matching()
        self.assertIsNotNone(result_df)
        self.assertFalse(result_df.empty)
        self.assertIn('student_id', result_df.columns)
        self.assertIn('course_type', result_df.columns)
        self.assertIn('course_id', result_df.columns)

    def test_check_time_conflict(self):
        """Test the time conflict detection logic"""
        self.assertTrue(check_time_conflict("Mon", "10", "12", "Mon", "11", "13"))
        self.assertFalse(check_time_conflict("Mon", "10", "12", "Tue", "10", "12"))
        self.assertFalse(check_time_conflict("Mon", "10", "11", "Mon", "11", "12"))
        self.assertFalse(check_time_conflict("Mon", "10", "12", "Mon", "12", "14"))

    def test_lab_matching_output(self):
        """Ensure lab matching returns a valid result DataFrame"""
        result_df = optimize_lab_matching()
        self.assertIsNotNone(result_df)
        self.assertFalse(result_df.empty)
        self.assertIn('student_id', result_df.columns)
        self.assertIn('lab_day', result_df.columns)
        self.assertIn('course_id', result_df.columns)

if __name__ == '__main__':
    unittest.main()