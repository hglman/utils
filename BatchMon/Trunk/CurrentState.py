import logging
import datetime

log = logging.getLogger('main').log

class CurrentState(object):

    def __init__(self, bics_obj, threshold_obj):
        self.BatchMessageID = ()
        self.bics_obj = bics_obj
        self.threshold_obj = threshold_obj
        self.BatchMessageID = None
        self.Alert = []
        self.Master = {}
        self.History ={}
        self.Total = {}
        self.Finish = False
        self.Start = False
    
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return 'Alert:{} Total:{} Master:{}, History:{}, Finish:{}'.format(
            self.Alert, self.Total, self.Master, self.History, self.Finish)

    def get_BatchMessageID(self):
        if self.bics_obj.CurrentState:
            self.BatchMessageID= self.bics_obj.CurrentState[0].attrs["BatchMessageID"]

    def process_bics(self):
        self.get_BatchMessageID()
        self.process_alert_state()
        self.process_history()
        self.process_master()

    def process_alert_state(self):
        for alert in self.bics_obj.Alert:
            if alert.attrs["handled"] == '0':
                alert.attrs["handled"] = False
            elif alert.attrs["handled"] == "1":
                alert.attrs["handled"] = True
            self.Alert.append(alert.attrs)

    def process_node_list_to_dict(self, key, type, count, total):
        self.Total[type] = 0
        start = {}
        finish = {}
        if self.bics_obj.CurrentState:
            #collect up start and finish, as we need to choose out comes based on what data is present
            for record in self.bics_obj.CurrentState[0].__dict__[type]:
                if 'Finish' in record.attrs["batchName"]:
                    finish[key(record.attrs)] = int(record.attrs[count])
                if 'Start' in record.attrs["batchName"]:
                    start[key(record.attrs)] = int(record.attrs[count])
            if start:
                if finish:
                    #this is the case that should occur in a "good" run
                    for key in start.iterkeys():
                        #if no finish key, then things are crazy and I am just going to pretend it didn't happen
                        if key in finish:
                            value = abs(int(start[key]) - int(finish[key]))
                            self.__dict__[type][key] = abs(int(start[key]) - int(finish[key]))
                            #add to total
                            self.Total[type] += total(key, value)
            #start with now finish is a failure, we will alert just on the total being 0
            elif finish:
                #no start flag, but a finish, so shit went down, but likely our start flag data was lost in transit
                for key in start.iterkeys():
                    self.__dict__[type][key] = int(finish[key])
                    #add to total
                    self.Total[type] += total(key, int(finish[key]))

    def process_master(self):
        def key(dict):
            return (("productTypeID",dict["productTypeID"]))
        def total(key, value):
            return value
        self.process_node_list_to_dict(key, 'Master', 'masterCount', total)

    def process_history(self):
        def key(dict):
            DOW = datetime.datetime.strptime(dict["postDate"], '%Y%m%d').weekday()
            return (("productTypeID", dict["productTypeID"]), ("postDateDOW", unicode(DOW)))
        def total(key, value):
            if self.threshold_obj.DOW == key[1][1]:
                return value
            return 0
        self.process_node_list_to_dict(key, 'History', 'tranCount', total)
