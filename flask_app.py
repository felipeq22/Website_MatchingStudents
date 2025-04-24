#Created libraries
#from algorithm import StudentCourseMatchingAlgorithm
#from courses import Courses
#from students import Student

#Helper libraries
from flask import Flask, render_template, request
import threading
import webbrowser
import algorithm 

#Create a Flask app
app = Flask(__name__)

@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")

@app.route('/student_demo')
def student_demo():
    return render_template('student_demo.html')

@app.route('/course_assignation', methods=['GET', 'POST'])
def course_assignation():
    return render_template('course_assignation.html')

@app.route('/demo', methods = ['GET', 'POST'])
def demo():
    output = None
    if request.method == 'POST':
        try:
            num_students = int(request.form.get('num_students', 15))
            lab_capacity = int(request.form.get('lab_capacity', 3))

            output, assignments, stats, data = algorithm.run_test(
                num_students=num_students,
                lab_capacity=lab_capacity
            )
            
        except Exception as e:
            output = f"<p style='color:red;'>Error: {str(e)}</p>"
            
    return render_template('demo.html', output = output)

@app.route('/classes')
def classes():
    return render_template('classes.html')

#Function to open browser automatically
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

#Run Flask app in a separate thread
def run_app():
    app.run(debug=False, use_reloader=False)

if __name__ == "__main__":  
    app.run(debug=True)
#    threading.Thread(target=run_app).start()
#    open_browser()
