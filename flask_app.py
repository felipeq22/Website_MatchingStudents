#Created libraries
#from algorithm import StudentCourseMatchingAlgorithm
#from courses import Courses
#from students import Student

#Helper libraries
from flask import Flask, render_template, request, redirect, url_for, session
import threading
import webbrowser
import algorithm
import pandas as pd 

#Create a Flask app
app = Flask(__name__)
app.secret_key = 'your_unique_secret_key'

USERNAME = 'admin'
PASSWORD = 'password123'

@app.route("/", methods = ['GET', 'POST'])
@app.route('/login', methods = ['GET', 'POST'])
def login():
    error = None
    username = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
    
        if username == USERNAME and password == PASSWORD:
            session['user'] = username
            return redirect(url_for('home'))
        
        else:
            error = "Invalid username or password."
    
    return render_template('login.html', error=error, username = username)

@app.route("/home")
def home():
    if 'user' in session:

        return render_template("home.html")
    else:
        return redirect(url_for('login'))


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
            df = pd.read_csv('backend/student.csv')
            
            student_name = request.form.get('student_name')
            program = request.form.get('program')
            
            if student_name and program:
                
                last_id =df['student_id'].iloc[-1]
                new_row = [last_id + 1, student_name , program, 1, 2]
                new_df = pd.DataFrame([new_row], columns = df.columns)
                df = pd.concat([df, new_df], ignore_index=True)

                df.to_csv('backend/student.csv', index=False)
            
            output = df.to_html(classes='table table-bordered', index=False)
        except Exception as e:
            output = f"<p style='color:red;'>Error: {str(e)}</p>"
            
    return render_template('demo.html', output = output)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/walk_through')
def walk_through():
    return render_template('walk_through.html')
    
def about():
    return render_template('about.html')

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
