import logging
import datetime

log = logging.getLogger('main').log

class CurrentThreshold(object):

    def __init__(self, width, bth_obj):
        self.width = width
        self.bth_obj = bth_obj
        self.DOW = None
        self.Total = {}
        self.Time= {}
        self.Master = {}
        self.History = {}

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'DOW:{} Total:{} Time:{} Master:{} History:{}'.format(self.DOW, self.Total, self.Time, self.Master, self.History)

    def get_min_start_time(self, time):
        return float(time.attrs['mean']) - (self.width * float(time.attrs['std']))
        
    def get_max_start_time(self, time):
        return float(time.attrs['mean']) + (self.width * float(time.attrs['std']))

    def process_master(self):
        def key(item):
            return ("productTypeID", item.attrs["productTypeID"])
        self.process_type('Master', key)

    def process_history(self):
        def key(item):
            return ("productTypeID", (item.attrs["productTypeID"])),("postDateDOW", item.attrs["postDateDOW"])
        self.process_type('History', key)

    def process_type(self, type, key):
        for item in self.bth_obj.__dict__[type]:
            if item.attrs["runDOW"] == str(self.DOW) and float(item.attrs["mean"]) > 0.0:
                self.__dict__[type][key(item)] = {"mean": item.attrs["mean"], "std": item.attrs["std"]}

    def process_total(self):
        for time in self.bth_obj.Time:
            log(10, 'time:{}'.format(time.attrs))
            if time.attrs["runDOW"] == str(self.DOW):
                log(10, 'runDOW:{} timeType:{}'.format(time.attrs["runDOW"], time.attrs["timeType"]))
                if time.attrs["timeType"] == 'history':
                    log(10, 'history:{}'.format({"mean": time.attrs["mean"], "std": time.attrs["std"]}))
                    self.Total['History'] = {"mean": time.attrs["mean"], "std": time.attrs["std"]}
                    log(10, 'self.Total:{}'.format(self.Total))
                if time.attrs["timeType"] == 'master':
                    log(10, 'master:{}'.format({"mean": time.attrs["mean"], "std": time.attrs["std"]}))
                    self.Total['Master'] = {"mean": time.attrs["mean"], "std": time.attrs["std"]}
                    log(10, 'self.Total:{}'.format(self.Total))
                    
    def get_datetime(self, time, now):
        log(10, 'time:{}, now:{}'.format(time, now))
        hour = int(time / 3600)
        log(10, 'time/3600:{}'.format(time / 3600))
        time = time % 3600
        log(10, 'time:{}'.format(time))
        min = int(time / 60)
        second = int(time % 60)
        log(10, 'hour:{}, min:{}, second:{}'.format(hour, time, min))
        day = now.day
        if hour > 24:
            day = now.day + 1
            hour = hour % 24
        time = datetime.datetime(now.year, now.month, day, hour, min, second)
        if now.weekday() == self.DOW:
            return time
        return time - datetime.timedelta(days = 1)

    def process_time(self):
        now = datetime.datetime.now()
        time, DOW = self._process_time(now)
        log(10, 'now: {}, time: {}, DOW: {}'.format(now, time, DOW))
        if not time:
            return None
        self.DOW = DOW
        start_time = time[0]
        log(10,'start_time: {}'.format(start_time))
        self.Time['start_time'] = self.get_datetime(start_time, now)
        end_time = float(time[1].attrs['mean']) + (self.width * float(time[1].attrs['std']))
        log(10, 'end_time: {}'.format(end_time))
        self.Time['finish_time'] = self.get_datetime(self.get_max_start_time(time[0]), now) + datetime.timedelta(seconds=end_time)
        log(10, 'finish_time:{}'.format(self.Time['finish_time']))

    def _process_time(self, now):
        DOW = now.weekday()
        now = (now.time().hour * 3600) + (now.time().minute * 60)
        DBDOW = ((DOW - 1) % 7)
        log(10,'current DOW: {}, current time: {}, DBDOW: {}'.format(DOW, now, DBDOW))
        candidate_run = {}
        for time in self.bth_obj.Time:
            if time.attrs["runDOW"] == str(DOW):
                if time.attrs["timeType"] == 'start_time':
                    #have we seen the run time
                    if DOW in candidate_run:
                        #is this the DOW we want
                        if self.get_min_start_time(time) <= now:
                            return (time, candidate_run[DOW]), DOW
                    else:
                        candidate_run[DOW] = time
                if time.attrs["timeType"] == 'run_time':
                    #have we seen the start time
                    if DOW in candidate_run:
                        #if there is a start time, we want to use this DOW
                        return (candidate_run[DOW], time), DOW
                    else:
                        #store run_time for possible return later
                        candidate_run[DOW] = time
            if time.attrs["runDOW"] == DBDOW:
                if time.attrs["type"] == 'start_time':
                    #have we seen the run_time
                    if DBDOW in candidate_run:
                        candidate_run[DBDOW][0] = time
                    else:
                        candidate_run[DBDOW] = [time, None]
                if time.attrs["type"] == 'run_time':
                    #have we seen the start_time
                    if DBDOW in candidate_run:
                        candidate_run[DBDOW][1] = time
                    else:
                        candidate_run[DBDOW] = [None, time]
        if DBDOW in candidate_run:
            return candidate_run[DBDOW], DBDOW
        else:
            return False, False

    def process_bth_obj(self):
        try:
            self.process_time()
            self.process_master()
            self.process_history()
            self.process_total()
        except Exception as e:
            log(40, '{}'.format(e))