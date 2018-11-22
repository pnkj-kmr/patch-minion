#!/usr/bin/python
__license__     = "PATCH MINION"
__version__     = "1.0"
__author__      = "Pankaj (EIMS-032)"
__email__       = "pankaj.k@everest-ims.com"
__copyright__   = "Copyright 2018, EverestIMS Technologies Pvt Ltd"
__status__      = "Production/Development"
from utils import *
import shutil

""" 
        MODULE IS WRITTEN FOR LINUX BASED PLATFORM
"""

"""
return response defination
response = {
    "status": "success/fail"
    "msg" : "<Name of action>"
    "desc" : "<ERROR MESSAGE DESCRIPTION>"
    "list" : [<ABC>, ...]
}
"""
"""
patch_config = {
    u'patchtype': 0, u'name': u'PORTAL', u'descr': u'Portal Patching', u'creationtime': u'2018-10-26T15:17:38.981861', 
    u'buildno': u'20181031', u'version': u'5.0.23', u'lastupdatetime': u'2018-10-26T15:17:38.981816', 
    u'id': 2, u'isdeleted': 0,
    u'apply_rollback': 0,
    u'apply_with': 3,
    }
app_config  = {
    u'apptype': 0, u'status': u'', 'loc': u'/opt/portal/source', 'name': u'Portal', 'service': u'portal', 
    'progress_severity': 'severity_3', 'ip': u'192.168.50.78', 'creationtime': '2018-10-29T10:32:50.510028', 
    'port': 8080, 'buildno': u'20180912', 'version': u'5.0.21', 'iscompleted': False, 
    'lastupdatetime': '2018-10-29T10:32:50.509995', 'id': 5, 'isdeleted': 0, 
    'progress_status': 'Inprogress'
}
data = {'patch':patch_config, 'app': app_config}

requested data as
data = {'data': json.dumps(data).encode('base64')}
"""

application_list = {}

application_types = {
    0 : "Everest",
    1 : "Portal",
    2 : "SD",
    3 : "NCCM",
}

patch_app_actions = {
    1: 'Patching & Restart App',
    2: 'Patching Only',
    3: 'Stop App Only',
    4: 'Start App Only',
    5: 'Restart App Only',
    6: 'Patching & Stop App',
}

# ########################################
# # defining the thread based decorator as
# from threading import Thread
# def application(function):
#     def decorator(*args, **kwargs):
#         t = Thread(target=function, args=args, kwargs=kwargs)
#         t.daemon = True
#         t.start()
#     return decorator
# ########################################


def get_running_patch_status(request, logger):
    """ Retrun the running patch status
    """
    return application_list

def patch(request, logger, PatchInfoDB):
    """
    Main patch method with will perform patching activity
    """
    data_ret = {}
    # extacing the data of post request
    logger.info("Extracting Post Request Data")
    data = request.json
    request_content = data.get('data')
    raw_data_dict = json.loads(str(request_content).decode('base64'))
    # print ">>>data_dict",raw_data_dict
    data_dict = {}
    for key, value in raw_data_dict.items():
        if type(value) == type({}):
            data_dict[str(key)] = {}
            for k1, v1 in value.items():
                data_dict[str(key)][str(k1)] = v1
        else:
            data_dict[str(key)] = value
    # print "1>>>data_dict",data_dict
    logger.debug("Data >> %s\nData Raw>>%s "%(data_dict, data))
    # initiating application_list
    application_list[data_dict.get('app', {}).get('name', '')] = []
    app_action = safe_int(data_dict.get('patch', {}).get('apply_with', 0))
    if not (0 < app_action < 7):
        logger.debug("Patch Application Action is not proper found - %s" % app_action)
        return 400, {
            "status": "fail",
            "msg": "Patch Application Action is not proper. Apply again.",
            "desc": "",
            "list": []
            }

    if app_action in (1, 2, 6):
        logger.info("Validating Patch Request")
        # Validating the requested data
        error = validate_patch_request(data_dict, logger)
        if error.get('status') != 'success':
            logger.debug("Error found into patch request as %s" % error)
            return 400, error
        
        logger.info("Verifying Patch Request")
        error = verifying_patch(data_dict, logger, DatabaseTable=PatchInfoDB)
        if error.get('status') != 'success':
            logger.debug("Error found into patch verify as %s" % error)
            return 400, error

        # Applying patch at detincation
        logger.info("Applying Patch at destination")
        error = applying_patch(data_dict, logger)
        if error.get('status') != 'success':
            logger.debug("Error found into patch applying as %s" % error)
            return 400, error
        else:
            data_ret["list"] = error.get('list', [])

    # triggering the application service 
    logger.info("Application actions")
    error = application_actions(app_action, data_dict, logger)
    # logger.info("Application actions triggered.")
    if error.get('status') != 'success':
        logger.debug("Error found into applying application actions as %s" % error)
        return 400, error

    desc_ = str(patch_app_actions.get(app_action, "Unknown")).upper()
    data_ret.update({
        "status" : "success",
        "msg" : "Task is executed successfully.",
        "desc" : "Task action has been taken as %s" % desc_,
    })
    logger.info("Exiting with status %s" % data)
    return 201, data_ret

