import pulp
import pandas as pd
import numpy as np
from collections import defaultdict
import random
import time
import math

def phase1_course_matching(students, courses, course_preferences, 
                          mandatory_courses, max_electives):
    """
    Phase 1: Match students to courses using Integer Linear Programming.
    
    Parameters:
    -----------
    students : list of dict
        List of student information with keys 'id', 'name', 'program'
    courses : list of dict
        List of course information with keys 'id', 'name', 'type', 'allowed_programs', 'has_lab'
    course_preferences : dict
        Dict mapping (student_id, course_id) to preference rank (1-5, where 1 is most preferred)
    mandatory_courses : dict
        Dict mapping program to list of mandatory course_ids
    max_electives : dict
        Dict mapping program to number of elective courses each student should take
        
    Returns:
    --------
    course_assignments : dict
        Dict mapping student_id to list of assigned course_ids
    stats : dict
        Dict containing statistics about the assignment
    """
    # Create the ILP problem
    prob = pulp.LpProblem("CourseMatching", pulp.LpMaximize)
    
    # Decision variables - x[s,c] = 1 if student s is assigned to course c
    x = {}
    for student in students:
        student_id = student['id']
        program = student['program']
        
        # Student can only take courses allowed for their program
        allowed_courses = [c['id'] for c in courses if program in c['allowed_programs']]
        
        for course_id in allowed_courses:
            x[(student_id, course_id)] = pulp.LpVariable(
                f"x_{student_id}_{course_id}", cat=pulp.LpBinary
            )
    
    # Objective function: Maximize course preference satisfaction
    objective_terms = []
    for student in students:
        student_id = student['id']
        
        for course in courses:
            course_id = course['id']
            if student['program'] in course['allowed_programs']:
                # Get course preference weight (convert rank to weight)
                course_pref_rank = course_preferences.get((student_id, course_id), 3)  # Default to middle rank
                course_weight = max(6 - course_pref_rank, 1)  # Convert to weight (5 is best, 1 is worst)
                
                if (student_id, course_id) in x:
                    objective_terms.append(course_weight * x[(student_id, course_id)])
    
    prob += pulp.lpSum(objective_terms)
    
    # Constraint 1: Each student must take their mandatory courses
    for student in students:
        student_id = student['id']
        program = student['program']
        
        for course_id in mandatory_courses[program]:
            if (student_id, course_id) in x:
                prob += x[(student_id, course_id)] == 1
    
    # Constraint 2: Each student must take the required number of elective courses
    for student in students:
        student_id = student['id']
        program = student['program']
        required_electives = max_electives[program]
        
        elective_courses = [c['id'] for c in courses 
                           if c['type'] == 'elective' and program in c['allowed_programs']]
        
        if elective_courses:
            prob += pulp.lpSum(
                x.get((student_id, course_id), 0) for course_id in elective_courses
            ) == required_electives
    
    # Solve the problem
    start_time = time.time()
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    solving_time = time.time() - start_time
    
    # Extract the solution
    course_assignments = {}
    for student in students:
        student_id = student['id']
        course_assignments[student_id] = []
        
        for course in courses:
            course_id = course['id']
            if (student_id, course_id) in x and pulp.value(x[(student_id, course_id)]) == 1:
                course_assignments[student_id].append(course_id)
    
    # Calculate statistics
    total_preference = 0
    for student in students:
        student_id = student['id']
        for course_id in course_assignments[student_id]:
            course_pref_rank = course_preferences.get((student_id, course_id), 3)
            course_weight = max(6 - course_pref_rank, 1)
            total_preference += course_weight
    
    stats = {
        'status': pulp.LpStatus[prob.status],
        'obj_value': pulp.value(prob.objective),
        'total_preference': total_preference,
        'avg_preference': total_preference / len(students) if students else 0,
        'solving_time': solving_time
    }
    
    return course_assignments, stats 




