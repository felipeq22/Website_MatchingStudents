import time
from itertools import product

def maunal_ilp(objective_terms, constraints, variables):
    """
    A brute-force ILP solver that finds the best solution by iterating through all possible assignments.
    """
    best_solution = None
    best_value = float('-inf')
    
    # Generate all possible binary assignments
    for assignment in product([0, 1], repeat=len(variables)):
        solution = dict(zip(variables, assignment))
        
        # Check constraints
        if all(eval(constraint, {}, solution) for constraint in constraints):
            value = sum(coef * solution[var] for var, coef in objective_terms.items())
            if value > best_value:
                best_value = value
                best_solution = solution
    
    return best_solution, best_value

def phase1_course_matching(students, courses, course_preferences, 
                          mandatory_courses, max_electives):
    """
    Phase 1: Match students to courses manually.
    """
    course_assignments = {}
    total_preference = 0
    
    # Decision variables and constraints
    variables = {}
    constraints = []
    objective_terms = {}
    
    for student in students:
        student_id = student['id']
        program = student['program']
        allowed_courses = [c['id'] for c in courses if program in c['allowed_programs']]
        
        for course_id in allowed_courses:
            var_name = f"x_{student_id}_{course_id}"
            variables[var_name] = 0  # Binary variable (0 or 1)
            
            # Assign objective function weight (preference-based)
            course_pref_rank = course_preferences.get((student_id, course_id), 3)
            course_weight = max(6 - course_pref_rank, 1)
            objective_terms[var_name] = course_weight
            
        # Constraint: Mandatory courses must be taken
        for course_id in mandatory_courses.get(program, []):
            constraints.append(f"{variables[f'x_{student_id}_{course_id}']} == 1")
        
        # Constraint: Must take required number of electives
        elective_courses = [c['id'] for c in courses if c['type'] == 'elective' and program in c['allowed_programs']]
        required_electives = max_electives.get(program, 0)
        elective_vars = [f"x_{student_id}_{course_id}" for course_id in elective_courses]
        constraints.append(f"sum([{', '.join(elective_vars)}]) == {required_electives}")
    
    # Solve manually
    start_time = time.time()
    best_solution, best_value = maunal_ilp(objective_terms, constraints, variables)
    solving_time = time.time() - start_time
    
    # Extract assignments from best solution
    for student in students:
        student_id = student['id']
        course_assignments[student_id] = [course_id for course_id in allowed_courses 
                                          if best_solution.get(f"x_{student_id}_{course_id}", 0) == 1]
    
    # Calculate total preference score
    total_preference = best_value
    
    stats = {
        'total_preference': total_preference,
        'avg_preference': total_preference / len(students) if students else 0,
        'solving_time': solving_time
    }
    
    return course_assignments, stats
