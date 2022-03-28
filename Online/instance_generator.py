import sqlite3
import random

g_instance_id = "my_steel"
g_stage_names = ['LD', 'LF', 'CC']
g_stage_pt_min = [20, 30, 40]
g_stage_pt_max = [30, 50, 60]
g_stage_skips = [0, 0, 0]
g_machine_numbers = [3, 4, 3]
g_case_in_instance = 4
g_batch_levels = {6: (10, 20), 8: (10, 20), 10: (10, 20)}
g_setup_time = 60
g_trans_time = 5


def cretate_database(instance_id):
    conn = sqlite3.connect(instance_id + ".db")
    try:
        create_stage_table = '''
            CREATE TABLE IF NOT EXISTS [mbd_stage_info](
            [stage_id] VARCHAR(8) PRIMARY KEY, 
            [stage_name] VARCHAR(16), 
            [machine_count] INT, 
            [pt_min] INT, 
            [pt_max] INT, 
            [skip_rate] DOUBLE, 
            [remark] VARCHAR(255));
        '''
        conn.execute(create_stage_table)
        create_mach_table = '''
            CREATE TABLE IF NOT EXISTS [mbd_machine_info](
              [machine_id] VARCHAR(5)  PRIMARY KEY, 
              [machine_name] VARCHAR(10), 
              [speed_normal] DOUBLE, 
              [speed_min] DOUBLE, 
              [speed_max] DOUBLE, 
              [stage_id] VARCHAR(10), 
              [remark] VARCHAR(255));
                '''
        conn.execute(create_mach_table)

        create_inst_table = '''
            CREATE TABLE IF NOT EXISTS [sch_instance_info](
              [instance_id] VARCHAR(16)  PRIMARY KEY, 
              [batch_num] INT(4), 
              [batch_size_min] INT(4), 
              [batch_size_max] INT(4), 
              [remark] VARCHAR(255));
                        '''
        conn.execute(create_inst_table)

        create_batch_table = '''
            CREATE TABLE IF NOT EXISTS [sch_batch_info](
              [batch_id] VARCHAR(10),
              [instance_id] VARCHAR(10),
              [batch_size] INT, 
              [setup_time] INT, 
              [ma_destined] VARCHAR(10), 
              [st_destined] INT, 
              [remark] VARCHAR(256),
              PRIMARY KEY ([batch_id], [instance_id])
              ); '''
        conn.execute(create_batch_table)

        create_job_table = '''
            CREATE TABLE IF NOT EXISTS [sch_job_info](
            [job_id] VARCHAR(16), 
            [instance_id] VARCHAR(16), 
            [batch_id] VARCHAR(16), 
            [seq_in_batch] INT(4), 
            [due_date] INT(4), 
            [release_date] INT(4), 
            [remark] VARCHAR(255), 
            PRIMARY KEY([job_id], [instance_id]));
        '''
        conn.execute(create_job_table)

        create_operation_table = '''
            CREATE TABLE  IF NOT EXISTS [sch_operation_info](
            [operation_id] VARCHAR(10), 
            [instance_id] VARCHAR(10), 
            [job_id] VARCHAR(10), 
            [operation_status] INT(1) DEFAULT 0, 
            [stage_id] VARCHAR(10), 
            [oper_prev_stage] VARCHAR(10), 
            [oper_next_stage] VARCHAR(10), 
            [ma_pt_list] VARCHAR(100), 
            [up_dw_ts] VARCHAR(100), 
            [machine_id] VARCHAR(10), 
            [start_time] INT, 
            [end_time] INT, 
            [realized_pt] VARCHAR(128), 
            [arrival_time] INT, 
            [depart_time] INT, 
            PRIMARY KEY([operation_id], [instance_id]));
          '''
        conn.execute(create_operation_table)


    except:
        print("Create table failed")
        return False