def phase2_time_matching(students, courses, lab_sections, course_assignments, 
                        lab_time_preferences, time_slots, lab_capacity):
    """
    Phase 2: Assign lab times to students based on the course assignments from Phase 1.
    
    Parameters:
    -----------
    students : list of dict
        List of student information
    courses : list of dict
        List of course information
    lab_sections : list of dict
        List of lab sections with keys 'id', 'course_id', 'time_slot'
    course_assignments : dict
        Dict mapping student_id to list of assigned course_ids (from Phase 1)
    lab_time_preferences : dict
        Dict mapping (student_id, time_slot_id) to preference rank
    time_slots : dict
        Dict mapping time_slot_id to time information
    lab_capacity : int
        Maximum number of students in each lab section
        
    Returns:
    --------
    time_assignments : dict
        Dict mapping (student_id, course_id) to lab_section_id
    stats : dict
        Dict containing statistics about the assignment
    """
    # Create the ILP problem
    prob = pulp.LpProblem("TimeMatching", pulp.LpMaximize)
    
    # Decision variables - x[s,c,l] = 1 if student s is assigned to lab section l for course c
    x = {}
    
    # Create variables only for courses that have labs
    for student_id, assigned_courses in course_assignments.items():
        for course_id in assigned_courses:
            course = next(c for c in courses if c['id'] == course_id)
            
            # Only create variables for courses with labs
            if course['has_lab']:
                # Find lab sections for this course
                course_sections = [ls['id'] for ls in lab_sections if ls['course_id'] == course_id]
                
                for section_id in course_sections:
                    x[(student_id, course_id, section_id)] = pulp.LpVariable(
                        f"x_{student_id}_{course_id}_{section_id}", cat=pulp.LpBinary
                    )
    
    # Objective function: Maximize lab time preference satisfaction
    objective_terms = []
    
    for student_id, assigned_courses in course_assignments.items():
        for course_id in assigned_courses:
            course = next(c for c in courses if c['id'] == course_id)
            
            if course['has_lab']:
                for section in lab_sections:
                    if section['course_id'] == course_id:
                        section_id = section['id']
                        time_slot = section['time_slot']
                        
                        # Get time preference weight
                        time_pref_rank = lab_time_preferences.get((student_id, time_slot), 3)
                        time_weight = max(6 - time_pref_rank, 1)  # Convert to weight
                        
                        if (student_id, course_id, section_id) in x:
                            objective_terms.append(time_weight * x[(student_id, course_id, section_id)])
    
    prob += pulp.lpSum(objective_terms)
    
    # Constraint 1: Each student must be assigned to exactly one lab section for each of their 
    # assigned courses that have labs
    for student_id, assigned_courses in course_assignments.items():
        for course_id in assigned_courses:
            course = next(c for c in courses if c['id'] == course_id)
            
            if course['has_lab']:
                course_sections = [ls['id'] for ls in lab_sections if ls['course_id'] == course_id]
                
                prob += pulp.lpSum(
                    x.get((student_id, course_id, section_id), 0) for section_id in course_sections
                ) == 1
    
    # Constraint 2: Lab section capacity
    for section in lab_sections:
        section_id = section['id']
        course_id = section['course_id']
        
        # Find all students assigned to this course
        assigned_students = [student_id for student_id, courses in course_assignments.items() 
                            if course_id in courses]
        
        prob += pulp.lpSum(
            x.get((student_id, course_id, section_id), 0) for student_id in assigned_students
            if (student_id, course_id, section_id) in x
        ) <= lab_capacity
    
    # Constraint 3: No time conflicts between lab sections
    for student_id, assigned_courses in course_assignments.items():
        # Get all pairs of assigned courses that have labs
        courses_with_labs = [cid for cid in assigned_courses 
                           if next(c for c in courses if c['id'] == cid)['has_lab']]
        
        # For each time slot, ensure student is assigned to at most one lab at that time
        for time_slot_id in time_slots:
            # Get all lab sections at this time slot for the student's assigned courses
            conflicting_sections = []
            for course_id in courses_with_labs:
                sections_at_time = [ls['id'] for ls in lab_sections 
                                  if ls['course_id'] == course_id and ls['time_slot'] == time_slot_id]
                conflicting_sections.extend([(course_id, section_id) for section_id in sections_at_time])
            
            if len(conflicting_sections) >= 2:  # Only need constraint if there are at least 2 possible conflicts
                prob += pulp.lpSum(
                    x.get((student_id, course_id, section_id), 0)
                    for course_id, section_id in conflicting_sections
                    if (student_id, course_id, section_id) in x
                ) <= 1
    
    # Constraint 4: No conflicts between theory class times and lab times
    for student_id, assigned_courses in course_assignments.items():
        # For each assigned course with a theory time
        for course1_id in assigned_courses:
            course1 = next(c for c in courses if c['id'] == course1_id)
            theory_time = course1['theory_time_slot']
            
            # Check other assigned courses with labs
            for course2_id in assigned_courses:
                if course1_id != course2_id:
                    course2 = next(c for c in courses if c['id'] == course2_id)
                    
                    if course2['has_lab']:
                        # Find lab sections for course2 that conflict with course1's theory time
                        conflicting_sections = [ls['id'] for ls in lab_sections 
                                             if ls['course_id'] == course2_id and ls['time_slot'] == theory_time]
                        
                        for section_id in conflicting_sections:
                            if (student_id, course2_id, section_id) in x:
                                prob += x[(student_id, course2_id, section_id)] == 0
    
    # Solve the problem
    start_time = time.time()
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    solving_time = time.time() - start_time
    
    # Extract the solution
    time_assignments = {}
    
    for student_id, assigned_courses in course_assignments.items():
        for course_id in assigned_courses:
            course = next(c for c in courses if c['id'] == course_id)
            
            if course['has_lab']:
                # Find which lab section was assigned
                for section in lab_sections:
                    if section['course_id'] == course_id:
                        section_id = section['id']
                        if (student_id, course_id, section_id) in x and pulp.value(x[(student_id, course_id, section_id)]) == 1:
                            time_assignments[(student_id, course_id)] = {'type': 'lab', 'section_id': section_id}
            else:
                # For courses without labs
                time_assignments[(student_id, course_id)] = {'type': 'no_lab'}
    
    # Calculate statistics
    lab_assignments_count = 0
    total_preference = 0
    
    for (student_id, course_id), assignment in time_assignments.items():
        if assignment['type'] == 'lab':
            lab_assignments_count += 1
            section_id = assignment['section_id']
            section = next(s for s in lab_sections if s['id'] == section_id)
            time_slot = section['time_slot']
            time_pref_rank = lab_time_preferences.get((student_id, time_slot), 3)
            time_weight = max(6 - time_pref_rank, 1)
            total_preference += time_weight
    
    stats = {
        'status': pulp.LpStatus[prob.status],
        'obj_value': pulp.value(prob.objective),
        'total_preference': total_preference,
        'avg_preference': total_preference / lab_assignments_count if lab_assignments_count > 0 else 0,
        'solving_time': solving_time
    }
    
    return time_assignments, stats