def validate_patch_request(data_dict, logger):
    """ Validating requested data
    """
    ret = {}
    ret["status"] = "fail"
    ret["status_code"] = -1
    try:
        logger.info("Entering into validate_patch_request function")
        # print ">>>>data_dict",type(data_dict),data_dict
        patch_config = data_dict.get('patch', {})
        if not safe_int(patch_config.get('id')):
            ret['msg'] = "Patch is not proper. Apply again."
            ret['desc'] = ""
            ret['list'] = []
            logger.debug("Error in validation as %s" % ret)
            return ret
        app_config = data_dict.get('app', {})
        if not app_config.get('loc') or not app_config.get('name') or not app_config.get('service'):
            ret['msg'] = "Patch Instance is not proper. Apply again."
            ret['desc'] = ""
            ret['list'] = []
            logger.debug("Error in validation as %s" % ret)
            return ret
        if patch_config.get('patchtype') != app_config.get('apptype'):
            ret['msg'] = "Patch type and Application type is not matching. Apply again."
            ret['desc'] = ""
            ret['list'] = []
            logger.debug("Error in validation as %s" % ret)
            return ret
        # status map
        application_list.setdefault(app_config.get('name'), []).append({
            "msg" : "Application patch validation",
            "status" : "Completed",
            "status_code" : 1,
        })
        logger.info("Exiting from validate_patch_request function")
        ret["status"] = "success"
        ret["status_code"] = 1
    except Exception,e:
        print ">>>>Exception,e",Exception,e
        # exc_type, exc_obj, exc_tb = sys.exc_info()
        # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        # print ">>>", exc_type, fname, exc_tb.tb_lineno
        logger.error("Validating Patch Request %s" % str(e))
        ret['msg'] = "Exception occured at validating request"
        ret['desc'] = str(e)
        ret['list'] = []
    return ret

def verifying_patch(data_dict, logger, DatabaseTable):
    """ Verifying the patch detail
    """
    # Patch.query.filter_by(id=0).first()
    ret = {}
    ret["status"] = "fail"
    ret["status_code"] = -1
    try:
        logger.info("Entering into verifying_patch function")
        # print ">>>>data_dict",type(data_dict),data_dict
        patch_config = data_dict.get('patch', {})
        app_config = data_dict.get('app', {})

        patchId = safe_int(patch_config.get('id'))
        # Getting patch text from DB
        try:
            patchObj = DatabaseTable.query.filter_by(id=patchId).first()
            patchId_DB = patchObj.id
        except Exception,e:
            logger.error("Verifying Patch DB Error %s" % str(e))
            ret['msg'] = "Request Patch is not available in DB"
            ret['desc'] = str(e)
            ret['list'] = []
            return ret
        if patchId_DB != patchId:
            logger.error("Verifying Patch DB Id Error")
            ret['msg'] = "Requested Patch is not matching with DB Patch"
            ret['desc'] = ""
            ret['list'] = []
            return ret

        print ">>>patch_config",patch_config
        app_name = "%s" % str(app_config.get('name','App')).replace(' ','')
        file_name = "%s" % str(patch_config.get('name','Patch')).replace(' ','')
        # print ">>>file_name",file_name
        if int(patch_config.get('apply_rollback', 0)):
            # gettting rollback patch
            file_name += '__rollback.tar.gz'
            patch_text = patchObj.rpatch
        else:
            file_name += '.tar.gz'
            patch_text = patchObj.patch
        # print "\n\npatchObj",patchObj.id
        # Writing into file
        if not os.path.exists(PATCH_PATH + os.sep + app_name):
            os.makedirs(PATCH_PATH + os.sep + app_name)
        f_patch_path = PATCH_PATH + os.sep + app_name + os.sep + file_name
        # print ">>f_patch_path",f_patch_path
        file_ptr = open(f_patch_path, "wb")
        file_ptr.write(patch_text.decode('base64'))
        file_ptr.close()
        print ">>>>> file creation... DONE"

        # Verifying patch files
        patch_file_dict = get_patch_files(app_name, file_name, logger)
        if patch_file_dict.has_key('files') and patch_file_dict['files']:
            print ">>> files ",patch_file_dict
            # pass
        else:
            logger.info("Verifying Patch Files")
            ret['msg'] = "Patch File %s having issue with extraction." % file_name
            ret['desc'] = "Details as %s" % str(patch_file_dict)
            ret['list'] = []
            return ret
        # status map
        application_list.setdefault(app_config.get('name'), []).append({
            "msg" : "Application patch verification",
            "status" : "Completed",
            "status_code" : 1,
        })
        logger.info("Exiting from verifying_patch function")
        ret["status"] = "success"
        ret["status_code"] = 1
    except Exception,e:
        print ">>>>Exception,e",Exception,e
        # exc_type, exc_obj, exc_tb = sys.exc_info()
        # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        # print ">>>", exc_type, fname, exc_tb.tb_lineno
        logger.error("Verifying Patch Request %s" % str(e))
        ret['msg'] = "Exception occured at verifying request"
        ret['desc'] = str(e)
        ret['list'] = []
    return ret

