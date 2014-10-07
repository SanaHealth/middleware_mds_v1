"""Sana mDS Django admin interface

:Authors: Sana dev team
:Version: 1.1
"""

from django.contrib import admin
from sana.mrs.models import Patient,Procedure,BinaryResource,SavedProcedure,Notification,QueueElement,RequestLog,ClientEventLog
from sana.mrs.api import maybe_upload_procedure

class ProcedureAdmin(admin.ModelAdmin):
    pass

class ClientEventLogAdmin(admin.ModelAdmin):
    list_display = ('client', 'event_time', 'event_type', 'event_value', 'encounter_reference', 'patient_reference', 'user_reference',)
    list_filter = ('event_time', 'event_type', 'encounter_reference', 'patient_reference', 'user_reference',)
    date_hierarchy = 'event_time'
    # exclude = ('created', 'modified',)

def resend(request,queryset):
    ''' Checks whether  zero, or more, SavedProcedure objects selected
        in the admin interface are ready to POST to the backend EMR and
        executes the POST if they are. 
    '''
    for sp in queryset:
        try:
            maybe_upload_procedure(sp)
        except:
            pass

resend.short_description = "Resend Selected to EMR"

class SavedProcedureAdmin(admin.ModelAdmin):
    actions = [resend,]

admin.site.register(Procedure)
admin.site.register(Patient)
admin.site.register(BinaryResource)
admin.site.register(SavedProcedure, SavedProcedureAdmin)
admin.site.register(Notification)
admin.site.register(QueueElement)
admin.site.register(RequestLog)
admin.site.register(ClientEventLog, ClientEventLogAdmin)
