# Your good Django code...
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()   # ← this sets application to Django

# ... then later this overrides it completely!
from flask import Flask
application = Flask(__name__)          # ← now application is a Flask app!

@application.route('/')                # ← and this defines the default route
def hello_world():
    return """ <html> ... Hello, World! ... """