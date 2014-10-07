"""Data models for Sana Mobile Dispatch Server

:Authors: Sana dev team
:Version: 1.1
"""
import cjson
import os, mimetypes

from django.db import models
from django.conf import settings


class Client(models.Model):
    """ Some arbirary way to refer to a client."""
    name = models.CharField(max_length=255, unique=True)
    last_seen = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name
    
    def touch(self):
        self.save()

class ClientEventLog(models.Model):
    """ A log entry for client events
    
    """
    class Meta:
        app_label = 'mrs'
        unique_together = (('event_type', 'event_time'),)
    
    client = models.ForeignKey('Client')
    event_type = models.CharField(max_length=512)
    event_value = models.TextField()
    event_time = models.DateTimeField()

    encounter_reference = models.TextField()
    patient_reference = models.TextField()
    user_reference = models.TextField()

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class Patient(models.Model):
    """ Someone about whom data is collected """
    class Meta:
        app_label = 'mrs'
    name = models.CharField(max_length=512)

    # the remote record identifier for the Patient, i.e. OpenMRS ID
    remote_identifier = models.CharField(max_length=1024)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

class Procedure(models.Model):
    """ A series of steps used to collect data observations 
    """
    class Meta:
        app_label = 'mrs'
    
    title = models.CharField(max_length=255)
    procedure_guid = models.CharField(max_length=255, unique=True)
    procedure = models.TextField()
    xml = models.FileField(upload_to='procedure')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

class BinaryResource(models.Model):
    """ A binary object, stored as a file, which was collected during an 
        encounter
    """
    class Meta:
        app_label = 'mrs'
        unique_together = (('procedure', 'element_id', 'guid'),)

    def __unicode__(self):
        return "%s-%s-%s (%d/%d)" % (self.procedure.client.name,
                                   self.procedure.guid,
                                   self.element_id,
                                   self.upload_progress,
                                   self.total_size)

    # the instance of a procedure which this binary resource is associated with
    procedure = models.ForeignKey('SavedProcedure')

    # the element id to which this binary resource applies
    element_id = models.CharField(max_length=255)

    guid = models.CharField(max_length=512)

    content_type = models.CharField(max_length=255)
    data = models.FileField(upload_to='binary/%Y/%m/%d', )

    # the current number of bytes stored for the resource
    upload_progress = models.IntegerField(default=0)
    # the binary size in bytes
    total_size = models.IntegerField(default=0)

    # Whether the binary resource was uploaded to a remote queueing
    # server.
    uploaded = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    
    # Whether type will be converted before upload
    convert_before_upload = models.BooleanField(default=False)
    
    # Whether the data has been converted. Binaries which do not need to be
    # converted before upload are considered to be in a state where conversion
    # is complete 
    conversion_complete = models.BooleanField(default=True)

    def receive_completed(self):
        """ Indicates whether the client has uploaded this entire
            binary resource to the MDS. 
        """
        return self.total_size > 0 and self.total_size == self.upload_progress

    def ready_to_convert(self):
        """ Indicates whether binary is ready to be converted. Binaries which do
            not need to be converted will return False.
        """
        return (self.receive_completed() and 
                (self.convert_before_upload == True) and
                (self.conversion_complete == False))

    def ready_to_upload(self):
        """ Indicates whether binary upload and conversion are complete
        """
        return (self.receive_completed() and 
                (self.conversion_complete == True))

    def filename(self):
        return "%s_%s" % (self.procedure.guid, self.element_id)

    def flush(self):
        """ Removes any file on disk that was created for this object.
        
            Sets the path assigned to the data field to None and commits on
            successful removal
        """
        f = self.data.path
        if f and os.path.isfile(f):
            os.remove(self.data.path)
        self.save()
        
    def create_stub(self, fname=None):
        """ Creates a zero length file stub on disk
        
            fname => a filename to assign. If None it will be auto-generated.
            Sets and updates the data field on success
        """
        #TODO add auto-generate filename
        self.data = self.data.field.generate_filename(self, fname)
        path, _ = os.path.split(self.data.path)
        # make sure we have the directory structure
        if not os.path.exists(path):
            os.makedirs(path)
        # create the stub and commit if no exceptions
        open(self.data.path, "w").close()
        self.save()
            
class SavedProcedure(models.Model):
    """ An encounter, representing a completed procedure, where data has been
        collected
    """
    class Meta:
        app_label = 'mrs'
        
    def __init__(self,*pargs,**kwargs):
        models.Model.__init__(self, *pargs, **kwargs)
        
    def __unicode__(self):
        return "SavedProcedure %s %s" % (self.guid, self.created)

    guid = models.CharField(max_length=255, unique=True)

    # GUID of the procedure this is an instance of
    procedure_guid = models.CharField(max_length=512)

    # ID of the reporting phone
    client = models.ForeignKey('Client')

    # Text responses of the saved procedure
    responses = models.TextField()

    # OpenMRS login credentials for this user
    upload_username = models.CharField(max_length=512)
    upload_password = models.CharField(max_length=512)

    # Whether the saved procedure was uploaded to a remote queueing
    # server.
    uploaded = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    # EMR Encounter Number
    # Might be cleaner to make this an integer, but EMR systems in general
    # might not use an integer as the unique ID of an encounter.
    encounter = models.CharField(default="-1", max_length=512)
    
    def flush(self):
        """ Removes the responses text and files for this SavedProcedure """
        self.responses = ''
        self.save()
        if settings.FLUSH_BINARYRESOURCE:
            for br in self.binaryresource_set.all():
                br.flush();
    
