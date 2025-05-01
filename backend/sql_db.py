import pandas as pd
import sqlite3

#load csv


course = pd.read_csv("course.csv")
day = pd.read_csv("day.csv")
elective_capacity = pd.read_csv("elective_capacity.csv")
elective_preference = pd.read_csv("elective_preference.csv")
lab_time = pd.read_csv("lab_time.csv")
pre_lab_ele_man = pd.read_csv("pre_lab_ele_man.csv")
program = pd.read_csv("program.csv")
student = pd.read_csv("student.csv")
theory_time = pd.read_csv("theory_time.csv")

#make database

# Create a connection to the database (or create it if it doesn't exist)
conn = sqlite3.connect("student_matching.db")

# Save each DataFrame to the database as a table
course.to_sql("course", conn, if_exists="replace", index=False)
day.to_sql("day", conn, if_exists="replace", index=False)
elective_capacity.to_sql("elective_capacity", conn, if_exists="replace", index=False)
elective_preference.to_sql("elective_preference", conn, if_exists="replace", index=False)
lab_time.to_sql("lab_time", conn, if_exists="replace", index=False)
pre_lab_ele_man.to_sql("pre_lab_ele_man", conn, if_exists="replace", index=False)
program.to_sql("program", conn, if_exists="replace", index=False)
student.to_sql("student", conn, if_exists="replace", index=False)
theory.to_sql("theory", conn, if_exists="replace", index=False)

conn.commit()

#load data for elective course matching

def load_elective_matching_data():
    """
    Load data for elective course matching from the SQLite database.
    """
    conn = sqlite3.connect('student_matching.db')

    course_data = pd.read_sql_query("SELECT * FROM course", conn)
    student_data = pd.read_sql_query("SELECT * FROM student", conn)
    elective_capacity_data = pd.read_sql_query("SELECT * FROM elective_capacity", conn)
    elective_preference_data = pd.read_sql_query("SELECT * FROM elective_preference", conn)

    # Clean up whitespace
    for df in [course_data, student_data, elective_capacity_data, elective_preference_data]:
        df.columns = df.columns.str.strip()
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip()

    conn.close()
    return course_data, student_data, elective_capacity_data, elective_preference_data

#load data for lab course matching

def load_lab_matching_data():
    """
    Load data for lab matching optimization from the SQLite database.
    """
    conn = sqlite3.connect('student_matching.db')

    student_course_matching = pd.read_sql_query("SELECT * FROM student_course_matching", conn)
    lab_time_data = pd.read_sql_query("SELECT * FROM lab_time", conn)
    day_data = pd.read_sql_query("SELECT * FROM day", conn)
    pre_lab_ele_man_data = pd.read_sql_query("SELECT * FROM pre_lab_ele_man", conn)
    theory_time_data = pd.read_sql_query("SELECT * FROM theory_time", conn)
    course_data = pd.read_sql_query("SELECT * FROM course", conn)

    # Clean up whitespace
    for df in [student_course_matching, lab_time_data, day_data,
               pre_lab_ele_man_data, theory_time_data, course_data]:
        df.columns = df.columns.str.strip()
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip()

    # Map day IDs to day names
    day_mapping = dict(zip(day_data['id_day'], day_data['day']))

    conn.close()
    return (student_course_matching, lab_time_data, day_mapping,
            pre_lab_ele_man_data, theory_time_data, course_data)