import os
import sys

projectpath = '/opt'
projectapppath = '/opt/sana'
if projectpath not in sys.path:
    sys.path.append(projectpath)
if projectapppath not in sys.path:
    sys.path.append(projectapppath)

os.environ['DJANGO_SETTINGS_MODULE'] = 'sana.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
