"""
Convenience wrappers around urllib2 Request

@author: Sana Development
"""
import urllib2
        
class DeleteRequest(urllib2.Request):
    """ Convenience wrapper for urllib2.Request with DELETE method """
    def __init__(self,url,data=None,headers={},origin_req_host=None, 
                 unverifiable=False):
        urllib2.Request.__init__(self, url, data, headers,
                 origin_req_host, unverifiable)
        
    def get_method(self):
        return 'DELETE'
    
class PutRequest(urllib2.Request):
    """ Convenience wrapper for urllib2.Request with PUT method """
    def __init__(self,url,data=None,headers={},origin_req_host=None, 
                    unverifiable=False):
        urllib2.Request.__init__(self, url, data, headers,
                 origin_req_host, unverifiable)
        
    def get_method(self):
        return 'PUT'   