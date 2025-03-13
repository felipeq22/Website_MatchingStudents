# Website_MatchingStudents
Project for developing the website of Website of Matching students to Projects.

Backend Development 

Objective
Documentation of specific details of the backend part of the application, which includes Data Model, Matching Algorithm, and the design of API.   


Core Features
Student-course matching algorithm
Course and program structure
Enrollment and scheduling management
Started on
March 10, 2025
Last updated
March 10, 2025



Data Model  

Student
Student’s basic information:- ID, name, program, academic year 
Mapping students to their programs 
Tracking academic progress (year, credits completed) 
Program
Degree programs (MDS, MPP, MIA)
Defining degree requirements and structure of the programs:- listing the courses offered for specific programs (course catalogue) 
Program Requirement
Mapping  specific courses to program requirements
Categorizing course requirements (core, elective, etc.)
Defining minimum number and mandatory courses needed per category
Mapping of courses with faculty 
Mapping courses with faculty
Credit hours, Faculty/TA
Course Prerequisite
Defining prerequisite relationships between courses
Supporting both required and recommended prerequisites
Section
Individual class sections for each course
Tracking capacity and current enrollment
Linking to specific semester/year
Time Slot
Scheduling time
Supports complex scheduling (multiple days/times per section)
Student Preference
Capturing student’s course preferences
Including preference ranking/priority
Including preference for timing 
Completed Course
Student's academic history
To be used to verify prerequisites and track progress
Enrollment
Connects students to specific sections
Tracks enrollment status and priority


Matching Algorithm  


Matching Process:- 

Priority based matching:-  
Student Preference :- Request from students for the time slots
Program Requirement:- Mandatory course required in a program
Prerequisites chain:- Setting up the prerequisite for any course 

Constraint Satisfaction:- 
Time conflict detection:- avoiding more than one class at a time
Capacity enforcement :- Number of students allowed in a class/lab
Prerequisite verification:- Listing out courses required prior to taking any specific course 

Special Case handling:-  
Accommodating for exchange request from students 
Suggestion for alternate 
API Endpoints   

/api/students - Student management
/api/courses - Course catalog
/api/sections - Section management
/api/matching - Run matching algorithm
/api/schedule/{student_id} - View individual schedules


