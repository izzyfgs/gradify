import os
from django.core.wsgi import get_wsgi_application

# Replace 'gradify.settings' with the actual name of your settings folder 
# if it's different, but based on your file path, this is correct.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gradify.settings')

application = get_wsgi_application()