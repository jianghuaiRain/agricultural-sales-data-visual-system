
if __name__ == "__main__":
    from utils1.utils import get_merged_data, get_all_product_count, get_product_table, get_region_table
else:
    from .utils import get_merged_data, get_all_product_count, get_product_table, get_region_table

def getHomeData():
    # 1. 获取数据（包含产品信息、交易记录、地区信息等）
    df_all = get_merged_data()
    if df_all is None or df_all.empty:
        return "关联后的数据集为空"

    # 2. 计算核心指标
    ## ① 商品总数：改为product表的所有产品数
    product_total = get_all_product_count()  # 替换原来的df_merged统计

    ## ② 销量最高品种（过滤掉无效数据，按全量二级分类的销量总数，单位：斤）
    invalid_categories = {"无", "未知", "未知小类", "其他品类", ""}
    df_valid_cat = df_all[~df_all["cate_sub_category_name"].isin(invalid_categories)]
    cat_sales = df_valid_cat.groupby("cate_sub_category_name")["quantity_value"].sum().reset_index()
    if cat_sales.empty:
        top_product = {"名称": "无销量数据", "总销量": 0}
    else:
        row = cat_sales.loc[cat_sales["quantity_value"].idxmax()]
        top_product = {"名称": row["cate_sub_category_name"], "总销量": int(row["quantity_value"])}

    ## ③ 畅销品类（成交单数最多的二级分类：按交易记录条数统计）
    df_c = df_valid_cat
    cat_counts = df_c.groupby("cate_sub_category_name").size().reset_index(name="count")
    if cat_counts.empty:
        top_category = {"名称": "无销量数据", "总销量": 0}
    else:
        row = cat_counts.loc[cat_counts["count"].idxmax()]
        top_category = {"名称": row["cate_sub_category_name"], "总销量": int(row["count"])}

    ## ④ 最热门地区（基于产品表的 region_id 映射到地区表的城市，统计出现次数最多的城市）
    df_prod = get_product_table()
    df_reg = get_region_table()
    if df_prod is None or df_prod.empty or df_reg is None or df_reg.empty:
        top_region = {"名称": "无销量数据", "总销量": 0}
    else:
        col_rid = "prod_region_id" if "prod_region_id" in df_prod.columns else ("region_id" if "region_id" in df_prod.columns else None)
        if not col_rid:
            top_region = {"名称": "无销量数据", "总销量": 0}
        else:
            rid_counts = df_prod[col_rid].value_counts()
            if rid_counts.empty:
                top_region = {"名称": "无销量数据", "总销量": 0}
            else:
                rid_top = rid_counts.index[0]
                # 通过地区表映射到城市名；若城市缺失，用省份名代替
                row = df_reg[df_reg["region_id"] == rid_top]
                if row.empty:
                    name = str(rid_top)
                else:
                    name = str(row.iloc[0]["city"]) if str(row.iloc[0].get("city", "")).strip() else str(row.iloc[0].get("province", ""))
                top_region = {"名称": name, "总销量": int(rid_counts.iloc[0])}

    # 3. 整理结果
    result = {
        "商品总数（所有产品）": product_total,  # 备注清楚是所有产品
        "有交易记录的商品数": df_all["prod_product_id"].nunique() if df_all is not None and not df_all.empty else 0,  # 可保留这个指标（可选）
        "销量最高品种": top_product,
        "畅销品类": top_category,
        "最热门地区": top_region
    }
    return result

# 运行测试
if __name__ == "__main__":
    home_data = getHomeData()
    print("=== 农产品核心分析数据 ===")
    for key, value in home_data.items():
        if isinstance(value, dict):
            print(f"{key}：{value['名称']}（总销量：{value['总销量']}）")
        else:
            print(f"{key}：{value}")
