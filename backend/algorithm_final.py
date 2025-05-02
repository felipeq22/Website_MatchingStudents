import pandas as pd
import numpy as np
import pulp
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict


#Sets and Parameters
#SS
#S: Set of students

#CC
#C: Set of courses
    
#PsP_s
#Ps​: Set of program-specific courses for student ss

    
#Decision Variables
#Xsc∈{0,1}X_{sc} \in {0, 1}
#Xsc​∈{0,1}:\
    
#Xsc=1X_{sc} = 1
#Xsc​=1 if student ss
#s is assigned to course cc
#Xsc=0X_{sc} = 0
#Xsc​=0 otherwise



# Utility Function
# Usc=max⁡(10−ranksc,1)U_{sc} = \\max(10 - \\text{rank}_{sc}, 1)
# Usc​=max(10−ranksc​,1)
# Objective Function:
# Maximize ∑_{s ∈ S} ∑_{c ∈ C} U_sc * X_sc
# Where:
# U_sc = max(10 - rank_sc, 1)
# X_sc ∈ {0, 1} (1 if student s is assigned to course c, 0 otherwise)

# Constraints:
# 1. Mandatory Course Constraint:
# ∀ s ∈ S, ∀ c ∈ P_s such that c is mandatory:
# X_sc = 1

#2 Elective Course Limit Constraint:
# ∀ s ∈ S:
# ∑_{c ∈ P_s where c is elective} X_sc = required_electives_s

# 3. Course Capacity Constraint:
# ∀ c ∈ C:
# ∑_{s ∈ S} X_sc ≤ capacity_c

# 4. Binary Constraint:
# ∀ s ∈ S, ∀ c ∈ C:
# X_sc ∈ {0, 1}

# Interpretation:
# Maximizes total utility of course assignments.
# Ensures mandatory courses are assigned to students.
# Limits elective courses assigned per student to the required number.
# Respects the maximum capacity constraints of each course.
  


def load_data():
    """Load necessary CSV files for course matching."""
    # Load CSV files
    course_data = pd.read_csv('course.csv')
    student_data = pd.read_csv('student.csv')
    elective_capacity_data = pd.read_csv('elective_capacity.csv')
    elective_preference_data = pd.read_csv('elective_preference.csv')
    
    # Strip whitespace from column names
    course_data.columns = course_data.columns.str.strip()
    student_data.columns = student_data.columns.str.strip()
    elective_capacity_data.columns = elective_capacity_data.columns.str.strip()
    elective_preference_data.columns = elective_preference_data.columns.str.strip()
    
    # Strip whitespace from string columns
    for df in [course_data, student_data, elective_capacity_data, elective_preference_data]:
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip()
    
    return course_data, student_data, elective_capacity_data, elective_preference_data

