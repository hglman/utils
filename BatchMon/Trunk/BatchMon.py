__author__ = 'btuttle'
import datetime
import numpy
import scipy.stats as stats
import functools
import API.xml.base_xml as BX
import logging
import logger
import traceback

log = logging.getLogger('main').log
#log_t = logger.make_logger('total', "Total.log", r"E:\BatchMon\Threshold", 10).log

class BatchHistorical(object):
    """ bite table for reference
    id	name
    3	history
    5	history_total
    4	master
    6	master_total
    1	run_time
    2	start_time
    7	start_time_top1

    FROM OPENXML (@idoc, '/BatchHistorical/dbName',1)
      WITH (Name  varchar(200) '../@Name',
            runDOW int '@run_DOW',
            productTypeID int '@productTypeID',
            postDOW int '@post_DOW',
            std real '@std',
            mean real '@mean',
            biteID INT '@biteID'
            )
    """

    def __init__(self, run_DOW, biteID, post_DOW = None, ProductTypeID=None):
        self.count_list = []
        self.run_DOW = run_DOW
        self.post_DOW = post_DOW
        self.ProductTypeID = ProductTypeID
        self.biteID = str(biteID)

    def append(self, value):
        self.count_list.append(float(value))

    def get_np_array(self, filter):
        np_array = numpy.empty(0)
        return numpy.append(np_array, filter(self.count_list))

    def std(self, filter):
        return numpy.std(self.get_np_array(filter))

    def mean(self, filter):
        return numpy.mean(self.get_np_array(filter))

    def to_xml(self, biteID_filter_dict=None):
        """
        make xml form of the object
        """
        filter = lambda x: x
        if biteID_filter_dict:
            filter = biteID_filter_dict[self.biteID]
        attr_dict = self.key()
        attr_dict['mean'] = str(self.mean(filter))
        attr_dict['std'] = str(self.std(filter))
        return BX.XMLNode(self.__class__.__name__, attr_dict)

    def __str__(self):
        return self.to_xml().flatten_self()

    def key(self):
        key_dict = {'runDOW': self.run_DOW,
            'postDOW': self.post_DOW,
            'productTypeID': self.ProductTypeID,
            'biteID': self.biteID}
        return dict([(k, v) for k, v in key_dict.iteritems() if v is not None])

    def __hash__(self):
        return hash(self.key())

    def __eq__(self, other):
        return self.key() == other.__key()

