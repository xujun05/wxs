import MySQLdb
import util.config as config
from DBUtils.PooledDB import PooledDB
import types

db_dict = config.get_dict_by_section("wx.conf", "db")
db_pools = PooledDB(MySQLdb, 5, host=db_dict['db_host'], port=int(db_dict['db_port']), \
                    user=db_dict['db_user'], password=db_dict['db_pwd'], db=db_dict['db_name'], \
                    use_unicode=True, charset="utf8")


def get_all_thread_list_by_code(stock_code):
    return execute_query(
        "SELECT thread_id FROM `{}` WHERE stock_code='{}'".format("xueqiu_rs_stockcode_threads", stock_code))


def execute_update(sql):
    """
    执行SQL语句，主要是Insert与Update语句
    :param sql: 需要执行的insert与update语句
    :return:
    """
    conn = db_pools.connection()
    cur = conn.cursor()
    try:
        cur.execute(sql)
        conn.commit()
    except Exception as e:
        print("[SQL UPDATE ERROR]SQL={}".format(sql))
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def execute_query(sql):
    """
    执行SQL的查询语句，并返回结果集
    :param sql: 需要执行的query语句
    :return: 
    """
    conn = db_pools.connection()
    cur = conn.cursor()
    try:
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        print("[SQL QUERY ERROR]SQL={}".format(sql))
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def update_with_insert_id_key(_table, _msg_dict, add_kvs={}, drop_keys=[], _id_key=""):
    """
    如果存在就触发update操作，否则就触发insert操作。唯一性测试的SQL由Sql保证
    :param _table:表名
    :param _msg_dict:需要处理的字典
    :param add_kvs:字典需要增加的key value
    :param drop_keys:字典需要删除的keys
    :param _id_key:适用于表中有一个字段为id，且为primary key或者没有重复值的字段
    :return:数据库处理影响的行数
    """
    if id_test_is_exists(_id_key, table=_table):
        return update_dict(_table, _msg_dict, ['id'], add_kvs, drop_keys)
    else:
        return insert_dict(_table, _msg_dict, add_kvs, drop_keys)


def update_with_insert(_table, _msg_dict, add_kvs={}, drop_keys=[], predicates_keys=[], test_sql=""):
    """
    如果存在就触发update操作，否则就触发insert操作。唯一性测试的SQL由Sql保证
    :param _table:表名
    :param _msg_dict:需要处理的字典
    :param add_kvs:字典需要增加的key value
    :param drop_keys:字典需要删除的keys
    :param predicates_keys:UPDATE语句中的微词
    :param test_sql:唯一性测试的SQL
    :return:数据库处理影响的行数
    """
    if test_is_exists(test_sql):
        return update_dict(_table, _msg_dict, predicates_keys, add_kvs, drop_keys)
    else:
        return insert_dict(_table, _msg_dict, add_kvs, drop_keys)


def update_only_insert(_table, _msg_dict, add_kvs={}, drop_keys=[], test_sql=""):
    """
    如果存在就不做任何操作，否则就触发insert操作。唯一性测试的SQL由Sql保证
    :param _table:表名
    :param _msg_dict:需要处理的字典
    :param add_kvs:字典需要增加的key value
    :param drop_keys:字典需要删除的keys
    :param test_sql:唯一性测试的SQL
    :return:数据库处理影响的行数
    """
    if test_is_exists(test_sql):
        return 0
    else:
        return insert_dict(_table, _msg_dict, add_kvs, drop_keys)


def id_test_is_exists(_id, table):
    """
    简单的函数，测试某表是否存在某个id。原因，大量的表存在id这个字段
    :param _id: 需要检测的ID
    :param table: 表名称
    :return:
    """
    sql = "SELECT ISNULL((SELECT id FROM %s WHERE id = ('%s')))" % (table, _id)
    return test_is_exists(sql)


def test_is_exists(sql):
    """
    测试唯一性
    :param sql:需要执行的SQL SELECT IS NULL语句
    :return:如果存在，那么返回True，否则返回False
    """
    conn = db_pools.connection()
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