def get_patch_files(appname, filename, logger, isExtract=True):
    """function helps us patch file list
    """
    ret = {}
    try:
        name = PATCH_PATH + os.sep + appname + os.sep + filename
        patch_extract_dir = PATCH_PATH + os.sep + appname + os.sep + 'source' + os.sep
        if os.path.isfile(name):
            # removing patch dir if there as --> <path>everest/patches/source
            # print "1>>",os.listdir(patch_path)
            cmd_result = 0
            if isExtract:
                try:shutil.rmtree(patch_extract_dir)
                except:pass
                # print "2>>",os.listdir(patch_path)
                cmd = "tar -zxvf %s -C %s" % (name, PATCH_PATH + os.sep + appname)
                print ">>>cmd",cmd
                cmd_result = os.system(cmd)
            # print "3>>",os.listdir(patch_path)
            if cmd_result != 0:
                ret["patch"] = filename
            else:
                ret["patch"] = filename
                # files = os.listdir(patch_extract_dir)
                # files = filter(lambda a:a, files)
                files = []
                for rootdir_, dirs, files_ in os.walk(patch_extract_dir):
                    for file_ in files_:
                        # files.append(rootdir_ + os.sep + file_)
                        file_p = rootdir_.replace(PATCH_PATH + os.sep + appname + os.sep, '')
                        if file_p.endswith(os.sep):
                            file_p = file_p[:-len(os.sep)]
                        files.append(file_p + os.sep + file_)
                if files:
                    ret["files"] = files
    except Exception, e:
        print ">>>>Exception,e",Exception,e
        # exc_type, exc_obj, exc_tb = sys.exc_info()
        # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        # print ">>>", exc_type, fname, exc_tb.tb_lineno
        logger.error("Verifying-2 Patch Request %s" % str(e))
    return ret

