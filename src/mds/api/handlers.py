from __future__ import with_statement
import logging
import traceback
import sys
from StringIO import StringIO

from django import forms
from django.forms.models import modelform_factory
from django.conf import settings
from django.shortcuts import render_to_response

from lxml import etree

from piston.handler import BaseHandler
from piston import resource
from piston.utils import rc, validate#, decorator

from sana.mrs.models import Procedure, RequestLog
from sana.mrs.util import enable_logging
from sana.api.forms import *
from django.template import RequestContext

dtd = etree.DTD(file=file(settings.PROCEDURE_DTD,'r+b'))

class XMLValidationHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')
    model = Procedure
    exclude = ('created', 'modified',)
    
    #@validate
    def create(self,request):#,*args,**kwargs):
        msg = dict(request.POST)
        try:
            xml = msg['text'][0]
            lines = [x for x in xml.split("\n")]
            try:
                exml = etree.XML(str(xml))
                if dtd.validate(exml):
                    return "..........ok!"
                else:
                    error_list = [ { 'line': x[1],'message':x[6] } for x in [ str(y).split(":") for y in list(dtd.error_log)]]
                    return render_to_response("xml/errors.html", 
                                             {'error_list': error_list})
            except etree.LxmlError as e:
                l = [x for x in str(e.message).split(",")] if (e.message and len(e.message)) > 0  else [u"Empty line",u"Add text", u"1", ]
                return render_to_response("xml/errors.html", 
                                         {'error_list': [ {'line': l[2].strip("line "), "message": l[0] + ", " +l[1]}]})
        except:
            return  sys.exc_info()
            
    @enable_logging
    def read(self,request, uuid=None, m=None):
        query = dict(request.GET)
        try:
            if m:
                manifest = u'<manifest>'
                return Procedure.objects.all()
            elif uuid:
                p = Procedure.objects.filter(procedure_guid__exact=uuid)[0]
                with open(p.xml.path, 'rb') as f:
                    xml = f.read()
                return xml
            else:
                return  modelform_factory(self.model)
        except:
            return "FAIL"
        return "??????????"            

class ManifestHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')
    model = Procedure
    exclude = ('created', 'modified',)
    
    #@validate
    def create(self,request,*args,**kwargs):
        pass
    
    
    
    def read(self,request, uuid=None):
        try:
            if not uuid:
                manifest = u'<manifest>'
                return Procedure.objects.all()
            else:
                p = Procedure.objects.filter(procedure_guid__exact=uuid)[0]
                with open(p.xml.path, 'rb') as f:
                    xml = f.read()
                return xml
        except:
            return sys.exc_info()
            #return rc.NOT_FOUND


class BaseDispatchHandler(BaseHandler):
    """ 
       Base handler for api model objects following basic CRUD approach using 
       django-piston api. Extending classes must specify:
       
           model
               Sana api model class
           v_form
               ModelForm used for validating
               
       Additionally, extending classes may specify:
           
           allowed_methods
               CRUD methods which will be accepted
    """
    
    @validate('POST')
    def create(self,request):
        """ POST request method. 
            Parameters:
                request
                    a form based http POST request
        """
        new_obj = request.form.save()
        return render_to_response("sanctuary/form.html",
                                  {'form':request.form },
                                  RequestContext(request))
        
    @validate('GET')
    def read(self,request, *args, **kwargs):
        """ GET request method for retrieving existing records.
            Parameters:
                request
                    an http GET request
                args
                    slug for identifying a record
        """
        query = dict(request.REQUEST.items())
        if not query.get('meta',0):
            return dict(request.META)
        context = RequestContext(request)
        try:
            klass = getattr(self.__class__, 'model')
            form_klass = getattr(self.__class__, 'v_form')
            if request.form.data:
                obj = klass.objects.get(**query)#request.form.data)
                form = form_klass(instance=object)
            else:
                form = form_klass()
            return render_to_response("form.html", 
                                      {'form':form },
                                      context_instance=context)
        except:
            typ, val, tb = sys.exc_info()
            # debugging prints remove prior to release
            #for t in traceback.format_tb(tb):
            # Return empty form
            return render_to_response("form.html", 
                                      {'form':request.form },
                                      context_instance=context)
        
    @validate('PUT')
    def update(self,request):
        """ PUT request method for updating existing records.
            Parameters
                request
                    an http PUT request
        """
        return render_to_response("form.html", 
                                  {'form':request.form },
                                  RequestContext(request))
    
    @validate('DELETE')
    def delete(self,request, *args):
        """ DELETE request method for deleting existing records.
            Parameters
                request
                    an http DELETE request
                args
                    placeholder for slug used to identify record
        """
        return render_to_response("form.html", 
                                  {'form':request.form },
                                  RequestContext(request))

    
class RequestLogHandler(BaseDispatchHandler):
    allowed_methods = ('GET')
    model = RequestLog
    v_form = RequestLogForm
    
    #@validate('GET')
    #def read(self, request, page):
#	return self.request(page=page)
    
    def read(self, request, *args, **kwargs):

        query = dict(request.GET.items())
        page = int(query.get('page', 1 ))
        page_size = int(query.get('page_size', 20))
        rate = int(query.get('refresh', 5))

        log_list = RequestLog.objects.all().order_by('-timestamp')
        log_count = log_list.count()
        page_count = int( log_count / page_size) + 1
        if log_count > page_size:
            page_range = range(1, page_count) if page_count > 1 else range (0,1) 
            object_list = log_list[((page-1)*page_size):page*page_size ]
        else:
            page_range = range(0,1)
            object_list = log_list
        return render_to_response('logging/index.html', 
				 {'object_list': object_list,
				  'page_range': page_range,
				  'page_size': page_size,
				  'page': page }) 

class RequestLogTableHandler(BaseDispatchHandler):
    allowed_methods = ('GET')
    model = RequestLog
    v_form = RequestLogForm
    
    #@validate('GET')
    #def read(self, request, page):
#	return self.request(page=page)
    
    def read(self, request, *args, **kwars):
        query = dict(request.GET.items())
        page_size = int(query.get('page_size', 20))
        page = int(query.get('page',1))
        rate = int(query.get('refresh', 5))
        log_list = RequestLog.objects.all().order_by('-timestamp')
        log_count = log_list.count()
        page_count = int( log_count / page_size) + 1
        
        if log_count > page_size:
            page_range = range(1, page_count) if page_count > 1 else range (0,1)
            object_list = log_list[((page-1)*page_size):page*page_size ]
        else:
            page_range = range(0,1)
            object_list = log_list        
        return render_to_response('logging/list.html', 
				 {'object_list': object_list,
				  'page_range': page_range,
				  'page_size': page_size,
				  'page': page,}) 
