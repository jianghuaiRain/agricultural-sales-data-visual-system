
#清洗无效数据
import pandas as pd

def clean_invalid_records(input_file="惠农网商品详情清洗2.xlsx", output_file="惠农网商品详情清洗3.xlsx"):
    """
    仅删除含「请求失败」的商品记录（多字段识别：batch_quantity/price/ship_from）
    :param input_file: 原始文件路径
    :param output_file: 清洗后保存路径
    :return: 清洗后的DataFrame
    """
    # 1. 读取Excel文件（兼容.xlsx/.xls格式，sheet_name=Sheet1保持不变）
    try:
        df = pd.read_excel(input_file, sheet_name="Sheet1", engine="openpyxl")
    except Exception as e:
        df = pd.read_excel(input_file, sheet_name="Sheet1", engine="xlrd")
    print(f"✅ 成功读取P2文档，原始记录总数：{len(df)} 条")

    # 2. 定义无效记录条件：仅识别多字段中含「请求失败」的记录（完全贴合你的需求）
    invalid_conditions = (
        df["batch_quantity"].str.contains("请求失败", na=False)
        | df["price"].str.contains("请求失败", na=False)
        | df["ship_from"].str.contains("请求失败", na=False)
    )

    # 3. 过滤无效记录（保留有效数据，重置索引）
    df_cleaned = df[~invalid_conditions].reset_index(drop=True)

    # 4. 保存清洗后的数据
    df_cleaned.to_excel(output_file, index=False, engine="openpyxl")

    # 5. 打印清洗统计结果
    deleted_count = len(df) - len(df_cleaned)
    print(f"\n📊 清洗结果统计：")
    print(f"- 原始记录数：{len(df)} 条")
    print(f"- 删除含「请求失败」记录数：{deleted_count} 条")
    print(f"- 清洗后有效记录数：{len(df_cleaned)} 条")
    print(f"\n✅ 清洗完成！有效数据已保存至：{output_file}")

    # 可选：显示被删除的无效记录明细（仅保留存在的列，避免KeyError）
    if len(df[invalid_conditions]) > 0:
        print(f"\n📌 被删除的「请求失败」记录明细（共{deleted_count}条，前10条）：")
        # 只引用确定存在的列，避免未知列名报错
        deleted_records = df[invalid_conditions][["product_link", "price", "ship_from", "batch_quantity"]].head(10)
        print(deleted_records.to_string(index=False))
    else:
        print(f"\n📌 未检测到含「请求失败」的记录，所有数据均有效！")

    return df_cleaned

# -------------------------- 执行清洗 --------------------------
if __name__ == "__main__":
    cleaned_df = clean_invalid_records(
        input_file="惠农网商品详情精准分类.xlsx",
        output_file="惠农网商品详情清洗.xlsx"
    )