def applying_patch(data_dict, logger):
    """function helps to apply patch at destination
    """
    # Patch.query.filter_by(id=0).first()
    ret = {}
    ret["status"] = "fail"
    ret["status_code"] = -1
    try:
        logger.info("Entering into applying_patch function")
        logger.debug("Data dict given %s " % data_dict)
        # print ">>>>data_dict",type(data_dict),data_dict
        patch_config = data_dict.get('patch', {})
        app_config = data_dict.get('app', {})
        # status map
        application_list.setdefault(app_config.get('name'), []).append({
            "msg" : "Application patch applying triggered for %s" % app_config.get('name'),
            "status" : "Started",
            "status_code" : 0
        })

        # print ">>>patch_config",patch_config
        app_name = "%s" % str(app_config.get('name','App')).replace(' ','')
        patch_path = PATCH_PATH + os.sep + app_name + os.sep
        file_name = "%s" % str(patch_config.get('name','Patch')).replace(' ','')
        # print ">>>file_name",file_name
        if patch_config.get('apply_rollback', False):
            # gettting rollback patch
            file_name += '__rollback.tar.gz'
        else:
            file_name += '.tar.gz'
        # getting all patch files list
        patch_file_dict = get_patch_files(app_name, file_name, logger, isExtract=False)
        if patch_file_dict.has_key('files') and patch_file_dict['files']:
            print ">>> files ",patch_file_dict
            # pass
        else:
            logger.info("Verifying Patch Files")
            ret['msg'] = "Patch File %s having issue with extraction." % file_name
            ret['desc'] = "Details as %s" % str(patch_file_dict)
            ret['list'] = []
            return ret

        # Verifying the app destination 
        # print ">>>>>>>>>app_config",app_config
        application_loc = app_config.get('loc')
        if application_loc.endswith(os.sep):
            application_loc = application_loc[:len(os.sep)]
        ## TESTING
        # application_loc = '/opt/projects/portald_old/source'
        application_loc = str(os.sep).join(map(lambda a:a, application_loc.split('/')))
        logger.debug("App Loc given %s " % application_loc)
        # print ">>application_loc",application_loc
        if not os.path.exists(application_loc):
            ret['msg'] = "App (%s) location is not proper." % app_name
            ret['desc'] = "Details as %s" % str(application_loc)
            ret['list'] = []
            return ret

        # Moving patch file from patches to applicaiton source folder by taking backups as well
        cmd_list = []
        ret['list'] = []
        backup_dir = application_loc + os.sep + 'patch_backups' + os.sep
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        for file_ in patch_file_dict['files']:
            cmd_result = -1
            # aborting source folder
            file_name = splitLeft(file_,os.sep)[-1]
            app_inner_dir = splitRight(file_name, os.sep)
            if file_name.endswith(app_inner_dir[0]):
                app_inner_dir = ''
            else:
                app_inner_dir = app_inner_dir[0]
            if app_inner_dir:
                # creting dirs inside the back folder
                if not os.path.exists(backup_dir + app_inner_dir):
                    os.makedirs(backup_dir + app_inner_dir)
            file_alias = time.strftime("%Y%m%d%H%M%S",time.localtime())
            # print ">>file_name",file_name
            # print ">>app_inner_dir",app_inner_dir
            logger.debug("File Dirs Alais >> %s %s %s" % (file_name, app_inner_dir, file_alias))
            # setting with proper location
            patch_file_loc = patch_path + file_
            logger.debug("Patch Loc %s " % patch_file_loc)
            # print ">>>>patch_file_loc",patch_file_loc
            app_file_loc = application_loc + os.sep + file_name
            logger.debug("App Loc %s " % app_file_loc)
            # print ">>>app_file_loc",app_file_loc
            # checking file pyc or not
            py_check_ = ""
            if app_file_loc.endswith('pyc'):
                py_check_ = app_file_loc[:-1]
            if py_check_:
                # wrting py file mv to patch_backup
                if os.path.isfile(py_check_):
                    cmd = "cp -rf %s %s && rm -rf %s" % (
                        py_check_, 
                        backup_dir + file_name + '__' + file_alias, 
                        py_check_)
                    cmd_list.append(cmd)
                    logger.debug("Executing patch cmd $ %s" % cmd)
                    # print ">>> cmd $", cmd
                    cmd_result = os.system(cmd)
                    logger.debug("Executing patch cmd result $ %s" % cmd_result)
            if os.path.isfile(app_file_loc):
                cmd = "cp -rf %s %s && cp -rf %s %s" % (
                    app_file_loc,
                    backup_dir + file_name + '__' + file_alias,
                    patch_file_loc,
                    application_loc + os.sep + app_inner_dir 
                )
            else:
                cmd = "cp -rf %s %s" % (
                    patch_file_loc,
                    application_loc + os.sep + app_inner_dir
                )
            cmd_list.append(cmd)
            logger.debug("Executing patch cmd $ %s" % cmd)
            # print ">>> cmd $",cmd
            cmd_result = os.system(cmd)
            logger.debug("Executing patch cmd result $ %s" % cmd_result)
            if cmd_result == 0:
                ret['list'].append(file_)
        # TESTING
        # for cmd in cmd_list:
        #     print ">> $", cmd
        # print "\n>>>file1 ",len(patch_file_dict['files']),patch_file_dict['files']
        # print "\n>>>file2 ",len(ret['list']),ret['list']
        logger.info("Executed CMDs >> %s"  % cmd_list)
        if len(patch_file_dict['files']) != len(ret['list']):
            ret['msg'] = "Patch (%s) file merged get failed" % patch_config.get('name', 'Patch')
            ret['desc'] = "Moved file only as %s" % str(ret['list']).replace("'", "").replace('"', '')
            ret['list'] = patch_file_dict['files']
            return ret
        
        # status map
        application_list.setdefault(app_config.get('name'), []).append({
            "msg" : "Application patch applied",
            "status" : "Completed",
            "status_code" : 1
        })
        logger.info("Exiting from applying_patch function")
        ret["status"] = "success"
        ret["status_code"] = 1
    except Exception,e:
        print ">>>>Exception,e",Exception,e
        # exc_type, exc_obj, exc_tb = sys.exc_info()
        # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        # print ">>>", exc_type, fname, exc_tb.tb_lineno
        logger.error("Applying Patch Request %s" % str(e))
        ret['msg'] = "Exception occured at applying request"
        ret['desc'] = str(e)
        ret['list'] = []
    return ret