class Notification(models.Model):
    """ A message to be sent
    """
    class Meta:
        app_label = 'mrs'

    # some identifier that tells us which client it is (phone #?)
    client = models.CharField(max_length=512)
    patient_id = models.CharField(max_length=512)
    procedure_id = models.CharField(max_length=512)

    message = models.TextField()
    delivered = models.BooleanField()

    def to_json(self):
        return cjson.encode({
            'phoneId': self.client,
            'message': self.message,
            'procedureId': self.procedure_id,
            'patientId': self.patient_id
            })
        
    def flush(self):
        """ Removes the message text """
        self.message = ''
        self.save()
        
class QueueElement(models.Model):
    """ An element that is being processed
    """
    class Meta:
        app_label = 'mrs'
    procedure = models.ForeignKey('Procedure')
    saved_procedure = models.ForeignKey('SavedProcedure')

    finished = models.BooleanField()

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

TIME_FORMAT = "%m/%d/%Y %H:%M:%S"

class RequestLog(models.Model):
    """
    Logging facility for requests.
    """
    class Meta:
        app_label = 'mrs'

    def __unicode__(self):
        return "%s : %s : Duration: %0.4fs" % (self.uri,
                                 self.timestamp.strftime(TIME_FORMAT),
                                 self.duration)

    # max keylength of index is 767
    uri = models.CharField(max_length=767)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    duration = models.FloatField()



class Concept(models.Model): 
    def __unicode__(self):
        return self.name

     
    name = models.CharField(max_length=255, unique=True)
    """ A short unique name."""
    
    display_name = models.CharField(max_length=255, blank=True)
    """ Optional descriptive name or text. """
    
    description = models.CharField(max_length=255, blank=True)
    
    conceptclass = models.CharField(max_length=255, blank=True)
    
    datatype = models.CharField(max_length=64,
                                choices=((x,x) for x in settings.DATATYPES),
                                default="string")
    """ The data class, i.e. string, int, etc. """
    
    mimetype = models.CharField(max_length=64,
                                choices=((x,x) for x in settings.MIMETYPES),
                                default="text/plain") 
    @property
    def is_complex(self):
        return self.datatype == 'complex' or self.datatype == 'blob'
    """ True if this concept requires file storage when used for values """
    
class Observation(models.Model):
    """ A piece of data collected about a subject during an external_id"""
    
    class Meta:  
        unique_together = (('encounter', 'node'),)

    #def __unicode__(self):
    #    return "Observation %s %s %s %s" % (self.encounter.uuid, 
    #                                           self.node,
    #                                           self.concept.name,
    #                                           str(self.value), )
    
    encounter = models.ForeignKey('SavedProcedure', to_field='guid')
    """ The instance of a procedure which this observation is associated with. """
    
    node = models.CharField(max_length=255)
    """Unique node id within the external_id as defined by the original procedure."""

    concept = models.ForeignKey('Concept', to_field='name')
    """ A dictionary entry which defines the type of information stored.""" 
    
    value_text = models.CharField(max_length=255)
    """ A textual representation of the observation data.  For observations
        which collect file data this will be the value of the absolute
        url to the file
    """
    
    value_complex = models.FileField(upload_to='binary/%Y/%m/%d', blank=True,)
    """ File object holder """
    
    def getvalue(self):
        if self.is_complex:
            return self._value_complex.path
        else:
            return self._value_text
        
    def setvalue(self,value):
        if self.is_complex:
            self._value_complex = value
            self._value_text = "complex_data" 
        else:
            return self._value_text
            
    value = property(fset=setvalue,fget=getvalue)
    """ A textual representation of the observation data.  For observations
        which collect file data this will be the value of the absolute
        url to the file
    """
    
    # next two are necessary purely for packetizing
    _complex_size = models.IntegerField(default=0)
    """ Size of complex data in bytes """
    
    _complex_progress = models.IntegerField(default=0)
    """ Bytes recieved for value_complex when packetized """
    

    @property
    def is_complex(self):
        """ Convenience wrapper around Concept.is_complex """
        if self.concept:
            return self.concept.is_complex
        else:
            False
    
    @property
    def data_type(self):
        """ Convenience wrapper around Concept.data_type """
        if self.concept:
            return self.concept.data_type
        else:
            return None
    
    def open(self, mode="w"):
        if not self.is_complex:
            raise Exception("Attempt to open file for non complex observation")
        path, _ = os.path.split(self._value_complex.path)
        # make sure we have the directory structure
        if not os.path.exists(path):
            self.create_file()
        return open(self._value_complex.path, mode)
    
    def _complex_path(self):
        name = '%s-%s' % (self.encounter.guid, self.node)
        ext = mimetypes.guess(self.concept.data_type, False)
        fname = '%s%s' % (name, ext)
        
        
    def create_file(self, append=None):
        """ Creates a zero length file stub on disk
            Parameters:
            append
                Extra string to append to file name.
        """
        name = '%s-%s' % (self.encounter.guid, self.node)
        if append:
            name += '-%s' % append
        ext = mimetypes.guess(self.concept.data_type, False)
        fname = '%s%s' % (name, ext)
        self.value_complex = self._value_complex.field.generate_filename(self, fname)
        path, _ = os.path.split(self._value_complex.path)
        # make sure we have the directory structure
        if not os.path.exists(path):
            os.makedirs(path)
            # create the stub and commit if no exceptions
            open(self._value_complex.path, "w").close()
        self.save()
    
    def complete(self):
        if self._complex_size is 0:
            return True
        else:
            return not self._complex_progress < self._complex_size

