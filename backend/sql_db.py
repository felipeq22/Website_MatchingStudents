import pandas as pd
import sqlite3

#load csv


def load_csvs_to_db(csv_folder_path, db_name="student_matching.db"):
    # Define the filenames and corresponding table names
    files_tables = {
        "course.csv": "course",
        "day.csv": "day",
        "elective_capacity.csv": "elective_capacity",
        "elective_preference.csv": "elective_preference",
        "lab_time.csv": "lab_time",
        "pre_lab_ele_man.csv": "pre_lab_ele_man",
        "program.csv": "program",
        "student.csv": "student",
        "theory_time.csv": "theory"
    }

    # Create connection to the SQLite database
    conn = sqlite3.connect(db_name)

    # Read each CSV and store in the database
    for filename, table_name in files_tables.items():
        df = pd.read_csv(f"{csv_folder_path}/{filename}")
        df.to_sql(table_name, conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()
    print(f"All tables loaded into {db_name}")

#load data for elective course matching

def load_data_first():
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

def load_data_second():
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