# @application
def application_actions(action, data_dict, logger):
    """ Function helps to start/stop/restart the application
    """
    ret = {}
    ret["status"] = "fail"
    ret["status_code"] = -1
    try:
        logger.info("Entering into application_actions function")
        logger.debug("Data dict given %s " % data_dict)
        app_config = data_dict.get('app', {})

        logger.info("%s application is getting proceed" % application_types.get(app_config.get('type')))
        # EVEREST APPLICATION
        if app_config.get('apptype') == 0:
            error = everest_action(action, app_config, logger)
        # EVEREST PORTAL APPLICATION
        elif app_config.get('apptype') == 1:
            error = portal_action(action, app_config, logger)
        # SD APPLICATION
        elif app_config.get('apptype') == 2:
            error = sd_action(action, app_config, logger)
        # NCCM APPLICATION
        elif app_config.get('apptype') == 3:
            error = nccm_action(action, app_config, logger)
        else:
            application_list.setdefault(app_config.get('name'), []).append({
                "msg" : "Application type is not matched.",
                "status" : "Failed",
                "status_code" : -1,
            })
            error = {
                "msg" : "Application action type is not matched - %s." % application_types.get(app_config.get('apptype'), "UNKNOWN"),
                "status" : "Failed",
                "status_code" : -1,
            }
        if error:
            return error

        application_list.setdefault(app_config.get('name'), []).append({
                "msg" : "Application patching is completed.",
                "status" : "COMPLETED",
                "status_code" : 1,
            })
        ret['msg'] = "Application patching is completed."
        ret['status_code'] = 1
        ret["status"] = "success"
        logger.info("Exiting from application_actions function")
    except Exception,e:
        print ">>>>Exception,e",Exception,e
        # exc_type, exc_obj, exc_tb = sys.exc_info()
        # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        # print ">>>", exc_type, fname, exc_tb.tb_lineno
        logger.error("Exception in application_actions %s" % str(e))
        ret['msg'] = "Exception occured at applying application action"
        ret['desc'] = str(e)
        ret['list'] = []
    return ret

def everest_action(action, app_config, logger):
    """ Funciton helps to start/stop/restart the Everest
    """
    ret = {}
    ret["status"] = "fail"
    ret["status_code"] = -1
    try:
        logger.info("Entering into everest_action function")
        cmd_result = -1
        default_sleep = 120 #seconds
        application_list.setdefault(app_config.get('name'), []).append({
            "msg" : "Application action (%s) is triggered."%action,
            "status" : "...",
            "status_code" : 0
        })
        ret['msg'] = "Application action (%s) is triggered."%action
        service_name = str(app_config.get('service')).strip()
        if action in [3, 6]:
            # applicaiton stop 
            cmd_result = stop_service(service_name)
            logger.info("App stopping with status %s" % (cmd_result))
            application_list.setdefault(app_config.get('name'), []).append({
                "msg" : "Application is stopped.",
                "status" : "Stopped",
                "status_code" : 1,
                "desc" : "Application stopped with status %s" % (cmd_result),
            })
            ret['msg'] = "Application is stopped with status %s" % (cmd_result)

        elif action in [4]:
            # applicaiton start 
            cmd_result = start_service(service_name)
            logger.info("App starting with status %s" % (cmd_result))
            application_list.setdefault(app_config.get('name'), []).append({
                "msg" : "Application is started. Refer app url <http://%s:%s>" % (app_config.get('ip'), app_config.get('port')),
                "status" : "Started",
                "status_code" : 1,
                "desc" : "Application started with status %s" % (cmd_result),
            })
            ret['msg'] = "Application is started with status %s" % (cmd_result)

        elif action in [1, 5]:
            ## NEED TO IMPLETED URL LEVEL RESTART
            # TODO
            # restarting application
            # stopping
            cmd_result = stop_service(service_name)
            logger.info("App stopping with status %s" % (cmd_result))
            # setting sleep time 
            if safe_int(app_config.get('sleep')):
                default_sleep = safe_int(app_config.get('sleep'))
            time.sleep(default_sleep)
            # starting
            cmd_result = start_service(service_name)
            logger.info("App starting with status %s" % (cmd_result))
            application_list.setdefault(app_config.get('name'), []).append({
                "msg" : "Application is restarted. Refer app url <http://%s:%s>" % (app_config.get('ip'), app_config.get('port')),
                "status" : "Restarted",
                "status_code" : 1,
                "desc" : "Application restarted with status %s" % (cmd_result),
            })
            ret['msg'] = "Application is restarted with %s. Refer app url <http://%s:%s>" % (cmd_result, app_config.get('ip'), app_config.get('port'))

        logger.info("Exiting from everest_action function")
        ret['status_code'] = 1
        ret["status"] = "success"
    except Exception,e:
        print ">>>>Exception,e",Exception,e
        # exc_type, exc_obj, exc_tb = sys.exc_info()
        # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        # print ">>>", exc_type, fname, exc_tb.tb_lineno
        logger.error("Exception in everest_action %s" % str(e))
        ret['msg'] = "Exception occured at applying - application action"
        ret['desc'] = str(e)
        ret['list'] = []
    return ret

