""" Classes and utilities for talking to an OpenMRS server

:Authors: Sana Dev Team
:Version: 1.1
"""
import urllib
import cookielib
import logging
import urllib2
import cjson
import base64
import time,datetime

from django.conf import settings

from sana.api.urlrequestlib import DeleteRequest, PutRequest
from sana.mrs import MultipartPostHandler

SESSION_STATUS = u"authenticated"
SESSION_INVALID = u"Invalid auth data"
SESSION_CONTENT = "sessionId"
LIST_CONTENT  = u"results"
ERROR_CONTENT = u"error"
ERROR_MESSAGE = u"message"
ERROR_SOURCE = u"code"


REST_DATE_FMT = "%Y-%m-%d"

DEFAULT_IDENTIFIERTYPE = "8d79403a-c2cc-11de-8d13-0010c6dffd0f"
DEFAULT_LOCATION="Unknown Location"


#v=custom:(uuid,datatype:(uuid,name),conceptClass,names:ref)

class NoSessionException(Exception):
    def __init__(self):
        Exception.__init__(self,"No Open Session")

def patient_form(first_name, last_name, patient_id, gender, birthdate, location=None):
    """OpenMRS Short patient form for creating a new patient.

            Parameters    OpenMRS form field            Note
            first_name    personName.givenName          N/A
            last_name     personName.familyName         N/A
            patient_id    identifiers[0].identifier     N/A
            gender        patient.gender                M or F
            birthdate     patient.birthdate             single digits must be padded
            N/A           identifiers[0].identifierType use "2"
            N/A           identifiers[0].location       use "1"
    """
    
    location = location if location else 1
    data = {"personName.givenName": first_name,
            "personName.familyName": last_name,
            "identifiers[0].identifier": patient_id,
            "identifiers[0].preferred": "true",
            "identifiers[0].identifierType": 2,
            "identifiers[0].location": location,
            "patient.gender": gender,
            "patient.birthdate": birthdate,}
    return data

class PatientForm:
    
    def __init__(self):
        pass
    
    def to_post(self, person_id, patient_id, location=None):
        """ Webservices REST module POST data.
        
            person_id:
                The openmrs uuid
            patient_id:
                Sana created id
            
        """
        location = location if location else "Unknown Location"
        data = {"person": person_id,
                "identifiers":[{"identifier": patient_id,
                                "identifierType": "8d79403a-c2cc-11de-8d13-0010c6dffd0f",
                                "location": location }]}
        return data
        
    def from_post(self,response):
        msg = cjson.decode(response.read(), all_unicode=True)
    
        if ERROR_CONTENT in msg.keys():
            return error_reader(msg)
        else:
            return msg["uuid"]
        
    def from_get(self,response):
        msg = cjson.decode(response.read(), all_unicode=True)
    
        if ERROR_CONTENT in msg.keys():
            return error_reader(msg)
        else:
            result = []
            for p in msg["results"]:
                # TODO remove these
                #gender = p["gender"]
                #birthdate = p["birthdate"]
                #name = p["preferredName"]

                # Get person first
                person = p["person"]
                gender = person["gender"]
                birthdate = person["birthdate"]
                # get first and last name from "preferredName"
                name = person["preferredName"]
                firstname = name["givenName"]
                lastname = name["familyName"]
                # including here since we will need it later
                uuid = p["uuid"]
                patient = "%s%s%s%s%s%s" % (firstname.lower(),
                                            birthdate[0:4],
                                            birthdate[5:7],
                                            birthdate[8:10],
                                            lastname.lower(),
                                            gender.lower())
                # useful when debugging but do not expose in production
                #logging.debug("patient: %s " % patient)
                result.append(patient)

        return "".join(result)
        
