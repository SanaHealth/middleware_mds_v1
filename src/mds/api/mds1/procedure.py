'''
Utils for handling old procedure scheme.

Created on Dec 12, 2011

@author: Sana Dev Team
'''
from xml.etree import ElementTree
from xml.etree.ElementTree import parse

deprecated = ('patientEnrolled',
              "patientId",
              "patientGender",
              'patientFirstName',
              'patientLastName',
              'patientBirthdateDay',
              'patientBirthdateMonth',
              'patientBirthdateYear',
              "patientIdNew",
              "patientGenderNew",
              'patientFirstNameNew',
              'patientLastNameNew',
              'patientBirthdateDayNew',
              'patientBirthdateMonthNew',
              'patientBirthdateYearNew',)
""" Deprecated terms not used within observations """


LCOMPLEX_TYPES = { 'PICTURE': 'image/jpeg',
                   'SOUND': 'audio/3gpp',
                   'VIDEO': 'video/3gpp',
                   'BINARYFILE': 'application/octet-stream'}

def strip_deprecated_observations(observations):
    """ Removes old bio glomming in the observation dict 
        Parameters:
        observations
            A dictionary of observations.
    """
    _obs = {}
    #_obs = dict([(lambda x: (k,v) for k not in deprecated)(observations)])
    for k,v in observations.items():
        if k not in deprecated:
            _obs[k] = v 
    return _obs

def element2obs(obs, allow_null=False):
    """ Remaps the old format to new api Observation model for a single 
        observation. Returns a dictionary, not an observation instance.
    """
    # Should only be one
    
    _obs = {}
    #For now we require non-empty strings
    if obs['answer']:
        _obs['value'] = obs['answer']
    else:
        return {}
    node = obs.keys()[0]
    _obs['node'] = node
    _obs['concept'] = obs['concept']
    return _obs

def elements2obs(observations, allow_null=False):
    """ Remaps the old format to new api Observation model. Returns only the 
        text dictionary, not the actual observations.
    """
    _obs_set = {}
    for k,v in observations.items():
        _obs = {}
        #For now we require non-empty strings
        if v['answer']:
            _obs['value'] = v['answer']
        else:
            continue
        _obs['node'] = k
        _obs['concept'] = v['concept']
        _obs_set[k] = _obs
    return _obs_set