def two_phase_assignment(students, courses, lab_sections, course_preferences, 
                        lab_time_preferences, time_slots, mandatory_courses, 
                        max_electives, lab_capacity):
    """
    Run the complete two-phase course assignment algorithm.
    
    Phase 1: Match students to courses
    Phase 2: Assign lab times based on course matches
    
    Returns:
    --------
    assignments : dict
        Dict mapping (student_id, course_id) to lab assignment details
    stats : dict
        Statistics about both phases
    """
    print("Running Phase 1: Course Matching...")
    course_assignments, phase1_stats = phase1_course_matching(
        students, courses, course_preferences, mandatory_courses, max_electives
    )
    
    print("Running Phase 2: Time Matching...")
    time_assignments, phase2_stats = phase2_time_matching(
        students, courses, lab_sections, course_assignments, 
        lab_time_preferences, time_slots, lab_capacity
    )
    
    # Combine statistics
    stats = {
        'phase1': phase1_stats,
        'phase2': phase2_stats,
        'total_solving_time': phase1_stats['solving_time'] + phase2_stats['solving_time']
    }
    
    return time_assignments, stats




def generate_test_data(num_students=15, lab_capacity=3):
    """
    Generate test data for the course assignment problem with:
    - Each course has one theory class time slot for all students
    - Each course either has 2 lab sections or no lab at all
    """
    programs = ['MPP', 'MDS', 'MIA']
    
    # Generate students
    students = []
    for i in range(num_students):
        program = programs[i % len(programs)]  # Distribute students evenly across programs
        students.append({
            'id': f's{i+1}',
            'name': f'Student {i+1}',
            'program': program
        })
    
    # Generate time slots
    time_slots = {
        't1': "Monday 9-11",
        't2': "Monday 2-4",
        't3': "Tuesday 9-11",
        't4': "Tuesday 2-4",
        't5': "Wednesday 9-11",
        't6': "Wednesday 2-4",
        't7': "Thursday 9-11",
        't8': "Thursday 2-4",
        't9': "Friday 9-11",
        't10': "Friday 2-4"
    }
    
    # Generate courses (mix of mandatory and elective, with and without labs)
    courses = []
    
    # Mandatory courses (2 per program)
    for p_idx, program in enumerate(programs):
        for j in range(2):
            theory_time_slot = random.choice(list(time_slots.keys()))
            has_lab = random.choice([True, False])  # 50% chance of having labs
            
            courses.append({
                'id': f'c{len(courses)+1}',
                'name': f'{program} Mandatory {j+1}',
                'type': 'mandatory',
                'allowed_programs': [program],
                'theory_time_slot': theory_time_slot,
                'has_lab': has_lab
            })
    
    # Elective courses (shared among programs)
    for i in range(6):  # 6 elective courses
        # Randomly choose which programs can take this elective
        allowed = []
        for program in programs:
            if random.random() > 0.3:  # 70% chance a program can take an elective
                allowed.append(program)
        
        if not allowed:  # Ensure at least one program can take the course
            allowed = [random.choice(programs)]
        
        theory_time_slot = random.choice(list(time_slots.keys()))
        has_lab = random.choice([True, False])  # 50% chance of having labs
            
        courses.append({
            'id': f'c{len(courses)+1}',
            'name': f'Elective {i+1}',
            'type': 'elective',
            'allowed_programs': allowed,
            'theory_time_slot': theory_time_slot,
            'has_lab': has_lab
        })
    
    # Generate lab sections (exactly 2 for courses that have labs)
    lab_sections = []
    for course in courses:
        if course['has_lab']:
            # Create exactly 2 lab sections for this course
            for j in range(2):
                # Make sure lab time doesn't conflict with the course's theory time
                available_slots = [ts for ts in time_slots.keys() if ts != course['theory_time_slot']]
                time_slot = random.choice(available_slots)
                
                lab_sections.append({
                    'id': f'l{len(lab_sections)+1}',
                    'course_id': course['id'],
                    'time_slot': time_slot
                })
    
    # Define mandatory courses for each program
    mandatory_courses = {program: [] for program in programs}
    for course in courses:
        if course['type'] == 'mandatory':
            for program in course['allowed_programs']:
                mandatory_courses[program].append(course['id'])
    
    # Define number of elective courses per program
    max_electives = {
        'MPP': 2,
        'MDS': 3,
        'MIA': 2
    }
    
    # Generate student preferences for courses
    course_preferences = {}
    for student in students:
        # Set preference for all courses this student can take
        for course in courses:
            if student['program'] in course['allowed_programs']:
                if course['type'] == 'mandatory':
                    # Random preference between 1-3 for mandatory courses
                    course_preferences[(student['id'], course['id'])] = random.randint(1, 3)
                else:
                    # Random preference between 1-5 for elective courses
                    course_preferences[(student['id'], course['id'])] = random.randint(1, 5)
    
    # Generate student preferences for lab times
    lab_time_preferences = {}
    for student in students:
        for time_slot_id in time_slots:
            # Random preference between 1 and 5 for time slots
            lab_time_preferences[(student['id'], time_slot_id)] = random.randint(1, 5)
    
    return {
        'students': students,
        'courses': courses,
        'lab_sections': lab_sections,
        'course_preferences': course_preferences,
        'lab_time_preferences': lab_time_preferences,
        'time_slots': time_slots,
        'mandatory_courses': mandatory_courses,
        'max_electives': max_electives,
        'lab_capacity': lab_capacity
    }

