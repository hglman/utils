__author__ = 'btuttle'

import os
import sys
import VmBoxList
import subprocess
import re
import shutil
import logger
import multiprocessing
import EPAdapter
import hashlib


examples = r"""
BAD
Line 139:20140117_020001:(14:E:\Logs\1234\) skip [20140117]E:\Logs\1234\StartupException_20140117_003531_455.log

BAD
Line 478:20140117_020005:(24:E:\var\Logs\1234\ExceptionLogBackup\) Starting

GOOD
Line 3302:20140117_030522:(20:E:\Logs\Wedge\Auto\) Failed deleting file
    [20131227_Task20_Auto.3]E:\Logs\Wedge\Auto\new_path_summary.log.12-27-2013.log.System.IO.IOException:
     The process cannot access the file 'E:\Logs\Wedge\Auto\new_path_summary.log.12-27-2013.log' because it is being used by another process.

Line 49:System.Web.Services.Protocols.SoapException: Server was unable to process request. ---> Object reference not set to an instance of an object.
matches found:1

"""

log = logger.make_logger('main', 'archiverUpdate.log', '.', 10).log


def runVmBFA():
    log(10, 'start')
    xml = subprocess.check_output("Topology VmBox %")
    log(10, 'xml returned')
    status, vmb_obj = VmBoxList.obj_wrapper(xml)
    log(10, 'vmb_obj returned')
    pool = multiprocessing.Pool(10)
    pool.map(FindArchiver(), vmb_obj.VMBox)

class FindArchiver(object):

    fa_re_obj = re.compile(r'filearchive.exe', re.IGNORECASE)

    fav_insert = r"""INSERT INTO dbo.ArchiveVersion
            ( ArchiveId, FileName, Version )
    VALUES  ( {}, -- ArchiveId - int
              '{}', -- FileName - varchar(256)
              '{}'  -- Version - varchar(256)
              )"""

    fa_insert = r"""
        INSERT INTO dbo.Archive
            ( ServerId, Path, Config )
        OUTPUT INSERTED.id
        VALUES  ( '{}', -- ServerId - varchar(39)
                  '{}', -- Path - varchar(256)
                  '{}'  -- Config - text
                  )
        """

    fa_select = r"""
        SELECT id FROM Archive WHERE ServerIp = {} and Path = {}
    """

    def __call__(self, vm_node):
        self.search_path(vm_node)

    def search_path(self, vm_node):
        """
        search box at ip, look for the pattern
        """
        drives = ['C$', 'D$', 'E$']
        if vm_node.Drive:
            drives = []
            for d in vm_node.Drive:
                drives.append(d.attrs['driveLetter'] + '$')
        log(10, drives)
        for d in drives:
            path = '\\\\' + os.path.join(vm_node.attrs["serverName"], d)
            log(10, path)
            if not os.path.exists(path):
                continue
            tree = os.walk(path)
            for dirpath, dirnames, filenames in tree:
                for item in filenames:
                    if self.fa_re_obj.match(item):
                        ver_dict = self.build_ver_dict(dirpath)
                        log(10, ver_dict)
                        config_text = self.get_config_text(dirpath)
                        log(10, config_text)
                        self.updateDBArchiver(vm_node, dirpath, ver_dict, config_text)

    def get_config_text(self, path):
        text = ""
        for f in os.listdir(path):
            if f == r'FileArchiveconfig.xml' and not text:
                with open(os.path.join(path, f)) as _f:
                    text = _f.read()
            if f == r'FileArchive.config':
                with open(os.path.join(path, f)) as _f:
                    text = _f.read()
        return text

    def get_version(self, path, f):
        fv = subprocess.check_output(u'getversionnumber.exe {}'.format(os.path.join(path, f)))
        if not fv:
            with open(os.path.join(path, f)) as _f:
                fv = hashlib.sha1(_f.read()).hexdigest()
        return fv

    def build_ver_dict(self, path):
        keeper = ('.exe', '.bat', '.cfg', 'dll', 'xml', '.config')
        ret_dict = {}
        for f in os.listdir(path):
            for i in keeper:
                if i in f:
                    ret_dict[f] = self.get_version(path, f)
        return ret_dict

    def updateDBArchiver(self, vm_node, dirpath, ver_dict, config_text):
        with EPAdapter.EPAdapter() as epa:
            fa_id = epa.exec_statement(self.fa_insert.format(vm_node.attrs["serverId"], dirpath, config_text))[0][0]
            log(10, fa_id)
            for k, v in ver_dict.iteritems():
                epa.exec_statement(self.fav_insert.format(fa_id, k, v))

class ArchiveUpdate(object):

    except_reg = re.compile(r'FindInFiles.exe -pFileArchive.log -s\(\?i:exception\)', re.I)
    except_new = r'FindInFiles.exe -pFileArchive.log -s"(?i:(?<!HydraStartup|soap)exception(?!LogBackup))"'

    def __call__(self, path):
        self.path = os.path.join(path, 'ArchiveIt.bat')
        self.exec_update()

    def file_backup(self):
        shutil.copyfile(self.path, self.path + '.backup')
        with open(self.path) as _f:
            f_string = _f.read()
        return f_string

    def get_hash(self, f_string):
        log(10, f_string)
        curr_file_hash = hashlib.new('sha1')
        curr_file_hash.update(f_string)
        return curr_file_hash.hexdigest()

    def file_write(self, f_string):
        with open(self.path, 'w') as _f:
            _f.write(f_string)

    def update(self, file_text):
        """
        wrapper for getting file string, updating file and writing everything back
        """
        file_text, num_start = self.except_reg.subn(self.except_new, file_text)
        log(10, 'Regex Subn, file text:{} num_start:{}'.format(file_text, num_start))
        if not (num_start):
            log(40, 'failed to update, not writing changes')
            return False
        return file_text

    def run_update(self, data_obj):
        curr_thread = multiprocessing.Process(target=self.update(data_obj))
        curr_thread.start()
        curr_thread.join(30)
        if curr_thread.is_alive():
            curr_thread.terminate()
            curr_thread.join()

    def exec_update(self):
        f_string = self.file_backup()
        old_hash = self.get_hash(f_string)
        log(20, r'Old Hash:{}'.format(old_hash))
        file_text = self.update(f_string)
        if file_text:
            new_hash = self.get_hash(file_text)
            self.file_write(file_text)


if __name__ == '__main__':
    runVmBFA()