def insert_dict(_table, _msg_dict, add_kvs={}, drop_keys=[]):
    """
    将Dictionary类型的Python对象写入数据库，add_kvs表示需要增加的属性值，drop_keys代表不需要的属性
    :param _table: 需要插入的表名
    :param _msg_dict: 消息字典，防止修改原dictionary，进入后拷贝一份
    :param add_kvs: 需要增加的字段
    :param drop_keys: 需要删除的字段
    :return:影响数据库表的行数
    """
    msg_dict = _msg_dict
    # 处理不需要的key
    if len(drop_keys) != 0:
        for key in drop_keys:
            if key in msg_dict:
                del msg_dict[key]
    # 添加需要的key value键值对
    if len(add_kvs) != 0:
        for key, value in add_kvs.items():
            msg_dict[key] = value
    # 处理msg_dict中间的嵌套dict, tuple, list
    for key, value in msg_dict.items():
        if isinstance(value, dict) or isinstance(value, list) or isinstance(value, tuple):
            print("[IGNORED]:KEY({}) is not supported! tostring used! ".format(key))
            msg_dict[key]= str(value)
    conn = db_pools.connection()
    cur = conn.cursor()
    mask = ', '.join(['%s'] * len(msg_dict))  # 用于替换记录值
    cols = ', '.join(msg_dict.keys())  # 字段名
    sql = "INSERT INTO %s (%s) VALUES (%s)" % (_table, cols, mask)
    try:
        return cur.execute(sql, msg_dict.values())
    except Exception as e:
        print("ERROR {}\nINSERT INTO {} ERROR, RAW DICTIONARY {}".format(e, _table, msg_dict))
    finally:
        cur.close()
        conn.close()


def update_dict(_table, _msg_dict, predicates_keys=[], add_kvs={}, drop_keys=[]):
    """
    将Dictionary类型的Python对象更新数据库_table, 其中predicates_keys表示谓词，多个谓词之间采用and连接。
    add_kvs表示需要增加的属性值，drop_keys代表不需要的属性

    :param _table:表名
    :param _msg_dict:需要更新的msg字典对象
    :param predicates_keys:谓词字典，多个key value之间采用and连接
    :param add_kvs:需要增加的（key value）对
    :param drop_keys:需要删除的key
    :return:更新数据的行数
    """
    msg_dict = _msg_dict
    # 处理不需要的key
    if len(drop_keys) != 0:
        for key in drop_keys:
            if key in msg_dict:
                del msg_dict[key]
    # 添加需要的key value键值对
    if len(add_kvs) != 0:
        for key, value in add_kvs.items():
            msg_dict[key] = value

    update_kvs = []
    predicate_kvs = []
    for key, value in msg_dict.items():
        if isinstance(value, dict) or isinstance(value, list) or isinstance(value, tuple):
            print("[UPDATE IGNORED]Wrong KV=>key={}".format(key))
            continue
        connect_str = '\''
        if value is None or isinstance(value, int) or isinstance(value, float):
            connect_str = ''
            if value is None:
                value = 'NULL'
        else:
            MySQLdb.escape_string(value)
        if key in predicates_keys:
            predicate_kvs.append("{} = {}{}{}".format(key, connect_str, value, connect_str))
        else:
            update_kvs.append("{} = {}{}{}".format(key, connect_str, value, connect_str))
    sql = "UPDATE {} SET {} WHERE {}".format(_table, ", ".join(update_kvs), " AND ".join(predicate_kvs))
    conn = db_pools.connection()
    cur = conn.cursor()
    try:
        return cur.execute(sql)
    except Exception as e:
        print("ERROR {}\nUPDATE {} ERROR, SQL= {}".format(e, _table, sql))
    finally:
        cur.close()
        conn.close()


def get_max_appmsgid_by_fakeid(fakeid):
    """
    获取当前公众号的最大appmsgid
    :param fakeid:微信公众号的biz
    :return:最大的msg id
    """
    conn = db_pools.connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT MAX(appmsgid) FROM `article` WHERE fakeid = '{}'".format(fakeid))
        result = cur.fetchone()[0]
        if type(result) == int:
            return result
        else:
            return 0
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()