class PersonForm:
    
    def to_post(self, given,family, gender,dob):
        """ Generates properly structured POST data for sending
            to the Webservices.REST module
            
            given:
                given name
            family:
                family name
            gender:
                gender(Accepts M or F as of ver 1.9.2)
            dob:
                date of birth, will accept string, date, or 
                datetime object. If it is a string, it should be formatted as
                settings.DATE_FMT
        """
        if type(dob) == str or type(dob) == unicode:
            dob = datetime.datetime.strptime(dob, settings.DATE_FMT)
            
        data = {"names":[{
                    "givenName": given,
                    "familyName": family }],
                "gender": gender,
                "birthdate": dob.strftime(REST_DATE_FMT)}
        return data
    
    def from_post(self, response):
        msg = cjson.decode(response.read(), all_unicode=True)
    
        if ERROR_CONTENT in msg.keys():
            return error_reader(msg)
        else:
            return msg["uuid"]

def rest_reader(response, reader):
    msg = cjson.decode(response.read(), all_unicode=True)
    
    if ERROR_CONTENT in msg.keys():
        return error_reader(msg)
    else:
        return reader(msg)
        
def error_reader(response, all_unicode=False):
    message = response[ERROR_CONTENT][ERROR_MESSAGE]
    return message

def patient_reader(response, all_unicode=False):
    msg = cjson.decode(response.read(), all_unicode=all_unicode)
    
    if ERROR_CONTENT in msg.keys():
        return error_reader(msg)
    else:
        result = []
        for p in msg["results"]:
            person = p["person"]
            name = person["preferredName"]
            firstname = name["givenName"]
            lastname = name["familyName"]
            gender = person["gender"]
            birthdate = person["birthdate"]
            uuid = p["uuid"]
            patient = "%s%s%s%s%s%s" % (firstname.lower(),
                                            birthdate[0:4],
                                            birthdate[5:7],
                                            birthdate[8:10],
                                            lastname.lower(),
                                            gender.lower())
            if settings.DEBUG:
                logging.debug("patient: %s " % patient)
            result.append(patient)

        return "".join(result)

