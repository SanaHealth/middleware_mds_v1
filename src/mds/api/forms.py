'''
Created on Nov 21, 2011

@author: Sana Development Team
'''
from django import forms

from sana.mrs.models import *


class ClientForm(forms.ModelForm):
    """ A simple Client form
    """
    class Meta:
        model = Client
        
        
class ProcedureForm(forms.ModelForm):
    """ A simple procedure form
    """
    class Meta:
        model = Procedure
        excludes = ('xml')
        

        
        
class NotificationForm(forms.ModelForm):
    """ A simple Notification form """
    class Meta:
        model = Notification
    
class BinaryPacketForm(forms.ModelForm):
    class Meta:
        model = BinaryResource
        
class RequestLogForm(forms.ModelForm):
    class Meta:
        model = RequestLog