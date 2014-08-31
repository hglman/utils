__author__ = 'btuttle'
import os
import hashlib
import shutil
import datetime
import API.sql.helper as sql_helper
import logging
import subprocess
import multiprocessing, threading
import re
import Queue

def make_logger(file_name, log_path, level):
    logging.addLevelName(2,'Main')
    _f = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%m/%d/%Y %H:%M:%S')
    date = datetime.datetime.now()
    _hm = logging.FileHandler(os.path.join(log_path,
        date.strftime('%Y-%m-%d_%H-%M-%S_') + file_name))
    _hm.setFormatter(_f)
    _hm.setLevel(2)
    _l = logging.getLogger('main')
    _l.setLevel(level)
    _l.addHandler(_hm)

    return _l

log = make_logger("DSUpdate.log", ".", 2).log


#Utility pulls batch locations from Enterprise Monitor as set by batch messaging

c_data = {}
batch_location_query = """
SELECT DISTINCT db.dbName, srv.serverName, HostBoxIP, HostBoxPath FROM dbo.BatchImport bim
INNER JOIN dbo.DBTest db ON bim.databaseId = db.id
INNER JOIN dbo.ServerTest srv ON db.serverId = srv.id
WHERE Patindex ('[0-9]%.%[0-9]%.%[0-9]%.%[0-9]',bim.HostBoxIP) != 0 AND HostBoxIP IS NOT NULL
ORDER BY dbName, serverName
"""

def batch_pre_update():
    run_update_from_SQL('Batch.exe', '.', file_push, batch_location_query)
    run_update_from_SQL('BatchImportPre.bat', '.', StartFinishPreUpdate, batch_location_query)

def run_update_from_SQL(file_to_update, local_path_to_update, update_function, query):
    log(2, "Starting Update")
    log(2, "Opening SQL Connection")
    conn = sql_helper.sql_conn_obj(c_data)
    result, details = conn.connect()
    if not result:
        log(2, "Connection failed, update will return. {}".format(details))
        return False
    log(2, "Connection Established")
    log(2, "Looking up Batch Locations")
    result, details = conn.execute(query)
    if not result:
        log(2, "Unable to get batch locations, update will return. {}".format(details))
        return False
    log(2, "Batch location lookup complete.")
    log(2, "Begin processing Update")
    update_function(details, file_to_update, local_path_to_update)
    #add in reporting back to the database
    conn.shutdown()
    log(2, "End processing Update")
    
def run_update_from_file(file_to_update, local_path_to_update, update_function, source_file):
    log(2, "Starting Update")
    log(2, "Opening Source File")
    with open(source_file) as _f:
        log(2, "Begin processing Update")
        update_function(_f, file_to_update, local_path_to_update)
        #add in reporting back to the database
        conn.shutdown()
        log(2, "End processing Update")
    
def get_hash(curr_file):
        curr_file_hash = hashlib.new('sha1')
        for line in curr_file:
            curr_file_hash.update(line)
        return curr_file_hash.hexdigest()

def exist_test(curr_path_file, curr_name_file):
    """
    Will test for
    access to the path
    ability to open file
    hash of the file
    version of the file
    """
    curr_file_good = None
    curr_file_hash = None
    version = None
    path_file_good = False
    try:
        path_file_good = os.path.exists(curr_path_file)
        path = os.path.join(curr_path_file, curr_name_file)
        curr_file = open(path)
        curr_file_good = False
        curr_file_hash = get_hash(curr_file)
        curr_file.close()
        version = subprocess.check_output(u'getversionnumber.exe {}'.format(path))
    except Exception as why:
        curr_file_good = why
    return (path_file_good, curr_file_good, curr_file_hash, version)
    
def line_to_windows(details, file_to_update, local_path_to_update):
    for db_name, server_name, host_box_ip, host_box_path in details:
        log(2, "Running update on {}".format(db_name))
        host_box_path = host_box_path.replace(':', '$', 1)
        remote_path = '\\\\' + os.path.join(host_box_ip, host_box_path)
        init_exist_result = exist_test(remote_path, file_to_update)
        log(2, "Initial exist result, path: {}, open:{}, hash:{}, version:{}".format(*init_exist_result))
        if not init_exist_result[0] or init_exist_result[1]:
            log(2, "File not found, will send file.")
        try:
            log(2, "Attempting to rebuild")
            with open(os.path.join(remote_path, file_to_update)) as _f:
                with open(os.path.join(remote_path, file_to_update + '.new'), 'w') as _fnew:
                    for line in _f:
                        _fnew.write(line)
            shutil.copy(os.path.join(remote_path, file_to_update), os.path.join(remote_path, file_to_update + '.backup'))
            shutil.copy(os.path.join(remote_path, file_to_update + '.new'), os.path.join(remote_path, file_to_update))
            log(2, "Copy Success")
        except (IOError, OSError) as why:
            log(2, "Copy Failed, error:{}".format(why))
        post_exist_result = exist_test(remote_path, file_to_update)
        log(2, "Post exist result, path: {}, open:{}, hash:{}, version:{}".format(*post_exist_result))