class OpenMRS(object):
    """Utility class for remote communication with OpenMRS """

    def __init__(self, username,password,url):
        """Called when a new OpenMRS object is initialized.
            
        Parameters:
            username
                A valid user name for authoriztion
            password
                A valid user password for authorization
            url
                The OpenMRS host root url having the form::
                
                    http:<ip or hostname>[:8080 | 80]/openmrs/
                
                and defined in the settings.py module
        """
        self.url = url
        self.jsessionid = None
        self.opener = None
        self.username = username
        self.password = password
    
    def get_url(self, path):
        """ Constructs the full url for a request """
        url = self.url + path
        if settings.DEBUG:
            logging.debug("get_url(): " + url)
        return url
    
    # TODO Deprecate this
    def _login(self):
        loginParams = urllib.urlencode(
            {"uname": self.username,
             "pw": self.password,
             "redirect": "/openmrs",
             "refererURL": self.url+"index.htm"
             })
        try:
            logging.info("Auth check: %sloginServlet, %s" % (self.url, self.username))
            self.opener.open("%sloginServlet" % self.url, loginParams)
            logging.debug("Success: Validating with OpenMRS loginServlet")
            result = True
        except Exception, e:
            logging.debug("Error logging into OpenMRS: %s" % e)
            result = False
        return result
    
    # TODO Should really deprecate this
    def validate_credentials(self, username, password):
        """ Validates OpenMRS authorization for a user by creating and then
            immediately deleting a session.
           
        """
        result = self.create_session(username, password)
        if result:
            self.delete_session()
            return True
        else:
            return False
        
    
    def create_person(self,username,password, first_name, last_name, gender, birthdate):
        """ Creates a new Person in OpenMRS and returns the OpenMRS uuid
        """
        url = "%sws/rest/v1/person/" % self.url
        form = PersonForm()
        params = form.to_post(first_name, last_name, gender, birthdate)
        response = self.open(url,username,password,method='POST', **params )
        return form.from_post(response)
    
    def read_person(self, person_uuid, given_name=None, family_name=None):
        pass
    
    #TODO THis should be replaced entirely by read_patient
    def getPatient(self,username, password, patientid):
        """Retrieves a patient by id from OpenMRS through the REST module.

        OpenMRS url: <host> + ws/rest/v1/patient/?q={0}&v=full
        
        Parameters:
            username
                OpenMRS username
            password
                OpenMRS password
            userid
                patient identifier
           
        """ 
        url = self.get_url('ws/rest/v1/patient/?q={0}&v=full'.format(patientid))
        data = self.open(url, username, password, method='GET', data=None)
        response = patient_reader(data,all_unicode=True)
        self.delete_session()
        return response
    
    # NOTE: this doesn't work anymore with the new REST API
    # so the sync is broken. 
    # Question? Do we really want it anyway since it will not scale well
    def getAllPatients(self,username, password):
        """Retrieves all patients from OpenMRS through the REST module.

        OpenMRS url: <host> + ws/rest/v1/person/?q=
        
        NOTE: REST Webservices module will not return the full patient list
        as of 01/2013
        
        Parameters:
            username
                OpenMRS username
            password
                OpenMRS password
           
        """
        url = self.get_url('ws/rest/v1/patient/?q=&v=full')
        data = self.open(url, username, password)
        response = patient_reader(data,all_unicode=True)
        self.delete_session()
        return response
    
    def create_patient(self, patient_id, first_name, last_name, gender, 
                       birthdate, username, password, location=None):
        """Sends a post request to OpenMRS REST service to create patient.
                
            patient_id
                client generated identifier
            first_name
                patient given name
            last_name
                patient family name
            gender
                M or F
            birthdate
                patient birth date formatted as settings.DATE_FMT
            location
                should be None or a location defined in OpenMRS
                
        """
        person_uuid = self.create_person(username, password, first_name, last_name, gender, birthdate)
        url = self.get_url("ws/rest/v1/patient/")
        form = PatientForm()
        data = form.to_post(person_uuid, patient_id, location)
        response = self.open(url,username,password, method='POST', **data)
        return form.from_post(response)

    def read_patient(self, username,password, patient_id=None):
       if patient_id:
           url = self.get_url('ws/rest/v1/patient/?q={0}&v=full'.format(patient_id))
       else:
           url = self.get_url('ws/rest/v1/patient/?q={0}&v=full'.format(patient_id))
       data = self.open(url, username, password, method='GET', data=None)
       return data
       