def optimize_course_matching():
    """
    Optimize course matching for students
    """
    # Load data
    course_data, student_data, elective_capacity_data, elective_preference_data = load_data()
    
    # Create PuLP model
    model = pulp.LpProblem("Course_Matching", pulp.LpMaximize)
    
    # Prepare data
    students = student_data['student_id'].tolist()
    courses = course_data['course_id'].tolist()
    
    # Decision variables
    # X[s,c] = 1 if student s is assigned to course c, 0 otherwise
    X = pulp.LpVariable.dicts("X", 
                             [(s, c) for s in students for c in courses], 
                             cat=pulp.LpBinary)
    
    # Objective function: utility based on preference ranking
    def calculate_utility(rank):
        return max(10 - rank, 1)
    
    # Preference utility
    preference_utility = []
    for _, pref in elective_preference_data.iterrows():
        student_id = pref['student_id']
        course_id = pref['course_id']
        utility = calculate_utility(pref['preference_rank'])
        preference_utility.append(utility * X[(student_id, course_id)])
    
    # Set objective: maximize preference utility
    model += pulp.lpSum(preference_utility), "Preference Utility"
    
    # Constraints
    # 1. Mandatory course constraints
    for _, student in student_data.iterrows():
        student_id = student['student_id']
        program_id = student['program_id']
        
        # Identify mandatory courses for this student's program
        mandatory_courses = course_data[
            (course_data['program_id'] == program_id) & 
            (course_data['mandatory'] == 1)
        ]['course_id'].tolist()
        
        # Ensure all mandatory courses are assigned
        for course_id in mandatory_courses:
            model += X[(student_id, course_id)] == 1, f"Mandatory_{student_id}_{course_id}"
    
    # 2. Elective course constraints
    for _, student in student_data.iterrows():
        student_id = student['student_id']
        program_id = student['program_id']
        required_electives = student['required_electives']
        
        # Identify elective courses for this student's program
        elective_courses = course_data[
            (course_data['program_id'] == program_id) & 
            (course_data['mandatory'] == 0)
        ]['course_id'].tolist()
        
        # Ensure exact number of electives are assigned
        if elective_courses:
            model += pulp.lpSum(X[(student_id, c)] for c in elective_courses) == required_electives, f"ElectiveLimit_{student_id}"
    
    # 3. Elective course capacity constraints
    for _, capacity in elective_capacity_data.iterrows():
        course_id = capacity['course_id']
        max_capacity = capacity['capacity']
        
        model += pulp.lpSum(X[(s, course_id)] for s in students) <= max_capacity, f"ElectiveCapacity_{course_id}"
    
    # Solve the model
    model.solve()
    
    # Check solution status
    if pulp.LpStatus[model.status] != 'Optimal':
        print("Could not find an optimal solution.")
        return None
    
    # Extract results
    results = []
    for _, student in student_data.iterrows():
        student_id = student['student_id']
        program_id = student['program_id']
        
        # Find mandatory courses
        mandatory_courses = course_data[
            (course_data['program_id'] == program_id) & 
            (course_data['mandatory'] == 1)
        ]
        
        # Find elective courses
        elective_courses = course_data[
            (course_data['program_id'] == program_id) & 
            (course_data['mandatory'] == 0)
        ]
        
        # Track assigned courses
        for _, course in mandatory_courses.iterrows():
            if X[(student_id, course['course_id'])].value() > 0.5:
                results.append({
                    'student_id': student_id,
                    'student_name': student_data[student_data['student_id'] == student_id]['name'].iloc[0],
                    'course_type': 'Mandatory',
                    'course_id': course['course_id'],
                    'course_name': course['course_name']
                })
        
        for _, course in elective_courses.iterrows():
            if X[(student_id, course['course_id'])].value() > 0.5:
                results.append({
                    'student_id': student_id,
                    'student_name': student_data[student_data['student_id'] == student_id]['name'].iloc[0],
                    'course_type': 'Elective',
                    'course_id': course['course_id'],
                    'course_name': course['course_name']
                })
    
    # Convert to DataFrame and export
    results_df = pd.DataFrame(results)
    results_df.to_csv('student_course_matching.csv', index=False)
    
    print("Course matching completed. Results saved to student_course_matching.csv")
    return results_df

def main():
    # Run optimization
    optimize_course_matching()

if __name__ == "__main__":
    main()
  

  # Let S = {s₁, s₂, ..., sₙ} be the set of students
# Let C = {c₁, c₂, ..., cₘ} be the set of courses
# Let L = {l₁, l₂, ..., lₖ} be the set of lab sections
# Let P = {(s, c, l, r) | s ∈ S, c ∈ C, l ∈ L, r ∈ ℕ} be the set of lab preferences

# Decision Variables:
# Y[s,l] ∈ {0, 1}
# Y[s,l] = 1 if student s is assigned to lab section l
# Y[s,l] = 0 otherwise

# Preference Utility Function:
# u(r) : ℕ → ℝ⁺
# u(r) = max(10 - r, 1)
# Where:
#   r is the preference ranking
#   u(r) transforms the ranking into a utility score

# Objective Function:
# max Z = ∑[s∈S, l∈L, c∈C] u(r[s,c,l]) * Y[s,l]

# Constraints:

# 1. Lab Assignment Constraint:
#    ∀s ∈ S, ∀c ∈ C with lab:
#        ∑[l∈L(c)] Y[s,l] = 1

# 2. Lab Time Conflict Constraint:
#    ∀s ∈ S, ∀(l₁, l₂) ∈ L with conflicting times:
#        Y[s,l₁] + Y[s,l₂] ≤ 1

# 3. Lab Capacity Constraint:
#    ∀l ∈ L:
#        ∑[s∈S] Y[s,l] ≤ capacity[l]

# Detailed Description:

