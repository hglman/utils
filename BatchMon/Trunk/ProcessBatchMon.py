import BatchMon as bm
import logger
import XMLSerializers.XMLAdapter as xa
import API.xml.base_xml as bx
import cPickle
import datetime


log = logger.make_logger('main', "BatchMon.log", r"E:\BatchMon\Threshold", 10).log

def make_FI_list(dbs_obj):
    FI_list = [row.attrs['source_DBName'].upper()
        for row in dbs_obj.row
            if row.attrs['source_DBName']  not in ('DB_3041', 'DB_3176')
                and row.attrs['source_is_read_only'] == '0']
    return list(set(FI_list))
"""
    3	history
    5	history_total
    4	master
    6	master_total
    1	run_time
    2	start_time
    7	start_time_top1
"""
#for choosing how to filter each type
biteID_fliter_dict = {
'4': bm.func_comp(bm.remove_zero, bm.inner_percentage(.7)),
'3': bm.func_comp(bm.remove_zero, bm.inner_percentage(.7)),
'5': bm.func_comp(bm.remove_zero, bm.inner_percentage(.7)),
'6': bm.func_comp(bm.remove_zero, bm.inner_percentage(.7)),
'1': bm.func_comp(bm.remove_zero, bm.mode),
'2': bm.func_comp(bm.remove_zero, bm.mode)
}


def process_batchHistorical():
    log(30, 'Starting process_batchHistorical')
    log(10, 'bite_filter_dict:{}'.format(biteID_fliter_dict))
    with xa.XMLAdapter() as xa_obj:
        dbs_obj = xa_obj.get_dbs_obj()
        FI_list = make_FI_list(dbs_obj)
        log(20, 'xa_obj.get_FI_list: FI_list:{}, dbs_obj:{}'.format(FI_list, dbs_obj))
        with xa.XMLToFile('BatchHistorical.xml', 'BatchHistorical') as _f:
            with open(r'E:\BatchMon\Pickle\BatchMon.p', 'w') as _p:
                for dbName in FI_list:
                    log(30, '------xxxxxxXXXXXX NEW FI XXXXXXxxxxxx---------')
                    log(20, 'Current dbName:{}'.format(dbName))
                    bh_obj = xa_obj.get_bh_obj(dbName)
                    log(20, 'Get Batch Historical Object(bh_obj) from DB, bh_opj:{}'.format(bh_obj.DataBase))
                    thb_obj = bm.ThresholdBuilder(bh_obj)
                    thb_obj.process_batchHistorical_obj()
                    log(20, 'Process BatchHistorical to Thresholds(thb_obj), thb_obj')
                    cPickle.dump({dbName: thb_obj.curr_FI}, _p, 2)
                    child_list = thb_obj.process_curr_FI_to_child_list(biteID_fliter_dict)
                    temp_xml = bx.XMLNode("dbName", {"Name": dbName}, None, child_list).flatten_self()
                    _f.write(temp_xml)
        with open('BatchHistorical.xml', 'r') as _f:
            xa_obj.set_BatchImportThreshold_tbl(_f)

if __name__ == '__main__':
    process_batchHistorical()
