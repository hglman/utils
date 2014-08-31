import datetime
import logging
import batch_import_dbops_helper as bidh
import API.util.logging as lg

log = logging.getLogger('main').log

class MakeAlert(object):

    def __init__(self, state_obj, threshold_obj, dbName, width):
        self.dbName = dbName
        self.width = width
        self.state_obj = state_obj
        self.threshold_obj = threshold_obj
        self.type_list = ['History']
        self.alert_list = []

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'alert_list:{}'.format(self.alert_list)

    def process_current_alert(self):
        if self.state_obj.Alert:
            #a single false means go ahead, which is why we negate the return
            result = True
            for alert in self.state_obj.Alert:
                result = result and alert["handled"]
            return not result
        return True

    def get_interval(self, threshold_dict):
        std = float(threshold_dict['std'])
        return (float(threshold_dict['mean']) - (self.width * std),
            float(threshold_dict['mean']) + (self.width * std))

    def process_time_alert(self):
        now = datetime.datetime.now()
        result = False
        log(10,
            "Compare Finish Time to Now now:{}, self.threshold_obj.Time['finish_time']:{}".format(
                now, self.threshold_obj.Time['finish_time']))
        if self.threshold_obj.Time['finish_time'] < now:
            log(10, 'Finish flag:{}'.format(self.state_obj.Finish))
            if not self.state_obj.Finish:
                self.alert_list.append('Time Failure Alert')
            result = True
        log(10, 'Finished with Time Processing, self.alert_list:{}'.format(self.alert_list))
        return result

    def bound_alert(self, type, key, interval, data_point):
        self.alert_list.append('{} with key {} is out side of expected range {}-{} with value {}'.format(
                            type, key, interval[0], interval[1], data_point))

    def process_data_alert(self):
        for type in self.type_list:
            log(10, 'Current Type being processed to alert, Type:{}'.format(type))
            for key, threshold_dict in self.threshold_obj.__dict__[type].iteritems():
                log(10, 'Current Key and Thresholds, key:{} threshold_dict:{}'.format(key, threshold_dict))
                log(10, 'Test for Key in self.state_obj.__dict__[type]:{}'.format(self.state_obj.__dict__[type]))
                if key in self.state_obj.__dict__[type]:
                    interval = self.get_interval(threshold_dict)
                    data_point = self.state_obj.__dict__[type][key]
                    log(10, 'interval:{}, data_point:{}'.format(interval, data_point))
                    del self.state_obj.__dict__[type][key]
                    if not interval[0] <= data_point <= interval[1]:
                        self.bound_alert(type, key, interval, data_point)
            log(10, 'All Thresholds Have been Checked, Remaining Current State, {}'.format(
                self.state_obj.__dict__[type]))
            for key, value in self.state_obj.__dict__[type].iteritems():
                if value > 0:
                    self.alert_list.append('Unexpected {} Data with key {} of {}'.format(type, key, value))
            log(10, 'Finished Processing Data types, self.alert_list:{}'.format(self.alert_list))

    def process_total_alert(self):
        for type in self.type_list:
            log(10, 'type:{}'.format(type))
            interval = self.get_interval(self.threshold_obj.Total[type])
            log(10, 'total alert test:{} <= {} <= {}'.format(interval[0], self.state_obj.Total[type], interval[1]))
            if not interval[0] <= self.state_obj.Total[type] <= interval[1]:
                self.bound_alert(type, 'total', interval, self.state_obj.Total[type])

    def process_to_alert(self):
        if self.process_current_alert():
            if self.process_time_alert() and not self.alert_list:
                #self.process_data_alert()
                self.process_total_alert()
                
    def send_alert(self, dbs_obj):
        for row in dbs_obj.row:
            if row.attrs['source_DBName'].upper() == self.dbName and row.attrs['source_is_read_only'] == '0':
                fiToAlert = str(row.attrs['source_DBName'].upper())
                serverName =  str(row.attrs['serverName'].upper())
                messageID = self.state_obj.BatchMessageID
                log(20, 'Alert:{} {} {}'.format(fiToAlert, serverName, messageID))
                dbh = bidh.BatchImportDBopsHelper("http://operationsmonitor.dc.local/API_WS/Api.asmx", 
                    "990000001", "1", serverName, fiToAlert, messageID)
                dbh.triggerNotification(''.join(self.alert_list), 'BatchMon-Test')
