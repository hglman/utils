__author__ = 'btuttle'
import API.sql.helper as sql_helper
import logging
import traceback

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


class EPAdapter(object):
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

    def exec_sp(self, sp_name, parameter_list):
        log(30, "exec_sp Lookup")
        result, detail = self.conn.execute_sp_odbc(sp_name, parameter_list)
        if not result:
            log(50, "Unable to exec {}, update will return. {}".format(sp_name, detail))
            return False
        log(20, "exec_sp lookup complete.")
        return detail

    def exec_statement(self, sql):
        log(30, "exec_sp Lookup")
        result, detail = self.conn.execute(sql)
        if not result:
            log(50, "Unable to exec {}, update will return. {}".format(sql, detail))
            return False
        log(20, "exec_sp lookup complete.")
        return detail