def format_results(assignments, students, courses, lab_sections, time_slots):
    """Format the assignment results into a readable dataframe"""
    results = []
    
    for student in students:
        student_id = student['id']
        
        # Get all courses for this student
        student_courses = {
            'mandatory': [],
            'elective': []
        }
        
        for (sid, course_id), assignment in assignments.items():
            if sid == student_id:
                course = next(c for c in courses if c['id'] == course_id)
                
                if assignment['type'] == 'lab':
                    # Course with lab
                    section_id = assignment['section_id']
                    section = next(s for s in lab_sections if s['id'] == section_id)
                    
                    course_info = {
                        'course_id': course_id,
                        'course_name': course['name'],
                        'has_lab': True,
                        'section_id': section_id,
                        'lab_time': time_slots[section['time_slot']],
                        'theory_time': time_slots[course['theory_time_slot']]
                    }
                else:
                    # Course without lab
                    course_info = {
                        'course_id': course_id,
                        'course_name': course['name'],
                        'has_lab': False,
                        'section_id': None,
                        'lab_time': 'No Lab',
                        'theory_time': time_slots[course['theory_time_slot']]
                    }
                
                if course['type'] == 'mandatory':
                    student_courses['mandatory'].append(course_info)
                else:
                    student_courses['elective'].append(course_info)
        
        # Format for display
        mandatory_str = ", ".join([c['course_name'] for c in student_courses['mandatory']])
        elective_str = ", ".join([c['course_name'] for c in student_courses['elective']])
        
        lab_times = []
        for c in student_courses['mandatory'] + student_courses['elective']:
            if c['has_lab']:
                lab_times.append(f"{c['course_name']}: {c['lab_time']}")
            else:
                lab_times.append(f"{c['course_name']}: No Lab")
        
        theory_times = []
        for c in student_courses['mandatory'] + student_courses['elective']:
            theory_times.append(f"{c['course_name']}: {c['theory_time']}")
        
        results.append({
            'Student ID': student_id,
            'Name': student['name'],
            'Program': student['program'],
            'Mandatory Courses': mandatory_str,
            'Elective Courses': elective_str,
            'Lab Times': " | ".join(lab_times),
            'Theory Class Times': " | ".join(theory_times)
        })
    
    return pd.DataFrame(results) 





