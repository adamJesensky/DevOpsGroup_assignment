# Import the Flask class from the flask library
from flask import Flask

# Create an instance of the Flask class.
# __name__ is a special Python variable that gets the name of the current module.
# Flask uses this to know where to look for resources like templates and static files.
app = Flask(__name__)

# Define a route for the root URL ('/').
# This decorator tells Flask that the hello() function should be called
# when a user accesses the main page of the web app.
@app.route('/')
def hello():
    # This function returns the string that will be displayed in the browser.
    return "Hello, DevOpsGroup!"

# This block of code ensures that the development server is run only when
# the script is executed directly (not when it's imported as a module).
if __name__ == '__main__':
    # Run the Flask application.
    # host='0.0.0.0' makes the server publicly available, which is crucial for Docker
    # as it allows connections from outside the container.
    # port=5000 specifies the port the server will listen on.
    app.run(host='0.0.0.0', port=5000, debug=True)