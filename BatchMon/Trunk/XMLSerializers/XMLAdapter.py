__author__ = 'btuttle'
import DatabaseAndServer
import API.sql.helper as sql_helper
import BatchThreshold
import logging
import batchHistorical
import traceback
import BatchImportCurrentState

log = logging.getLogger('main').log

class XMLToFile(object):
    """
    class to simplify doing partial write as the final xml is built
    """

    def __init__(self, file_name, tag):
        self.file_name = file_name
        self.tag = tag

    def __enter__(self):
        """
        open file, write in start tag for whole xml block
        """
        self.f = open(self.file_name, 'w')
        self.f.write('<{}>'.format(self.tag))
        return self.f

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        write out the closing tag, then pass over the __exit__ for files
        """
        try:
            self.f.write('</{}>'.format(self.tag))
        finally:
            self.f.__exit__(exc_type, exc_val, exc_tb)


class XMLAdapter(object):
    """
    class smooths over pushing and pulling xml form the database
    and serializing it to objects
    """

    c_data = {}

    def __enter__(self):
        self.conn = self.get_DB_conn()
        return self


    def __exit__(self, type, value, tb):
        if type or value or tb:
            log(50, 'XMLAdapter {} {} {}'.format(type, value, traceback.extract_tb(tb)))
        self.conn.shutdown()

    def get_DB_conn(self):
        log(30, "Opening SQL Connection")
        conn = sql_helper.sql_conn_obj(self.c_data)
        result, details = conn.connect()
        if not result:
            log(50, "Connection failed, update will return. {}".format(details))
            return False
        log(30, "Connection Established")
        return conn

    def exec_sp(self, conn, sp_name, parameter_list):
        log(30, "exec_sp Lookup")
        result, detail = conn.execute_sp_odbc(sp_name, parameter_list)
        if not result:
            log(50, "Unable to exec {}, update will return. {}".format(sp_name, detail))
            return False
        log(20, "exec_sp lookup complete.")
        return detail

    def get_bh_obj(self, dbName):
        """
        For calling from external class when you do not need the
        raw xml for debugging
        """
        bh_xml = self.get_batchHistorical_XML(dbName)
        return self.get_batchHistorical_obj(bh_xml)

    def get_batchHistorical_XML(self, dbName):
        log(30, "Batch Historical Lookup, dbName:{}".format(dbName))
        detail = self.exec_sp(self.conn, 'get_BatchHistoricalResult', [dbName])
        xml = ''
        for part in detail:
            xml += part[0]
        log(30, "Batch Historical lookup complete.")
        return xml

    def get_batchHistorical_obj(self, bh_xml):
        log(20, "start batchHistorical.obj_wrapper")
        status, bh_obj = batchHistorical.obj_wrapper(bh_xml)
        log(10, "bh_obj: {}".format(bh_obj))
        log(20, "finish batchHistorical.obj_wrapper")
        return bh_obj
        
    def set_BatchImportThreshold_tbl(self, th_file):
        log(20, "Start send threshold to UpdateBatchThreshold sp")
        detail = self.exec_sp(self.conn, 'UpdateBatchThreshold', [th_file.read()])
        log(20, "Finish send threshold to UpdateBatchThreshold sp")
    
    def get_dbs_obj(self):
        """
        For calling from external class when you do not need the
        raw xml for debugging
        """
        dbs_xml = self.get_DatabaseAndServer_XML()
        return self.get_DatabaseAndServer_obj(dbs_xml)


    def get_DatabaseAndServer_XML(self):
        log(30, "DatabaseAndServer Lookup")
        details = self.exec_sp(self.conn, 'get_DatabaseAndServer', [])
        xml = ''
        for part in details:
            xml += part[0]
        log(20, "DatabaseAndServer lookup complete.")
        return xml

    def get_DatabaseAndServer_obj(self, bh_xml):
        log(30, "start DatabaseAndServers.obj_wrapper")
        status, dbs_obj = DatabaseAndServer.obj_wrapper(bh_xml)
        log(10, "bh_obj: {}".format(dbs_obj))
        log(30, "finish DatabaseAndServer.obj_wrapper")
        return dbs_obj

    def get_bth_obj(self, dbName):
        bth_xml = self.get_BatchThreshold_XML(dbName )
        return self.get_BatchThreshold_obj(bth_xml)

    def get_BatchThreshold_XML(self, dbName):
        log(30, "get_BatchThreshold Lookup")
        details = self.exec_sp(self.conn, 'get_BatchThreshold', [dbName])
        xml = ''
        for part in details:
            xml += part[0]
        log(20, "get_BatchThreshold lookup complete.")
        return xml

    def get_BatchThreshold_obj(self, bth_xml):
        log(30, "start get_BatchThreshold.obj_wrapper")
        status, dbs_obj = BatchThreshold.obj_wrapper(bth_xml)
        log(10, "bh_obj: {}".format(dbs_obj))
        log(30, "finish get_BatchThreshold.obj_wrapper")
        return dbs_obj

    def get_bics_obj(self, dbName, time_stamp):
        bics_xml = self.get_BatchImportCurrentState_XML(dbName, time_stamp)
        return self.get_BatchImportCurrentState_obj(bics_xml)

    def get_BatchImportCurrentState_XML(self, dbName, time_stamp):
        log(30, "get_BatchImportCurrentState Lookup")
        details = self.exec_sp(self.conn, 'get_BatchImportCurrentState', [dbName, time_stamp])
        xml = ''
        for part in details:
            xml += part[0]
        log(20, "get_BatchImportCurrentState lookup complete.")
        return xml

    def get_BatchImportCurrentState_obj(self, bics_xml):
        log(30, "start get_BatchImportCurrentState.obj_wrapper")
        status, dbs_obj = BatchImportCurrentState.obj_wrapper(bics_xml)
        log(10, "bh_obj: {}".format(dbs_obj))
        log(30, "finish get_BatchImportCurrentState.obj_wrapper")
        return dbs_obj
