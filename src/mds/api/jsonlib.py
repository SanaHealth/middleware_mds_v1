""" 
Convenience wrappers to ensure basic JSON encoding and decoding
regardless of whether cjson is available

@author: Sana Development
"""
import sys
try:
    import cjson
except:
    import json

# sets flag for whether we are using cjson or default json
_CJSON = True if 'cjson' in sys.modules else False
    
def encode(obj):
    """ Encodes a Python obj into a JSON string
    """
    if _CJSON:
        return cjson.encode(obj)
    else:
        return json.dumps(obj)

def decode(obj, all_unicode=True):
    """ Decodes a JSON formatted string or unicode obj inot a Python
        object
        
        all_unicode: 
            specifies how to convert the strings in the JSON 
            representation into python objects. If it is False, 
            it will return strings everywhere possible
            and unicode objects only where necessary, else it 
            will return unicode objects everywhere.
    """
    if _CJSON:
        return cjson.decode(obj, all_unicode=all_unicode)
    else:
        encoding = 'UTF-8' if all_unicode else None
        return json.loads(obj,encoding=encoding)
    
    
def _test(use_json=False):
    
    print "_CJSON", _CJSON
    
    obj1 = u'{"key1":"value1", "key2": 2}'
    dobj1 = decode(obj1)
    print dobj1
    eobj1 = encode(dobj1)
    print obj1, eobj1
    # Should be True
    print obj1 == eobj1
    
    obj2 = {u"key1":u"value1", u"key2": 2}
    eobj2 = encode(obj2)
    print eobj2
    dobj2 = decode(eobj2)
    print obj2, dobj2
    # May be True or False due to unordered dict keys
    print obj2 == dobj2
    
    
        