#     return self.getPatient(username, password, patient_id)
       # else:
       #     return self.getAllPatients(username, password)
         
    # TODO This should replace upload_procedure method
    def create_encounter(self, username, password, encounter):
        pass
    
    def read_encounter(self, encounter_uuid):
        pass
    
    def update_encounter(self,encounter_uuid, data):
        pass
    
    def delete_encounter(self, encounter_uuid):
        pass
    
    # TODO Deprecate this
    def upload_procedure(self, patient_id, phone_id,
                         procedure_title, saved_procedure_id,
                         responses, files):
        """Posts an encounter to the OPenMRS encounter service through the Sana
        module
        
        OpenMRS url: <host> + moduleServlet/moca/uploadServlet
        
        OpenMRS Form Fields: ::
        
            Parameter             OpenMRS form field    Note
            phone_id              phoneId
                                  procedureDate         mm/dd/yyyy
            patient_id            patientId
            procedure_title       procedureTitle
            saved_procedure_id    caseIdentifier
            responses             questions
            
        Note: Above parameters are then encoded and posted to OpenMRS as the
        'description' field value.
            
        Binaries are attached as one parameter per binary with field name
        given as 'medImageFile-<element-id>-<index> where index correlates 
        to the position in the csv 'answer' attribute of the particular 
        procedure element
        
        Parameters:
            phone_id
                client telephone number.     
            patient_id   
                The patient identifier.
            procedure_title
                The procedure tirle.
            saved_procedure_id
                Saved procedure id.
            responses
                Encounter text data as JSON encoded text.
        """
        hasPermissions = False 
        result = False
        message = ""
        encounter = None
        response = None
        try:
            self._use_multipart_opener(self.url, self.username, self.password)
            self._login()
            if settings.LOG_DEBUG:
                logging.debug("Validating permissions to manage sana queue")

            url = "%smoduleServlet/sana/permissionsServlet" % self.url
            if settings.LOG_DEBUG:
                logging.debug("POST to: %s" % url)
            response = self.opener.open(url).read()
            resp_msg = cjson.decode(response,True)
            message = resp_msg['message']
            hasPermissions = True if resp_msg['status'] == 'OK' else False
            if settings.LOG_DEBUG:
                logging.debug("Has permissions: %s" % hasPermissions)
            if not hasPermissions:
                return result, message
            
            logging.debug("Uploading procedure")
            # NOTE: Check version format in settings matches OpenMRS version
            description = {'phoneId': str(phone_id),
                           'procedureDate': time.strftime(
                                                    settings.OPENMRS_DATE_FMT),
                           'patientId': str(patient_id),
                           'procedureTitle': str(procedure_title),
                           'caseIdentifier': str(saved_procedure_id),
                           'questions': responses}
            if settings.LOG_DEBUG:
                logging.debug("%s" % description)
            description = cjson.encode(description)
            post = {'description': str(description)}
            logging.debug("Encoded parameters, checking files.")
            # Attach a file 
            for elt in responses:
                etype = elt.get('type', None)
                eid = elt.get('id', None)
                if eid in files:
                    logging.info("Checking for files associated with %s" % eid)
                    for i,path in enumerate(files[eid]):
                        if settings.LOG_DEBUG:
                            logging.info('medImageFile-%s-%d -> %s' 
                                     % (eid, i, path))
                        post['medImageFile-%s-%d' % (eid, i)] = open(path, "rb")

            url = "%smoduleServlet/sana/uploadServlet" % self.url
            logging.debug("About to post to " + url)
            
            response = self.opener.open(url,post).read()
            print response
            if settings.LOG_DEBUG:
                logging.debug("Got result %s" % response)
                
            resp_msg = cjson.decode(response,True)
            message = resp_msg.get('message', '')
            result = True if resp_msg['status'] == 'OK' else False
            encounter = resp_msg.get('encounter', None)
            logging.debug("Done with upload")
            
        except Exception as e:
            logging.error("Exception in uploading procedure: %s" 
                          % saved_procedure_id)
            raise
        return result, message, encounter

    def create_session(self,username,password):
        """ Performs an auth check and returns the session id if successful.
        """
        try:
            logging.debug("Opening session")
            url = self.get_url("ws/rest/v1/session/")
            
            # build opener
            cookies = cookielib.CookieJar()
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, url, username, password)
            auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
            self.opener = urllib2.build_opener(auth_handler,
                    urllib2.HTTPCookieProcessor(cookies),
                    MultipartPostHandler.MultipartPostHandler)
            urllib2.install_opener(self.opener)
            req = urllib2.Request(url)
            
            # The OpenMRS REST mod still uses basic auth for now
            basic64 = lambda x,y: base64.encodestring('%s:%s' % (x, y))[:-1]
            if username and password:
                req.add_header("Authorization", "Basic %s" % basic64(username, password))
            
            # Should return an authenticated message if successful
            session = cjson.decode(self.opener.open(req).read())
            if not session["authenticated"]:
                raise Exception(u"username and password combination incorrect!")
        
            # Need this to chain additional requests
            self.jsessionid = session.get("sessionId")
            if settings.LOG_DEBUG:
                logging.debug("Webservices.REST session response: " + self.jsessionid)
            logging.debug(unicode(username) + u": username and password validated!")
            return self.jsessionid
        except :
            return None
        
    def delete_session(self):
        """ Closes an open session with an OpenMRS instance. 
        
            Throws:
                
        """ 
        url = self.get_url("ws/rest/v1/session")
        if not self.jsessionid:
            raise Exception( "No session")
        response = self.open(url, method='DELETE')
        return response.read()
                
    def open(self, url, username=None, password=None, method='GET', content="application/json",**data):
        if not self.opener or not self.jsessionid:
            self.create_session(username, password)
        
        headers={"jsessionid": self.jsessionid}
        if method == 'DELETE':
            req = DeleteRequest(url, data=data, headers=headers)
        elif method == 'PUT':
            headers["Content-Type"] = content
            req = PutRequest(url, data=data, headers=headers)
        elif method == 'POST':
            data = cjson.encode(data)
            headers["Content-Type"] = content
            req = urllib2.Request(url, data, headers=headers)
        else:
            # data should really be None for GET 
            # TODO raise exception on Data not None
            req = urllib2.Request(url)
        if settings.DEBUG:
            logging.debug("Request: %s" % req.get_full_url())
            logging.debug("...headers: %s" % req.header_items())
            logging.debug("...method: %s" % req.get_method())
        return self.opener.open(req)

    def _use_multipart_opener(self, url, username, password):
        cookies = cookielib.CookieJar()
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None,url, username, password)
        auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        self.opener = urllib2.build_opener(auth_handler,
                urllib2.HTTPCookieProcessor(cookies),
                MultipartPostHandler.MultipartPostHandler)
        urllib2.install_opener(self.opener)        

