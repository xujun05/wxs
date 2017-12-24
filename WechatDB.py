import SpiderConfig
import MySQLdb
from DBUtils.PooledDB import PooledDB


class DBOperation:
    '''微信公众号数据库辅助类'''
    @staticmethod
    def init_pool(conf_file="db.conf"):
        conf_dict = SpiderConfig.Config.get_dict_by_section(conf_file,"db")
        DBOperation.pool = PooledDB(MySQLdb, 5, host=conf_dict['db_host'], port=int(conf_dict['db_port']),\
                                 user=conf_dict['db_user'], password=conf_dict['db_pwd'], db=conf_dict['db_name'], \
                                 use_unicode=True, charset="utf8")

    '执行SQL语句，主要是Insert与Update语句'
    @staticmethod
    def execute_operation(sql):
        conn = DBOperation.pool.connection()
        cur = conn.cursor()
        try:
            cur.execute(sql)
            conn.commit()
        except:
            conn.rollback()
        finally:
            cur.close()
            conn.close()

    '执行SQL的查询语句，并返回结果集'
    @staticmethod
    def excute_query(sql):
        conn = DBOperation.pool.connection()
        cur = conn.cursor()
        try:
            cur.execute(sql)
            return cur.fetchall()
        except Exception as e:
            print(e)
            conn.rollback()
        finally:
            cur.close()
            conn.close()

    '测试唯一性'
    @staticmethod
    def test_is_exists(sql):
        conn = DBOperation.pool.connection()
        cur = conn.cursor()
        try:
           cur.execute(sql)
           data = cur.fetchone()
           if data[0]:
               return False
           else:
               return True
        except Exception as e:
            print(e)
        finally:
            cur.close()
            conn.close()

    '将Dictionary类型的Python对象写入数据库，add_kvs表示需要增加的属性值，drop_keys代表不需要的属性'
    @staticmethod
    def insert_dict(table, msg_dict, add_kvs={},drop_keys=[]):
        # 处理不需要的key
        if len(drop_keys) != 0:
            for key in drop_keys:
                del msg_dict[key]
        # 添加需要的key value键值对
        if len(add_kvs) != 0:
            for key, value in add_kvs:
                msg_dict[key] = value
        conn = DBOperation.pool.connection()
        cur = conn.cursor()
        qmarks = ', '.join(['%s'] * len(msg_dict))  # 用于替换记录值
        cols = ', '.join(msg_dict.keys())  # 字段名
        sql = "INSERT INTO %s (%s) VALUES (%s)" % (table, cols, qmarks)
        try:
            cur.execute(sql, msg_dict.values())
        except Exception as e:
            print(e)
        finally:
            cur.close()
            conn.close()

    '获取当前公众号的最大appmsgid'
    @staticmethod
    def get_max_appmsgid_by_fackid(fakeid):
        conn = DBOperation.pool.connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT MAX(appmsgid) FROM `article` WHERE fakeid = '{}'".format(fakeid))
            result = cur.fetchone()[0]
            if type(result) == int :
                return result
            else:
                return 0
        except Exception as e:
            print(e)
        finally:
            cur.close()
            conn.close()