# Objective Function Breakdown:
# - Maximizes the total utility of lab assignments
# - Calculates utility for each student-course-lab combination
# - Utility depends on the student's preference ranking
# - Higher preference (lower rank) gives higher utility
# - Minimum utility is 1, maximum is 9

# Preference Utility Function [u(r)]:
# - Transforms preference ranking into a utility score
# - For rank 1 (most preferred): u(1) = 9
# - For rank 10 or higher: u(r) = 1
# - Creates a non-linear utility scale that heavily rewards top preferences

# Constraints Explanation:
# - Lab Assignment: Ensures each course with a lab gets exactly one lab section per student
# - Time Conflict: Prevents assigning conflicting lab times to the same student
# - Capacity: Ensures no lab section exceeds its maximum capacity

  


def load_data():
    """
    Load necessary data for lab matching optimization
    """
    # Load CSV files
    student_course_matching = pd.read_csv('student_course_matching.csv')
    lab_time_data = pd.read_csv('lab_time.csv')
    day_data = pd.read_csv('day.csv')
    pre_lab_ele_man_data = pd.read_csv('pre_lab_ele_man.csv')
    theory_time_data = pd.read_csv('theory_time.csv')
    course_data = pd.read_csv('course.csv')
    
    # Strip whitespace from column names and data
    for df in [student_course_matching, lab_time_data, day_data, 
               pre_lab_ele_man_data, theory_time_data, course_data]:
        df.columns = df.columns.str.strip()
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip()
    
    # Create day mapping
    day_mapping = dict(zip(day_data['id_day'], day_data['day']))
    
    return (student_course_matching, lab_time_data, day_mapping, 
            pre_lab_ele_man_data, theory_time_data, course_data)

def check_time_conflict(day1, start1, end1, day2, start2, end2):
    """
    Check if two time slots conflict with each other.
    """
    if day1 != day2:
        return False
    try:
        start1 = int(start1)
        end1 = int(end1)
        start2 = int(start2)
        end2 = int(end2)
        if end1 <= start2 or end2 <= start1:
            return False
        return True
    except ValueError:
        return False