def create_factory_info(stage_num):
    conn = sqlite3.connect(g_instance_id + ".db")
    cur = conn.cursor()
    cur.execute("delete from mbd_stage_info")
    cur.execute("delete from mbd_machine_info")
    conn.commit()
    machine_dict = {}
    for i in range(stage_num):
        sql = 'insert into mbd_stage_info(stage_id,stage_name,machine_count,pt_min,pt_max,skip_rate)' \
              ' values(%s,\'%s\',%s,%s,%s,%s)' % (i + 1, g_stage_names[i], g_machine_numbers[i],
                                                  g_stage_pt_min[i], g_stage_pt_max[i], 0.0)
        cur.execute(sql)
        for k in range(g_machine_numbers[i]):
            ma_id = str(i + 1) + str(k + 1)
            sql = 'insert into mbd_machine_info(machine_id,machine_name,stage_id,speed_normal,speed_min,speed_max)' \
                  ' values(%s,\'%s\',%s,%s,%s,%s)' % (ma_id, g_stage_names[i] + str(k + 1),
                                                      i + 1, 1.0, 1.0, 1.0)
            cur.execute(sql)
            machine_dict[ma_id] = 0
    conn.commit()
    return machine_dict


def create_instance_info(case_num, mach_dict):
    conn = sqlite3.connect(g_instance_id + ".db")
    cur = conn.cursor()
    cur.execute("delete from sch_instance_info")
    cur.execute("delete from sch_batch_info")
    cur.execute("delete from sch_job_info")
    cur.execute("delete from sch_operation_info")
    conn.commit()

    for n in range(case_num):
        for batch_num, batch_size in g_batch_levels.items():
            instance_id = '%s_%s*[%s-%s]#%s' % (g_instance_id, batch_num, batch_size[0], batch_size[1], n + 1)
            sql = 'insert into sch_instance_info(instance_id,batch_num,batch_size_min,batch_size_max)' \
                  ' values(\'%s\',%s,%s,%s )' % (instance_id, batch_num, batch_size[0], batch_size[1])
            cur.execute(sql)

            jx = 0
            for b in range(batch_num):
                batch_id = 'H_%02d' % (b + 1)
                dest_mach = '3%d' % (b % g_machine_numbers[-1] + 1)
                job_num = random.randint(batch_size[0], batch_size[1])
                sql = 'insert into sch_batch_info(batch_id,instance_id,batch_size,setup_time,ma_destined)' \
                      ' values(\'%s\',\'%s\',%s,%s,%s)' % (batch_id, instance_id, job_num, g_setup_time, dest_mach)
                cur.execute(sql)
                for j in range(job_num):
                    jx = jx + 1
                    job_id = 'J_%03d' % jx
                    sql = 'insert into sch_job_info(job_id, instance_id,batch_id,seq_in_batch,due_date,release_date)' \
                          ' values(\'%s\',\'%s\',\'%s\',%s,%s,%s )' % (job_id, instance_id, batch_id, j + 1, 0, 0)
                    cur.execute(sql)
                    prev_oper = ''
                    for i in range(len(g_stage_names)):
                        operation_id = 'O_%d_%03d' % (i + 1, jx)
                        if random.random() < g_stage_skips[i]:
                            continue
                        if i == 0:
                            up_dw_ts = '0|%s' % g_trans_time
                        elif i == len(g_stage_names) - 1:
                            up_dw_ts = '%s|0' % g_trans_time
                        else:
                            up_dw_ts = '%s|%s' % (g_trans_time, g_trans_time)
                        pt = random.randint(g_stage_pt_min[i], g_stage_pt_max[i])
                        ma_pt_list = ""
                        for key in mach_dict.keys():
                            if key[0] == str(i+1):
                                ma_pt_list += "%s:%s,%s,%s|" % (key, pt, g_stage_pt_min[i], g_stage_pt_max[i])
                        ma_pt_list = ma_pt_list.strip("|")
                        sql = 'insert into sch_operation_info(operation_id,instance_id,job_id,operation_status,' \
                              'stage_id, oper_prev_stage,ma_pt_list,up_dw_ts) ' \
                              'values(\'%s\',\'%s\',\'%s\',%s, %s,\'%s\',\'%s\',\'%s\') ' % \
                              (operation_id, instance_id, job_id, 0, i + 1, prev_oper, ma_pt_list, up_dw_ts)
                        print(sql)
                        cur.execute(sql)
                        if len(prev_oper) > 0:
                            sql = 'update sch_operation_info set oper_next_stage=\'%s\' where operation_id=\'%s\'' \
                                  ' and instance_id=\'%s\'' % (operation_id, prev_oper, instance_id)
                            print(sql)
                            cur.execute(sql)
                        prev_oper = operation_id
            conn.commit()


if __name__ == "__main__":

    cretate_database(g_instance_id)
    mach_dict = create_factory_info(len(g_stage_names))
    create_instance_info(g_case_in_instance, mach_dict)
