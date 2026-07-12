from pymysql import *

# 核心修改：将 database 参数改为 huinong_data
conn = connect(
    host='localhost',    # 如果你的数据库不是本地，请替换为实际IP
    user='root',         # 请根据你的数据库实际用户名填写
    password='123456',     # 请根据你的数据库实际密码填写
    database='huinong_data',  # 替换为目标数据库名
    port=3306
)
cursor = conn.cursor()

def querys(sql,params,type='no_select'):
    params = tuple(params)
    cursor.execute(sql,params)
    if type != 'no_select':
        data_list = cursor.fetchall()
        conn.commit()
        return data_list
    else:
        conn.commit()
        return '数据库语句执行成功'