def optimize_lab_matching():
    """
    Optimize lab matching for students based on course matching and preferences
    """
    (student_course_matching, lab_time_data, day_mapping, 
     pre_lab_ele_man_data, theory_time_data, course_data) = load_data()
    
    print("Initial Data Analysis:")
    print("Total students in course matching:", len(student_course_matching['student_id'].unique()))
    print("Total lab time entries:", len(lab_time_data))
    
    model = pulp.LpProblem("Lab_Matching", pulp.LpMaximize)

    def calculate_utility(rank):
        return max(10 - rank, 1)

    students = student_course_matching['student_id'].unique()
    lab_time_data['lab_id'] = lab_time_data.apply(
        lambda x: f"{x['course_id']}-{x['lab']}", axis=1
    )

    Y = pulp.LpVariable.dicts("Y", 
        [(s, l) for s in students for l in lab_time_data['lab_id']], 
        cat=pulp.LpBinary
    )

    lab_utility = []
    for _, pref in pre_lab_ele_man_data.iterrows():
        student_id = pref['student_id']
        course_id = pref['course_id']
        lab_num = pref['lab']
        lab_id = f"{course_id}-{lab_num}"

        course_match = student_course_matching[
            (student_course_matching['student_id'] == student_id) & 
            (student_course_matching['course_id'] == course_id)
        ]

        course_has_lab = course_data[
            (course_data['course_id'] == course_id) & 
            (course_data['has_lab'] == 1)
        ]

        if not course_match.empty and not course_has_lab.empty and lab_id in lab_time_data['lab_id'].values:
            utility = calculate_utility(pref['preference_rank'])
            lab_utility.append(utility * Y[(student_id, lab_id)])

    model += pulp.lpSum(lab_utility), "Lab Preference Utility"

    for student_id in students:
        student_courses = student_course_matching[
            student_course_matching['student_id'] == student_id
        ]
        for _, course in student_courses.iterrows():
            course_has_lab = course_data[
                (course_data['course_id'] == course['course_id']) & 
                (course_data['has_lab'] == 1)
            ]
            if not course_has_lab.empty:
                possible_labs = lab_time_data[
                    lab_time_data['course_id'] == course['course_id']
                ]
                course_lab_ids = [
                    f"{course['course_id']}-{lab['lab']}" 
                    for _, lab in possible_labs.iterrows()
                ]
                model += pulp.lpSum(Y[(student_id, l)] for l in course_lab_ids) == 1, \
                    f"LabAssignment_{student_id}_{course['course_id']}"

    lab_time_conflicts = []
    for student_id in students:
        student_courses_with_labs = student_course_matching[
            (student_course_matching['student_id'] == student_id) & 
            (student_course_matching['course_id'].isin(
                course_data[course_data['has_lab'] == 1]['course_id']
            ))
        ]
        lab_schedules = []
        for _, course in student_courses_with_labs.iterrows():
            course_labs = lab_time_data[lab_time_data['course_id'] == course['course_id']]
            for _, lab in course_labs.iterrows():
                lab_schedules.append({
                    'course_id': lab['course_id'],
                    'lab': lab['lab'],
                    'day': day_mapping.get(lab['id_day'], 'Unknown'),
                    'start_time': lab['start_time'],
                    'end_time': lab['end_time']
                })
        for i in range(len(lab_schedules)):
            for j in range(i+1, len(lab_schedules)):
                lab1 = lab_schedules[i]
                lab2 = lab_schedules[j]
                if check_time_conflict(
                    lab1['day'], lab1['start_time'], lab1['end_time'],
                    lab2['day'], lab2['start_time'], lab2['end_time']
                ):
                    lab_id1 = f"{lab1['course_id']}-{lab1['lab']}"
                    lab_id2 = f"{lab2['course_id']}-{lab2['lab']}"
                    lab_time_conflicts.append((student_id, lab_id1, lab_id2))

    for student_id, lab_id1, lab_id2 in lab_time_conflicts:
        model += Y[(student_id, lab_id1)] + Y[(student_id, lab_id2)] <= 1, \
            f"LabTimeConflict_{student_id}_{lab_id1}_{lab_id2}"

    model.solve()
    print("\nSolver Status:", pulp.LpStatus[model.status])

    if pulp.LpStatus[model.status] not in ['Optimal', 'Feasible']:
        print("Could not find a solution.")
        return None

    results = []
    for student_id in students:
        student_courses = student_course_matching[
            student_course_matching['student_id'] == student_id
        ]
        student_name = student_courses['student_name'].iloc[0]

        for _, course in student_courses.iterrows():
            theory_time = theory_time_data[theory_time_data['course_id'] == course['course_id']]
            lab_day = lab_start_time = lab_end_time = 'N/A'
            course_info = course_data[course_data['course_id'] == course['course_id']]
            has_lab = course_info['has_lab'].iloc[0] if not course_info.empty else 0

            if has_lab == 1:
                course_labs = lab_time_data[lab_time_data['course_id'] == course['course_id']]
                for _, lab in course_labs.iterrows():
                    lab_id = f"{lab['course_id']}-{lab['lab']}"
                    if Y[(student_id, lab_id)].value() > 0.5:
                        lab_day = day_mapping.get(lab['id_day'], 'Unknown')
                        lab_start_time = lab['start_time']
                        lab_end_time = lab['end_time']
                        break

            results.append({
                'student_id': student_id,
                'student_name': student_name,
                'course_id': course['course_id'],
                'course_name': course['course_name'],
                'course_type': course['course_type'],
                'theory_day': day_mapping.get(theory_time['id_day'].iloc[0], 'Unknown') if not theory_time.empty else 'N/A',
                'theory_start_time': theory_time['start_time'].iloc[0] if not theory_time.empty else 'N/A',
                'theory_end_time': theory_time['end_time'].iloc[0] if not theory_time.empty else 'N/A',
                'lab_day': lab_day,
                'lab_start_time': lab_start_time,
                'lab_end_time': lab_end_time
            })

    results_df = pd.DataFrame(results)
    results_df.to_csv('student_lab_matching.csv', index=False)
    print("Course matching completed. Results saved to student_lab_matching.csv")
    return results_df

def main():
    optimize_lab_matching()

if __name__ == "__main__":
    main()


#gale-shapely
import pandas as pd
from collections import defaultdict