def verify_assignment(assignments, data):
    """Verify that all constraints are met in the assignment"""
    print("\nVerifying constraints:")
    all_constraints_met = True
    
    # 1. Check mandatory course constraint
    mandatory_violations = []
    for student in data['students']:
        student_id = student['id']
        program = student['program']
        
        # Get assigned courses for this student
        assigned_courses = [course_id for (sid, course_id) in assignments.keys() if sid == student_id]
        
        # Check if all mandatory courses are assigned
        for mandatory_course in data['mandatory_courses'][program]:
            if mandatory_course not in assigned_courses:
                mandatory_violations.append((student_id, mandatory_course))
    
    if mandatory_violations:
        print(f"❌ Mandatory course constraint: {len(mandatory_violations)} violations")
        all_constraints_met = False
    else:
        print("✅ Mandatory course constraint: All students have their mandatory courses")
    
    # 2. Check elective course constraint
    elective_violations = []
    for student in data['students']:
        student_id = student['id']
        program = student['program']
        required_electives = data['max_electives'][program]
        
        # Count elective courses assigned to this student
        assigned_courses = [course_id for (sid, course_id) in assignments.keys() if sid == student_id]
        elective_courses = [cid for cid in assigned_courses 
                          if next(c for c in data['courses'] if c['id'] == cid)['type'] == 'elective']
        
        if len(elective_courses) != required_electives:
            elective_violations.append((student_id, len(elective_courses), required_electives))
    
    if elective_violations:
        print(f"❌ Elective course constraint: {len(elective_violations)} violations")
        all_constraints_met = False
    else:
        print("✅ Elective course constraint: All students have the correct number of electives")
    
    # 3. Check lab section capacity constraint
    capacity_violations = []
    for section in data['lab_sections']:
        section_id = section['id']
        
        # Count students assigned to this section
        assigned_students = [(sid, cid) for (sid, cid), assignment in assignments.items() 
                           if assignment['type'] == 'lab' and assignment['section_id'] == section_id]
        
        if len(assigned_students) > data['lab_capacity']:
            capacity_violations.append((section_id, len(assigned_students), data['lab_capacity']))
    
    if capacity_violations:
        print(f"❌ Lab capacity constraint: {len(capacity_violations)} violations")
        all_constraints_met = False
    else:
        print("✅ Lab capacity constraint: All lab sections within capacity limits")
    
    # 4. Check lab time conflict constraint
    lab_conflict_violations = []
    for student in data['students']:
        student_id = student['id']
        
        # Get all lab time slots for this student
        student_lab_slots = []
        for (sid, cid), assignment in assignments.items():
            if sid == student_id and assignment['type'] == 'lab':
                section_id = assignment['section_id']
                section = next(s for s in data['lab_sections'] if s['id'] == section_id)
                student_lab_slots.append((section['time_slot'], section_id, cid))
        
        # Check for lab time conflicts
        time_slot_count = {}
        for time_slot, _, _ in student_lab_slots:
            time_slot_count[time_slot] = time_slot_count.get(time_slot, 0) + 1
        
        conflicts = [(time_slot, count) for time_slot, count in time_slot_count.items() if count > 1]
        if conflicts:
            lab_conflict_violations.append((student_id, conflicts))
    
    if lab_conflict_violations:
        print(f"❌ Lab time conflict constraint: {len(lab_conflict_violations)} violations")
        all_constraints_met = False
    else:
        print("✅ Lab time conflict constraint: No lab time conflicts detected")
    
    # 5. Check theory class vs lab conflict constraint
    theory_lab_conflicts = []
    for student in data['students']:
        student_id = student['id']
        
        # Get all assigned courses for this student
        assigned_course_ids = [course_id for (sid, course_id) in assignments.keys() if sid == student_id]
        assigned_courses = [next(c for c in data['courses'] if c['id'] == cid) for cid in assigned_course_ids]
        
        # Get all assigned lab sections for this student
        assigned_labs = {}
        for (sid, cid), assignment in assignments.items():
            if sid == student_id and assignment['type'] == 'lab':
                section_id = assignment['section_id']
                section = next(s for s in data['lab_sections'] if s['id'] == section_id)
                assigned_labs[cid] = section['time_slot']
        
        # Check for conflicts between theory times and lab times
        for course in assigned_courses:
            theory_time = course['theory_time_slot']
            
            # Check if this theory time conflicts with any other course's lab time
            for other_cid, lab_time in assigned_labs.items():
                if course['id'] != other_cid and theory_time == lab_time:
                    theory_lab_conflicts.append((student_id, course['id'], other_cid))
    
    if theory_lab_conflicts:
        print(f"❌ Theory-lab conflict constraint: {len(theory_lab_conflicts)} violations")
        all_constraints_met = False
    else:
        print("✅ Theory-lab conflict constraint: No conflicts between theory classes and labs")
    
    return all_constraints_met

