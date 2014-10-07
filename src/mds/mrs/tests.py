from django.utils import unittest
from django.test.client import Client

from .openmrs import *

#openmrs_host="localhost" 
openmrs_host="demo.sana.csail.mit.edu" 
username="admin"
password="Sanamobile1"
host="http://" + openmrs_host + ":8080/openmrs/"
omrs = OpenMRS(username, password, host)
first_name = "Male"
last_name = "Patient"
gender = "M"
patient_id = "11110021"
new_patient_id = "11110059"
birthdate = "01/01/2012"
patient = { 
    "identifiers":[{
        "identifier": patient_id,
        "identifierType": DEFAULT_IDENTIFIERTYPE,
        "location": DEFAULT_LOCATION
            }],
    "person": {
        "names":[{
            "givenName": first_name,
            "familyName": last_name
            }],
        },
    "birthdate": birthdate,
        "gender": gender 
    }


class OpenMRSTests(unittest.TestCase):
    def testRun_open_close_session():        
        jsession = omrs.create_session(username, password)        
        print "Session open result: ", jsession                
        closed = omrs.delete_session()        
        print "Session closed: " , closed            

    def testRun_create_patient(self):        
        jsession = omrs.create_session(username,password)
        print "Session open result: ", jsession                        
        print "Creating Patient, ID: ", patient_id        
        data = omrs.create_patient(patient_id,first_name,
            last_name,gender,birthdate,username,password)        
        print "Patient ID:" ,patient_id, " UUID:", data        
        closed = omrs.delete_session()        
        print "Session closed: " , closed        

    def testRun_read_patient(self):        
        print "Fetching ", patient_id        
        jsession = omrs.create_session(username, password)        
        print "Session open result: ", jsession        
        response = omrs.read_patient(username, password,  patient_id)        
        print "Patient Fetch by ID:", response.read()        
        closed = omrs.delete_session()
        print "Session closed: " , closed
        
    def testRun_upload_procedure(self):
        print "TEsting procedure upload"
        phone_id = "1110001111"
        date = "12/01/2001"
        procedure_title = "Test Procedure"
        saved_procedure_id = "TEST000000001"
        responses = [{"answer": "1", 
                       "question": "Demonstrate selecting a single value.",
                       "concept": "TEST SELECT", 
                       "type": "SELECT", 
                       "id": "1"}, 
                      {"answer": "2", 
                       "question": "Demonstrate selecting a single value.",
                       "concept": "TEST SELECT", 
                       "type": "SELECT", 
                       "id": "2"}]
        files = {}
        
        response = omrs.upload_procedure(patient_id, 
                                              phone_id, 
                                              procedure_title, 
                                              saved_procedure_id, 
                                              responses,
                                              files)
        print response.read()