def download_procedure(self, encounter):
    # OpenMRS procedure retrieval goes here.
    # Recommend starting by making this return a test procedure.
    pass

def generateJSONDescriptionFromDict(responses, patientId, phoneId, procedureId):
    return cjson.encode(
        {'phoneId': str(phoneId),
         'patientId': str(patientId),
         'procedureId': str(procedureId),
         'questions': responses})

def sendToOpenMRS(patientId, phoneId, procedureId,
                  filePath, responses, username, password):
    """Sends procedure data to OpenMRS

    Expects:
    
        1. a valid patientId that is registered in OpenMRS already
        2. a file path to an image
        3. a QA dict of string question / answer pairs
    
    Parameters:
        patientId
            The patient id for this encounter
        phoneId
            The sending client id. Usually a telephone number.
        procedureId
            the id of the procedure used for collecting data
        filePath
            THe local path to files which will be uploaded.
        responses
            the data text collected
        username
            A username(for uploading).
        password
            A password(for uploading).
    """
    uploadToOpenMRS(
        patientId,
        filePath,
        generateJSONDescriptionFromDict(responses,
                                        patientId,
                                        phoneId,
                                        procedureId),
        settings.OPENMRS_SERVER_URL,
        username,
        password)


def uploadToOpenMRS(patientId, filePath, description, url, username, password):
    """Uploads a file to OpenMRS and tags it on a given patientId's 
    'Medical Images' tab.

    Parameters:
        patientId
            The patientId is the internal patient ID in OpenMRS, NOT the 
            "Identification Number" that one can search for in OpenMRS.
        filePath
            THe local path to files which will be uploaded.
        description
            The form data which will be sent. Does not need to be url-safe, 
            since this method encodes it as such. Double-encoding it will 
            produce non-desired output. 
        url
            The OpenMRS url. ::
        
                http://myserver.com/openmrs/
        username
            A username(for uploading).
        password
            A password(for uploading).
    
    """
    cookies = cookielib.CookieJar()

    opener = urllib2.build_opener(
        urllib2.HTTPCookieProcessor(cookies),
        MultipartPostHandler.MultipartPostHandler)
    loginParams = urllib.urlencode(
        {"uname": username,
         "pw": password,
         "redirect": "/openmrs",
         "refererURL": url+"index.htm"
         })
    opener.open("%sloginServlet" % url, loginParams)
    for cookie in cookies:
        logging.debug("Cookie: %s" % cookie)
    getParams = urllib.urlencode({'patientIdentifier': str(patientId),
                                  'imageDate': time.strftime("%m/%d/%Y"),
                                  'description': str(description)})
    postParams = {"medImageFile": open(filePath, "rb")}
    postUrl = "%smoduleServlet/gmapsimageviewer/formImageUpload?%s" % (url, getParams)
    opener.open(postUrl, postParams)
    logging.debug("Done with upload")