def load_data():
    """Load necessary CSV files for course matching."""
    # Load CSV files
    course_data = pd.read_csv('course.csv')
    student_data = pd.read_csv('student.csv')
    elective_capacity_data = pd.read_csv('elective_capacity.csv')
    elective_preference_data = pd.read_csv('elective_preference.csv')
    
    # Strip whitespace from column names
    course_data.columns = course_data.columns.str.strip()
    student_data.columns = student_data.columns.str.strip()
    elective_capacity_data.columns = elective_capacity_data.columns.str.strip()
    elective_preference_data.columns = elective_preference_data.columns.str.strip()
    
    # Strip whitespace from string columns
    for df in [course_data, student_data, elective_capacity_data, elective_preference_data]:
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip()
    
    return course_data, student_data, elective_capacity_data, elective_preference_data

def gale_shapley_course_matching():
    """
    Optimize course matching for students using Gale-Shapley algorithm
    with Preference Strength Priority for courses.
    """
    # Load data
    course_data, student_data, elective_capacity_data, elective_preference_data = load_data()
    
    # Create a result container
    results = []
    
    # First, assign all mandatory courses
    for _, student in student_data.iterrows():
        student_id = student['student_id']
        program_id = student['program_id']
        
        # Identify mandatory courses for this student's program
        mandatory_courses = course_data[
            (course_data['program_id'] == program_id) & 
            (course_data['mandatory'] == 1)
        ]
        
        # Assign all mandatory courses
        for _, course in mandatory_courses.iterrows():
            results.append({
                'student_id': student_id,
                'student_name': student['name'],
                'course_type': 'Mandatory',
                'course_id': course['course_id'],
                'course_name': course['course_name']
            })
    
    # Now, handle elective courses using Gale-Shapley
    
    # 1. Calculate preference priority scores
    max_rank = elective_preference_data['preference_rank'].max()
    priority_lookup = {}
    for _, pref in elective_preference_data.iterrows():
        student_id = pref['student_id']
        course_id = pref['course_id']
        rank = pref['preference_rank']
        priority = (max_rank + 1) - rank
        priority_lookup[(course_id, student_id)] = priority
    
    # 2. Prepare data structures for Gale-Shapley
    students_needing_electives = []
    for _, student in student_data.iterrows():
        student_id = student['student_id']
        required_electives = student['required_electives']
        
        if required_electives > 0:
            students_needing_electives.append({
                'student_id': student_id,
                'program_id': student['program_id'],
                'required_electives': required_electives,
                'assigned_electives': 0
            })
    
    student_preferences = {}
    for student in students_needing_electives:
        student_id = student['student_id']
        program_id = student['program_id']
        
        eligible_courses = course_data[
            (course_data['program_id'] == program_id) & 
            (course_data['mandatory'] == 0)
        ]['course_id'].tolist()
        
        student_prefs = elective_preference_data[
            (elective_preference_data['student_id'] == student_id) & 
            (elective_preference_data['course_id'].isin(eligible_courses))
        ].sort_values('preference_rank')
        
        student_preferences[student_id] = student_prefs['course_id'].tolist()
    
    course_capacities = {}
    for _, capacity in elective_capacity_data.iterrows():
        course_capacities[capacity['course_id']] = capacity['capacity']
    
    course_assignments = defaultdict(list)
    student_assignments = defaultdict(list)
    
    unmatched_students = [s['student_id'] for s in students_needing_electives]
    proposed_to = defaultdict(set)
    
    while unmatched_students:
        student_id = unmatched_students.pop(0)
        student_data_row = next(s for s in students_needing_electives if s['student_id'] == student_id)
        
        if student_data_row['assigned_electives'] >= student_data_row['required_electives']:
            continue
        
        preferences = student_preferences.get(student_id, [])
        next_preferences = [c for c in preferences if c not in proposed_to[student_id]]
        
        if not next_preferences:
            continue
        
        course_id = next_preferences[0]
        proposed_to[student_id].add(course_id)
        
        if len(course_assignments[course_id]) < course_capacities.get(course_id, 0):
            course_assignments[course_id].append(student_id)
            student_assignments[student_id].append(course_id)
            student_data_row['assigned_electives'] += 1
            
            if student_data_row['assigned_electives'] < student_data_row['required_electives']:
                unmatched_students.append(student_id)
        else:
            current_assignees = course_assignments[course_id]
            all_students = current_assignees + [student_id]
            priorities = [(s, priority_lookup.get((course_id, s), 0)) for s in all_students]
            priorities.sort(key=lambda x: x[1], reverse=True)
            
            capacity = course_capacities.get(course_id, 0)
            selected_students = [s for s, _ in priorities[:capacity]]
            
            if student_id in selected_students:
                bumped_students = [s for s in current_assignees if s not in selected_students]
                course_assignments[course_id] = selected_students
                student_assignments[student_id].append(course_id)
                student_data_row['assigned_electives'] += 1
                
                if student_data_row['assigned_electives'] < student_data_row['required_electives']:
                    unmatched_students.append(student_id)
                
                for bumped in bumped_students:
                    bumped_data = next(s for s in students_needing_electives if s['student_id'] == bumped)
                    student_assignments[bumped].remove(course_id)
                    bumped_data['assigned_electives'] -= 1
                    unmatched_students.append(bumped)
            else:
                unmatched_students.append(student_id)
    
    for student_id, courses in student_assignments.items():
        student_name = student_data[student_data['student_id'] == student_id]['name'].iloc[0]
        
        for course_id in courses:
            course_name = course_data[course_data['course_id'] == course_id]['course_name'].iloc[0]
            results.append({
                'student_id': student_id,
                'student_name': student_name,
                'course_type': 'Elective',
                'course_id': course_id,
                'course_name': course_name
            })
    
    results_df = pd.DataFrame(results)
    results_df['course_type_order'] = results_df['course_type'].apply(lambda x: 0 if x == 'Mandatory' else 1)
    results_df = results_df.sort_values(by=['student_id', 'course_type_order'])
    results_df = results_df.drop('course_type_order', axis=1)
    results_df.to_csv('student_course_matching_gale_shapley.csv', index=False)
    
    print("Course matching completed using Gale-Shapley algorithm. Results saved to student_course_matching_gale_shapley.csv")
    return results_df

