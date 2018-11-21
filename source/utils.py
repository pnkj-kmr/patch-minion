from flask import make_response
import string
import json
import time
import os
import sys

# DEBUG = True
DEBUG = False

ROOT_PATH = os.getcwd()
PATCH_PATH = ROOT_PATH + os.sep + 'patches'
if not os.path.exists(PATCH_PATH):
    os.makedirs(PATCH_PATH)
# Creating logs folder
if not os.path.exists(ROOT_PATH + os.sep + 'logs'):
    os.makedirs(ROOT_PATH + os.sep + 'logs')


JSON_MIME_TYPE = 'application/json'
def json_response(data='', status=200, headers=None):
    headers = headers or {}
    if 'Content-Type' not in headers:
        headers['Content-Type'] = JSON_MIME_TYPE
    return make_response(data, status, headers)

def safe_int(val):
    try:
        return int(val)
    except:
        try:return int(float(val))
        except:pass
    return 0

def iif(a,b,c):
    if a:return b
    else:return c

def splitRight(s, delimiter = ',') :
    i = string.rfind(s, delimiter)
    if i < 0 :
        return (s, "")
    return (s[:i], s[i + len(delimiter):])

def splitLeft(s, delimiter = ',') :
    i = string.find(s, delimiter)
    if i < 0 :
        return (s, "")
    return (s[:i], s[i + len(delimiter):])
    
def readODBC(filename="odbc.ini"):
    try :
        f = open(filename, "rb")
        lines = map(string.strip, f.readlines())
        f.close()
    except :
        return {}
    ret = {}
    for line in lines :
        if line != "" and line[0] != '#':
            a, v = splitLeft(line, "=")
            ret[a.strip()] = v.strip()
    return ret

def start_service(app_name):
    """
    function help to start the service for LINUX based system
    by running cmd as
    service <app_name> start
    on terminal
    """
    pass

def stop_service(app_name):
    """
    function help to stop the service for LINUX based system
    by running cmd as
    service <app_name> stop
    on terminal
    """
    pass

def restart_service(app_name):
    """
    function help to restart the service for LINUX based system
    by running cmd as
    service <app_name> restart
    on terminal
    """
    pass
