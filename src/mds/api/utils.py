'''
A collection of utility functions.

Created on Dec 8, 2011

@author: Sana Dev Team
'''

import mimetypes
mimetypes.init()
import uuid

from django.conf import settings

def make_uuid():
    """ A utility to generate universally unique ids. """
    return str(uuid.uuid4())

def guess_fext(ftype):
    """ A wrapper around mimetypes.guess_extension(type,True) with additional 
        types included from settings
        Parameters:
        type
            the file type
    """
    _tmp = mimetypes.guess_extension(ftype,True)
    return settings.EXTRA_EXTENSIONS.get(ftype, 'bin') if not _tmp else _tmp