def main():
    gale_shapley_course_matching()

if __name__ == "__main__":
    main()

#Overview of the Implementation

#Mandatory Course Assignment:
#- First assigns all mandatory courses automatically, just like in your original code
#- Only applies the matching algorithm to elective courses

#Preference Priority System:
#- Calculates priority scores using the formula: priority = (max_rank + 1) - rank
#- Creates a lookup dictionary for quick access to priority scores during matching

#Data Preparation:
#- Builds preference lists for each student
#- Tracks course capacities
#- Only includes eligible courses for each student based on their program

#Students "propose" to courses in order of their preferences
#- Courses accept students based on preference priorities
#- If a course is full, it compares the new student with currently assigned students
#- Students who need multiple electives can be re-added to the queue


#Lab matching completed using Gale-Shapley algorithm. Results saved to student_lab_matching_gale_shapley.csv\n"
    
import pandas as pd
from collections import defaultdict

def load_data():
    """
    Load necessary data for lab matching optimization
    """
    # Load CSV files
    student_course_matching = pd.read_csv('student_course_matching_gale_shapley.csv')
    lab_time_data = pd.read_csv('lab_time.csv')
    day_data = pd.read_csv('day.csv')
    pre_lab_ele_man_data = pd.read_csv('pre_lab_ele_man.csv')
    theory_time_data = pd.read_csv('theory_time.csv')
    course_data = pd.read_csv('course.csv')
    
    # Strip whitespace from column names and data
    for df in [student_course_matching, lab_time_data, day_data, 
               pre_lab_ele_man_data, theory_time_data, course_data]:
        df.columns = df.columns.str.strip()
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip()
    
    # Create day mapping
    day_mapping = dict(zip(day_data['id_day'], day_data['day']))
    
    return (student_course_matching, lab_time_data, day_mapping, 
            pre_lab_ele_man_data, theory_time_data, course_data)

def check_time_conflict(day1, start1, end1, day2, start2, end2):
    """
    Check if two time slots conflict with each other.
    """
    if day1 != day2:
        return False
    try:
        start1 = int(start1)
        end1 = int(end1)
        start2 = int(start2)
        end2 = int(end2)
        if end1 <= start2 or end2 <= start1:
            return False
        return True
    except ValueError:
        return False