def file_push(details, file_to_update, local_path_to_update):
    for db_name, server_name, host_box_ip, host_box_path in details:
        log(2, "Running update on {}".format(db_name))
        host_box_path = host_box_path.replace(':', '$', 1)
        remote_path = '\\\\' + os.path.join(host_box_ip, host_box_path)
        init_exist_result = exist_test(remote_path, file_to_update)
        log(2, "Initial exist result, path: {}, open:{}, hash:{}, version:{}".format(*init_exist_result))
        if not init_exist_result[0] or init_exist_result[1]:
            log(2, "File not found, will send file.")
        try:
            log(2, "Attempting to copy")
            shutil.copy(os.path.join(local_path_to_update, file_to_update), remote_path)
            log(2, "Copy Success")
        except (IOError, OSError) as why:
            log(2, "Copy Failed, error:{}".format(why))
        post_exist_result = exist_test(remote_path, file_to_update)
        log(2, "Post exist result, path: {}, open:{}, hash:{}, version:{}".format(*post_exist_result))

class StartFinishPreUpdate(object):

    def __init__(self, details, file_to_update, local_path_to_update):
        self.msg_pattern = re.compile('/dailypy:\".+?\"|/lgcfg:\".+?\"|/paibf.+?:\".+?\"', re.M|re.I|re.S)
        self.start_pattern = re.compile('^batch\.?e?x?e?[ \t]+?/start(?!.*?/sendData)', re.I|re.M)
        self.start_replacement = r'Batch /start {} /sendData'
        self.finish_pattern = re.compile('^exit\s*', re.I|re.M)
        self.finish_replacement = r'Batch /finish {} /sendData\nEXIT' #sodrnuk
        self.exec_update(details, file_to_update)

    def update_pre(self, new_path_file, name_file):
        """
        update BatchImportPre.bat to include start and finish flags
        """
        try:
            #spawn thread, time it and kill when too long
            log(2, 'Enter update_pre, new_path_file:{},  name_file:{}'.format(new_path_file, name_file))
            path = os.path.join(new_path_file, name_file)
            try:
                f = open(path)
                f_string = f.read()
                f.close()
                shutil.copyfile(path, path + '.backup')
            except (IOError, OSError) as no_I_am_not_mad:
                log(2, 'YOLO:{}'.format(no_I_am_not_mad))
                return
            msg_result = self.msg_pattern.search(f_string)
            if msg_result:
                #need to check if it worked, roll back if fail
                f_string, num_start = self.start_pattern.subn(self.start_replacement.format(msg_result.group()), f_string)
                f_string, num_finish = self.finish_pattern.subn(self.finish_replacement.format(msg_result.group()), f_string)
                if not (num_start * num_finish):
                    log(2, "Update failed, rolling back, start:{}, finish:{}".format(num_start, num_finish))
                    return
                out_file = open(path, 'w')
                out_file.write(f_string)
                out_file.close()
                log(2, 'Pre Update Complete')
            else:
                log(2, "Could not find db connection flag in pre file")
                return
        except (IOError, OSError) as why:
            log(2, "File Open Error, error:{}".format(why))
            return

    def exec_update(self, details, file_to_update):
        log(2, "details:{}, file_to_update:{}".format(details, file_to_update))
        for db_name, server_name, host_box_ip, host_box_path in details:
            log(2, "db_name:{}, server_name:{}, host_box_ip:{} host_box_path:{}".format(
                db_name, server_name, host_box_ip, host_box_path))
            host_box_path = host_box_path.replace(':', '$', 1)
            remote_path = '\\\\' + os.path.join(host_box_ip, host_box_path)
            curr_thread = multiprocessing.Process(target=self.update_pre(
                    remote_path, file_to_update))
            curr_thread.start()
            curr_thread.join(30)
            if curr_thread.is_alive():
                curr_thread.terminate()
                curr_thread.join()

    def yolo(self):
        print("ErikLovesThoseHats.dprk")