def portal_action(action, app_config, logger):
    """ Funciton helps to start/stop/restart the Portal
    """
    ret = {}
    ret["status"] = "fail"
    ret["status_code"] = -1
    try:
        logger.info("Entering into portal_action function")
        cmd_result = -1
        application_list.setdefault(app_config.get('name'), []).append({
            "msg" : "Application action (%s) is triggered."%action,
            "status" : "...",
            "status_code" : 0
        })
        ret['msg'] = "Application action (%s) is triggered."%action
        service_name = str(app_config.get('service')).strip()
        if action in [3, 6]:
            # applicaiton stop 
            cmd_result = stop_service(service_name)
            logger.info("App stopping with status %s" % (cmd_result))
            application_list.setdefault(app_config.get('name'), []).append({
                "msg" : "Application is stopped.",
                "status" : "Stopped",
                "status_code" : 1,
                "desc" : "Application stopped with status %s" % (cmd_result),
            })
            ret['msg'] = "Application is stopped with status %s" % (cmd_result)

        elif action in [4]:
            # applicaiton start
            cmd_result = start_service(service_name)
            logger.info("App starting with status %s" % (cmd_result))
            application_list.setdefault(app_config.get('name'), []).append({
                "msg" : "Application is started. Refer app url <http://%s:%s>" % (app_config.get('ip'), app_config.get('port')),
                "status" : "Started",
                "status_code" : 1,
                "desc" : "Application started with status %s" % (cmd_result),
            })
            ret['msg'] = "Application is started with status %s" % (cmd_result)

        elif action in [1, 5]:
            # restarting application
            cmd_result = restart_service(service_name)
            logger.info("App restarting with status %s" % (cmd_result))
            application_list.setdefault(app_config.get('name'), []).append({
                "msg" : "Application is restarted. Refer app url <http://%s:%s>" % (app_config.get('ip'), app_config.get('port')),
                "status" : "Restarted",
                "status_code" : 1,
                "desc" : "Application restarted with status %s" % (cmd_result),
            })
            ret['msg'] = "Application is restarted with %s. Refer app url <http://%s:%s>" % (cmd_result, app_config.get('ip'), app_config.get('port'))

        logger.info("Exiting from portal_action function")
        ret['status_code'] = 1
        ret["status"] = "success"
    except Exception,e:
        print ">>>>Exception,e",Exception,e
        # exc_type, exc_obj, exc_tb = sys.exc_info()
        # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        # print ">>>", exc_type, fname, exc_tb.tb_lineno
        logger.error("Exception in portal_action %s" % str(e))
        ret['msg'] = "Exception occured at applying - application action"
        ret['desc'] = str(e)
        ret['list'] = []
    return ret

def sd_action(action, app_config, logger):
    """ Funciton helps to start/stop/restart the SD
    """
    return {
            "msg" : "NOT DEVELOPED YET",
            "status" : "Failed",
            "status_code" : -1,
        }
    
def nccm_action(action, app_config, logger):
    """ Funciton helps to start/stop/restart the NCCM
    """
    return {
            "msg" : "NOT DEVELOPED YET",
            "status" : "Failed",
            "status_code" : -1,
        }