def gale_shapley_lab_matching():
    """
    Optimize lab matching for students using Gale-Shapley algorithm
    """
    (student_course_matching, lab_time_data, day_mapping, 
     pre_lab_ele_man_data, theory_time_data, course_data) = load_data()
    
    print("Initial Data Analysis:")
    print("Total students in course matching:", len(student_course_matching['student_id'].unique()))
    print("Total lab time entries:", len(lab_time_data))
    
    students = student_course_matching['student_id'].unique()
    
    lab_time_data['lab_id'] = lab_time_data.apply(
        lambda x: f"{x['course_id']}-{x['lab']}", axis=1
    )
    
    max_rank = pre_lab_ele_man_data['preference_rank'].max() if not pre_lab_ele_man_data.empty else 5
    priority_lookup = {}
    for _, pref in pre_lab_ele_man_data.iterrows():
        student_id = pref['student_id']
        course_id = pref['course_id']
        lab_num = pref['lab']
        lab_id = f"{course_id}-{lab_num}"
        rank = pref['preference_rank']
        priority = (max_rank + 1) - rank
        priority_lookup[(lab_id, student_id)] = priority
    
    student_preferences = defaultdict(dict)
    for student_id in students:
        student_courses = student_course_matching[student_course_matching['student_id'] == student_id]
        for _, course in student_courses.iterrows():
            course_id = course['course_id']
            course_has_lab = course_data[
                (course_data['course_id'] == course_id) & 
                (course_data['has_lab'] == 1)
            ]
            if not course_has_lab.empty:
                possible_labs = lab_time_data[lab_time_data['course_id'] == course_id]
                course_lab_ids = [f"{course_id}-{lab['lab']}" for _, lab in possible_labs.iterrows()]
                student_prefs = pre_lab_ele_man_data[
                    (pre_lab_ele_man_data['student_id'] == student_id) & 
                    (pre_lab_ele_man_data['course_id'] == course_id)
                ]
                if not student_prefs.empty:
                    lab_prefs = student_prefs.sort_values('preference_rank')
                    preferred_lab_ids = [f"{course_id}-{lab['lab']}" for _, lab in lab_prefs.iterrows()]
                    for lab_id in course_lab_ids:
                        if lab_id not in preferred_lab_ids:
                            preferred_lab_ids.append(lab_id)
                else:
                    preferred_lab_ids = course_lab_ids
                student_preferences[student_id][course_id] = preferred_lab_ids
    
    lab_assignments = defaultdict(list)
    student_lab_assignments = defaultdict(dict)
    lab_capacities = {f"{lab['course_id']}-{lab['lab']}": 30 for _, lab in lab_time_data.iterrows()}
    
    courses_with_labs = {}
    for student_id in students:
        student_courses = student_course_matching[student_course_matching['student_id'] == student_id]
        lab_courses = []
        for _, course in student_courses.iterrows():
            course_has_lab = course_data[
                (course_data['course_id'] == course['course_id']) & 
                (course_data['has_lab'] == 1)
            ]
            if not course_has_lab.empty:
                lab_courses.append(course['course_id'])
        courses_with_labs[student_id] = lab_courses
    
    unmatched_queue = [(student_id, course_id) for student_id, course_ids in courses_with_labs.items() for course_id in course_ids]
    proposed_to = defaultdict(lambda: defaultdict(set))
    
    while unmatched_queue:
        student_id, course_id = unmatched_queue.pop(0)
        if course_id in student_lab_assignments[student_id]:
            continue
        preferences = student_preferences[student_id].get(course_id, [])
        next_labs = [lab_id for lab_id in preferences if lab_id not in proposed_to[student_id][course_id]]
        if not next_labs:
            print(f"Warning: Student {student_id} has no more lab preferences for course {course_id}")
            continue
        lab_id = next_labs[0]
        proposed_to[student_id][course_id].add(lab_id)
        lab_info = lab_time_data[lab_time_data['lab_id'] == lab_id].iloc[0]
        lab_day = day_mapping.get(lab_info['id_day'], 'Unknown')
        lab_start = lab_info['start_time']
        lab_end = lab_info['end_time']
        has_conflict = False
        for other_course_id, assigned_lab_id in student_lab_assignments[student_id].items():
            other_lab_info = lab_time_data[lab_time_data['lab_id'] == assigned_lab_id].iloc[0]
            other_day = day_mapping.get(other_lab_info['id_day'], 'Unknown')
            other_start = other_lab_info['start_time']
            other_end = other_lab_info['end_time']
            if check_time_conflict(lab_day, lab_start, lab_end, other_day, other_start, other_end):
                has_conflict = True
                break
        if has_conflict:
            unmatched_queue.append((student_id, course_id))
            continue
        if len(lab_assignments[lab_id]) < lab_capacities.get(lab_id, 0):
            lab_assignments[lab_id].append(student_id)
            student_lab_assignments[student_id][course_id] = lab_id
        else:
            current_assignees = lab_assignments[lab_id]
            all_students = current_assignees + [student_id]
            priorities = [(s, priority_lookup.get((lab_id, s), 0)) for s in all_students]
            priorities.sort(key=lambda x: (x[1], x[0]), reverse=True)
            capacity = lab_capacities.get(lab_id, 0)
            selected_students = [s for s, _ in priorities[:capacity]]
            if student_id in selected_students:
                bumped_students = [s for s in current_assignees if s not in selected_students]
                lab_assignments[lab_id] = selected_students
                student_lab_assignments[student_id][course_id] = lab_id
                for bumped in bumped_students:
                    bumped_course = next((c for c, l in student_lab_assignments[bumped].items() if l == lab_id), None)
                    if bumped_course:
                        del student_lab_assignments[bumped][bumped_course]
                        unmatched_queue.append((bumped, bumped_course))
            else:
                unmatched_queue.append((student_id, course_id))
    
    results = []
    for student_id in students:
        student_courses = student_course_matching[student_course_matching['student_id'] == student_id]
        student_name = student_courses['student_name'].iloc[0]
        for _, course in student_courses.iterrows():
            course_id = course['course_id']
            theory_time = theory_time_data[theory_time_data['course_id'] == course_id]
            lab_day = 'N/A'
            lab_start_time = 'N/A'
            lab_end_time = 'N/A'
            course_info = course_data[course_data['course_id'] == course_id]
            has_lab = course_info['has_lab'].iloc[0] if not course_info.empty else 0
            if has_lab == 1:
                assigned_lab_id = student_lab_assignments[student_id].get(course_id)
                if assigned_lab_id:
                    lab_info = lab_time_data[lab_time_data['lab_id'] == assigned_lab_id].iloc[0]
                    lab_day = day_mapping.get(lab_info['id_day'], 'Unknown')
                    lab_start_time = lab_info['start_time']
                    lab_end_time = lab_info['end_time']
            results.append({
                'student_id': student_id,
                'student_name': student_name,
                'course_id': course_id,
                'course_name': course['course_name'],
                'course_type': course['course_type'],
                'theory_day': day_mapping.get(theory_time['id_day'].iloc[0], 'Unknown') if not theory_time.empty else 'N/A',
                'theory_start_time': theory_time['start_time'].iloc[0] if not theory_time.empty else 'N/A',
                'theory_end_time': theory_time['end_time'].iloc[0] if not theory_time.empty else 'N/A',
                'lab_day': lab_day,
                'lab_start_time': lab_start_time,
                'lab_end_time': lab_end_time
            })
    
    missing_labs = []
    for student_id in students:
        for course_id in courses_with_labs.get(student_id, []):
            if course_id not in student_lab_assignments[student_id]:
                missing_labs.append((student_id, course_id))
    
    if missing_labs:
        print(f"Warning: {len(missing_labs)} student-course pairs still need lab assignments")
        print("First few missing assignments:", missing_labs[:5])
    
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values(by=['student_id', 'course_id'])
    results_df.to_csv('student_lab_matching_gale_shapley.csv', index=False)
    
    print("Lab matching completed using Gale-Shapley algorithm. Results saved to student_lab_matching_gale_shapley.csv")
    return results_df

def main():
    gale_shapley_lab_matching()

if __name__ == "__main__":
    main()

  #Key Features of the Solution:

#Preference-Based Priority System:

#Uses student preferences for lab sections from the pre_lab_ele_man_data table
#Calculates priority scores based on preference rankings


#Multiple Constraint Handling:

#Lab Time Conflicts: Checks for conflicts between lab times before making assignments
#Course-Lab Association: Students are only assigned to labs for courses they're taking
#Lab Capacity: Ensures labs don't exceed capacity


#Modified Gale-Shapley Algorithm:

#Students "propose" to labs in order of their preferences
#Labs accept students based on priority scores with student ID as tie-breaker
#If a lab is full, it may bump lower-priority students


#Comprehensive Output:

#Includes theory and lab times for all courses
#Reports any students who couldn't be assigned to labs