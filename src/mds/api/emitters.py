from piston.emitters import Emitter
from piston.utils import rc
from django.http import HttpResponse

class HTMLEmitter(Emitter):
    
    def render (self, request):
        data = self.construct()
        resp = rc.ALL_OK
        resp.write(data)
        return  resp
        
Emitter.register('html', HTMLEmitter, 'text/html')