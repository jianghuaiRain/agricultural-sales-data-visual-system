

import pandas as pd
from sqlalchemy import create_engine

# ========== 你的MySQL配置 ==========
MYSQL_USER = "root"
MYSQL_PASSWORD = "123456"
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_DB = "huinong_data"

# 全局变量
df_category = None
df_product = None
df_region = None
df_transaction = None
df_user = None


# 初始化数据库数据
def init_db_data():
    global df_category, df_product, df_region, df_transaction, df_user
    try:
        con = create_engine(f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}")

        # 读取各表，并给product/category表的字段加前缀（避免和transaction字段冲突）
        df_category = pd.read_sql('select * from category', con)
        df_category.columns = [f"cate_{col}" for col in df_category.columns]  # 品类表字段加cate_前缀

        df_product = pd.read_sql('select * from product', con)
        df_product.columns = [f"prod_{col}" for col in df_product.columns]  # 产品表字段加prod_前缀

        df_region = pd.read_sql('select * from region', con)
        df_transaction = pd.read_sql('select * from transaction', con)
        df_user = pd.read_sql('select * from user', con)

        print("✅ 数据库表读取成功！")
        print(f"地区表字段：{df_region.columns.tolist()}")
        print(f"交易表字段：{df_transaction.columns.tolist()}")
    except Exception as e:
        print(f"❌ 数据库读取失败：{e}")


# 核心：关联多表（强制保留region_id）
def get_merged_data():
    if df_transaction is None:
        init_db_data()

    # 1. 交易表关联产品表（用prod_product_id匹配）
    # 先确认产品表的产品ID字段名（加了prod_前缀）
    df_t_p = pd.merge(
        df_transaction,  # 左表：交易表（保留region_id）
        df_product,  # 右表：产品表（字段加了前缀）
        left_on="product_id",
        right_on="prod_product_id",
        how="left"
    )
    print(f"✅ 交易表+产品表后字段：{df_t_p.columns.tolist()}")  # 验证region_id还在

    # 2. 关联品类表（用prod_category_id匹配）
    df_t_p_c = pd.merge(
        df_t_p,  # 左表：交易+产品
        df_category,  # 右表：品类表（字段加了前缀）
        left_on="prod_category_id",
        right_on="cate_category_id",
        how="left"
    )
    print(f"✅ 交易+产品+品类后字段：{df_t_p_c.columns.tolist()}")  # 验证region_id还在

    # 3. 关联地区表（直接用transaction的region_id）
    df_merged = pd.merge(
        df_t_p_c,
        df_region,
        on="region_id",
        how="left"
    )

    # 填充空值
    df_merged = df_merged.fillna({
        "prod_product_name": "未知产品",
        "cate_category_name": "未知大类",
        "cate_sub_category_name": "未知小类",
        "province": "未知省份",
        "city": "未知城市",
        "quantity_value": 0
    })
    return df_merged


# 测试
if __name__ == "__main__":
    init_db_data()
    test_merged = get_merged_data()
    print("\n=== 最终关联表字段 ===")
    print(test_merged.columns.tolist())

# （在utils.py末尾添加）
def get_all_product_count():
    """获取product表的所有商品总数（不管是否有交易）"""
    if df_product is None:
        init_db_data()
    return len(df_product)  # product表的总记录数（product_id是主键，直接len即可）

def get_product_table():
    if df_product is None:
        init_db_data()
    return df_product

def get_region_table():
    if df_region is None:
        init_db_data()
    return df_region

def get_category_table():
    if df_category is None:
        init_db_data()
    return df_category

