from flask import Flask, render_template
import threading
import webbrowser

#Create a Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

#Function to open browser automatically
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

#Run Flask app in a separate thread
def run_app():
    app.run(debug=False, use_reloader=False)

if __name__ == "__main__":
    threading.Thread(target=run_app).start()
    open_browser()
