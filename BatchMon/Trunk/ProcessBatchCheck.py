import CurrentState as cs
import CurrentThreshold as ct
import logger
import XMLSerializers.XMLAdapter as xa
import Alert as a
from datetime import datetime as dt

log = logger.make_logger('main', "BatchCheck.log", r"E:\BatchMon\Check", 10).log

def make_FI_list(dbs_obj):
    FI_list = [row.attrs['source_DBName'].upper() for row in dbs_obj.row
                if row.attrs['source_DBName'] not in ('TestDB2', 'TestDB3')
                    and row.attrs['source_is_read_only'] == '0']
    return list(set(FI_list))


def process_batchCheck():
    width = 3.7
    log(20, 'Starting process_batchCheck, Config: width:{}'.format(width))
    with xa.XMLAdapter() as xa_obj:
        with open('E:\BatchMon\Alert\{}-alert.txt'.format(dt.now().strftime('%Y-%m-%dT%H%M%S')), 'w') as _f:
            dbs_obj = xa_obj.get_dbs_obj()
            FI_list = make_FI_list(dbs_obj)
            log(20, 'xa_obj.get_FI_list: FI_list:{}, dbs_obj:{}'.format(FI_list, dbs_obj))
            for dbName in FI_list:
                log(30, '------xxxxxxXXXXXX NEW FI XXXXXXxxxxxx---------')
                log(20, 'Current dbName:{}'.format(dbName))
                bth_obj = xa_obj.get_bth_obj(dbName)
                log(20, 'Get Batch Threshold Object(bth_obj) from DataBase for {}, bth_obj:{}'.format(dbName, bth_obj))
                threshold_obj = ct.CurrentThreshold(width, bth_obj)
                threshold_obj.process_bth_obj()
                log(20, 'Process bth_obj into Threshold Object, threshold_obj:{}'.format(threshold_obj))
                if threshold_obj and threshold_obj.Time:
                    bics_obj = xa_obj.get_bics_obj(dbName,
                        threshold_obj.Time['start_time'].strftime('%Y-%m-%dT%H:%M:%S'))
                    log(20, '''
                        Get BatchImportCurrentState Object(bics_obj) from DB,
                        timestamp:{} bics_obj:{}'''.format(threshold_obj.Time[
                            'start_time'].strftime('%Y-%m-%dT%H:%M:%S'),bics_obj))
                    state_obj = cs.CurrentState(bics_obj, threshold_obj)
                    state_obj.process_bics()
                    log(20, 'Process bics_obj into Current State Object(state_boj), state_obj:{}'.format(state_obj))
                    ma_obj = a.MakeAlert(state_obj, threshold_obj, dbName, width)
                    try:
                        ma_obj.process_to_alert()
                    except Exception as e:
                        log(50, 'Failure:{}'.format(e))
                    log(20, 'Process state_obj, threshold_obj into Alerts Object (ma_object), ma_object:{}'.format(ma_obj))
                    if ma_obj.alert_list:
                        ma_obj.send_alert(dbs_obj)
                    _f.write('dbName:{} {}'.format(dbName, str(ma_obj.alert_list)))
                    _f.write('\n')

if __name__ == '__main__':
    process_batchCheck()