def run_test(num_students=15, lab_capacity=3):
    """Run a complete test of the two-phase course assignment algorithm"""
    print(f"Generating test data with {num_students} students and lab capacity {lab_capacity}...")
    data = generate_test_data(num_students=num_students, lab_capacity=lab_capacity)
    
    print(f"Students by program:")
    for program in ['MPP', 'MDS', 'MIA']:
        count = sum(1 for s in data['students'] if s['program'] == program)
        print(f"  - {program}: {count} students")
    
    print(f"Courses:")
    mandatory_with_lab = sum(1 for c in data['courses'] if c['type'] == 'mandatory' and c['has_lab'])
    mandatory_without_lab = sum(1 for c in data['courses'] if c['type'] == 'mandatory' and not c['has_lab'])
    elective_with_lab = sum(1 for c in data['courses'] if c['type'] == 'elective' and c['has_lab'])
    elective_without_lab = sum(1 for c in data['courses'] if c['type'] == 'elective' and not c['has_lab'])
    
    print(f"  - Mandatory with lab: {mandatory_with_lab}")
    print(f"  - Mandatory without lab: {mandatory_without_lab}")
    print(f"  - Elective with lab: {elective_with_lab}")
    print(f"  - Elective without lab: {elective_without_lab}")
    print(f"Lab sections: {len(data['lab_sections'])}")
    
    print("\nRunning two-phase assignment algorithm...")
    assignments, stats = two_phase_assignment(
        data['students'], 
        data['courses'], 
        data['lab_sections'], 
        data['course_preferences'],
        data['lab_time_preferences'],
        data['time_slots'], 
        data['mandatory_courses'], 
        data['max_electives'], 
        data['lab_capacity']
    )
    
    print(f"\nPhase 1 (Course Matching):")
    print(f"  Status: {stats['phase1']['status']}")
    print(f"  Course preference satisfaction: {stats['phase1']['avg_preference']:.2f}")
    print(f"  Solving time: {stats['phase1']['solving_time']:.2f} seconds")
    
    print(f"\nPhase 2 (Time Matching):")
    print(f"  Status: {stats['phase2']['status']}")
    print(f"  Time preference satisfaction: {stats['phase2']['avg_preference']:.2f}")
    print(f"  Solving time: {stats['phase2']['solving_time']:.2f} seconds")
    
    print(f"\nTotal solving time: {stats['total_solving_time']:.2f} seconds")
    
    # Verify the assignment
    all_constraints_met = verify_assignment(assignments, data)
    
    if all_constraints_met:
        print("\n✅ All constraints satisfied! The assignment is valid.")
    else:
        print("\n❌ Some constraints were violated. The assignment has issues.")
    
    # Format and display results
    results_df = format_results(
        assignments, 
        data['students'], 
        data['courses'], 
        data['lab_sections'], 
        data['time_slots']
    )
    
    print("\nCourse Assignment Results:")
    html_table = results_df.to_html(classes="table table-bordered", index=False)
    
    return html_table, assignments, stats, data

if __name__ == "__main__":
    # Run with 15 students and lab capacity of 3
    results_df, assignments, stats, data = run_test(num_students=15, lab_capacity=3)