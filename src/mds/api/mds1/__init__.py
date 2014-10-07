'''
Backwards compatibility code.

Created on Dec 8, 2011

@author: Sana Dev Team
'''

__all__ = ( 'ApiMap')

class ApiMap:
    """ Abstract class which provides mapping objects between APIs. """
    
    def field_map(self, version=None):
        """ Returns a dict of key mappings from the object version to another.
            
            Parameters:
            version
                The version to map to. Implementations should default to the 
                value of settings.API_VERSION
        """
        pass
    
    def py_map(self, version=None):
        """ Maps an object instance into a different API version. Returns
            a dict with the fields of the new class as keys.
            
            Parameters:
            version
                The version to map to. Implementations should default to the 
                value of settings.API_VERSION 
        """
        pass