class ThresholdBuilder(object):

    def __init__(self, bh_obj):
        self.bh_obj = bh_obj
        self.curr_FI = {}

    def process_batchHistorical_obj(self):
        try:
            for db in self.bh_obj.DataBase:
                max_start_time = datetime.datetime.min
                for re in db.RunEvent:
                    maxDate = self.process_start_finish_datetime(db.attrs["maxDate"])
                    if maxDate > max_start_time:
                        max_start_time = maxDate
                    run_DOW = self.process_run_event_node(re)
                    master_total = 0
                    for master in re.Master:
                        master_total += self.process_master_node(master, run_DOW)
                    self.process_master_total(run_DOW, master_total)
                    hist_dict = {}
                    for history in re.History:
                        result = (self.process_history_node(history, run_DOW))
                        if result[1] in hist_dict:
                            hist_dict[result[1]] += result[0]
                        else:
                            hist_dict[result[1]] = result[0]
                    self.process_history_total(run_DOW, hist_dict)
        except Exception as e:
            log(50, 'Error, {}'.format(traceback.format_exc()))

    def process_master_total(self, run_DOW, total):
        key = (run_DOW, 'master')
        if key in self.curr_FI:
            self.curr_FI[key].append(total)
        else:
            self.curr_FI[key] = BatchHistorical(run_DOW, 6)
            self.curr_FI[key].append(total)
            
    def process_history_total(self, run_DOW, hist_dict):
        key = (run_DOW, 'history')
        DBDOW = str((int(run_DOW) - 1) % 7)
        max = 0
        #goal is to pick the biggest of either the run day or the day before
        for k in hist_dict.iterkeys():
            if k in (run_DOW, DBDOW):
                if hist_dict[k] > max:
                    if key in self.curr_FI:
                        self.curr_FI[key].append(hist_dict[k])
                    else:
                        self.curr_FI[key] = BatchHistorical(run_DOW, 5)
                        self.curr_FI[key].append(hist_dict[k])
        log(10, '{} list:{}'.format(self.curr_FI[key], self.curr_FI[key].count_list))

    def process_run_event_node(self, re):
        start_datetime = self.process_start_finish_datetime(re.attrs['Start'])
        end_datetime = self.process_start_finish_datetime(re.attrs['Finish'])
        run_DOW = str(start_datetime.weekday())
        run_time = end_datetime - start_datetime
        start_time = ((start_datetime.time().hour * 3600) + (start_datetime.time().minute * 60)
                      + start_datetime.time().second)
        if (run_DOW, 'run_time') in self.curr_FI:
            self.curr_FI[(run_DOW, 'start_time')].append(start_time)
            self.curr_FI[(run_DOW, 'run_time')].append(run_time.total_seconds())
        else:
            start_time_obj = BatchHistorical(run_DOW, 2)
            start_time_obj.append(start_time)
            run_time_obj = BatchHistorical(run_DOW, 1)
            run_time_obj.append(run_time.total_seconds())
            self.curr_FI[(run_DOW, 'run_time')] = run_time_obj
            self.curr_FI[(run_DOW, 'start_time')] = start_time_obj
        return run_DOW

    def process_master_node(self, master, run_DOW):
        masterUpdated = int(master.attrs['mastersUpdated'])
        productTypeID = master.attrs['productTypeID']
        if (run_DOW, productTypeID) in self.curr_FI:
            self.curr_FI[(run_DOW, productTypeID)].append(masterUpdated)
        else:
            self.curr_FI[(run_DOW, productTypeID)] = BatchHistorical(run_DOW, 4, ProductTypeID=productTypeID)
            self.curr_FI[(run_DOW, productTypeID)].append(masterUpdated)
        return masterUpdated

    def process_history_node(self, history, run_DOW):
        transAdded = int(history.attrs['transAdded'])
        productTypeID = history.attrs['productTypeID']
        postDate_date = self.process_postdate_datetime(history.attrs['postDate'])
        postDate_DOW = str(postDate_date.weekday())
        if (run_DOW, productTypeID, postDate_DOW) in self.curr_FI:
            self.curr_FI[(run_DOW, productTypeID, postDate_DOW)].append(transAdded)
        else:
            self.curr_FI[(run_DOW, productTypeID, postDate_DOW
                )] = BatchHistorical(run_DOW, 3, post_DOW=postDate_DOW, ProductTypeID=productTypeID)
            self.curr_FI[(run_DOW, productTypeID, postDate_DOW)].append(transAdded)
        return transAdded, postDate_DOW
        
    def process_start_finish_datetime(self, time):
        try:
            date_format = '%Y-%m-%dT%H:%M:%S.%f'
            dt = datetime.datetime.strptime(time, date_format)
        except Exception:
            date_format = '%Y-%m-%dT%H:%M:%S'
            dt = datetime.datetime.strptime(time, date_format)
        return dt

    def process_postdate_datetime(self, time):
        date_format = '%Y%m%d'
        return datetime.datetime.strptime(time, date_format)

    def process_curr_FI_to_child_list(self, biteID_filter_dict):
        child_list =  self._process_curr_FI_to_child_list([], biteID_filter_dict)
        log(10, 'child_list:{}'.format(child_list))
        return child_list
        
    def _process_curr_FI_to_child_list(self, child_list, biteID_filter_dict):
        if self.curr_FI:
            #k is the __key, v is the object, dont care about the k
            k, v = self.curr_FI.popitem()
            child_list.append(v.to_xml(biteID_filter_dict))
            return self._process_curr_FI_to_child_list(child_list, biteID_filter_dict)
        else:
            return child_list

#build up a set of possible filters to be used, func_comp for applying multiple
def func_comp(*args):
    def comp(f, g):
        return lambda x: g(f(x))
    return functools.reduce(comp, args)

def remove_zero(count_list):
    tmp = [item for item in count_list if item != 0]
    if len(tmp) == 0:
        return [0]
    return tmp

def inner_percentage(percent):
    if not 0 <= percent <= 1:
        raise ValueError('Not a valid percent {}'.format(percent))
    ht_percent = int((1 - percent)  / 2)
    def part_inner_percent(count_list):
        size = len(count_list)
        list.sort(count_list)
        temp_list = count_list[ht_percent:-ht_percent]
        if len(temp_list) == 0:
            return count_list
        return temp_list
    return part_inner_percent

def mode(count_list):
    np_array = numpy.empty(0)
    a = numpy.append(np_array, count_list)
    return stats.mode(a)
