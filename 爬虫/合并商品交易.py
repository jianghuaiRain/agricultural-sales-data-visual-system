

import pandas as pd
import os
import re


# 1. 爬虫输出的成交数据Excel所在文件夹
FOLDER_PATH = r"D:\毕设\数据"
# 2. 商品详情分类表路径（p2文档）
CATEGORY_EXCEL_PATH = r"惠农网商品详情清洗.xlsx"

# 3. 中间/最终文件命名（无需改）
TEMP_MERGED_FILE = "惠农网成交数据整合.xlsx"  # 第一步整合后的临时文件
FINAL_OUTPUT_FILE = "惠农网成交数据整合2.xlsx"  # 最终完成文件


# ============================================================================

def merge_and_split_date():
    """第一步：整合所有成交Excel + 拆分成交时间为年月日"""
    print("=" * 80)
    print("开始第一步：整合成交数据并拆分时间")
    print("=" * 80)

    # 存储所有读取的Excel数据
    all_data = []
    # 遍历文件夹中的所有文件
    for file_name in os.listdir(FOLDER_PATH):
        # 只处理爬虫输出的成交数据Excel（匹配文件名前缀+后缀）
        if file_name.startswith("惠农网多品类成交数据_") and file_name.endswith(".xlsx"):
            file_path = os.path.join(FOLDER_PATH, file_name)
            try:
                # 读取Excel文件
                df = pd.read_excel(file_path)
                all_data.append(df)
                print(f"✅ 成功读取：{file_name}（数据量：{len(df)}条）")
            except Exception as e:
                print(f"❌ 读取失败：{file_name}，原因：{str(e)[:50]}")

    # 检查是否读取到数据
    if not all_data:
        print("⚠️  未找到符合要求的Excel文件，请检查文件夹路径和文件名！")
        return None

    # 1. 合并所有Excel数据
    merged_df = pd.concat(all_data, ignore_index=True)
    print(f"\n📊 所有文件合并完成，合并后总数据量：{len(merged_df)}条")

    # 2. 数据清洗：去重 + 过滤关键列空值
    # 按唯一标识去重（商品链接+成交时间+采购量，避免重复数据）
    cleaned_df = merged_df.drop_duplicates(
        subset=["商品链接", "成交时间", "采购量"],
        keep="first"
    )
    # 过滤关键列（商品链接、成交时间、采购量）为空的数据
    cleaned_df = cleaned_df.dropna(subset=["商品链接", "成交时间", "采购量"])
    print(f"🧹 数据清洗完成，去重后有效数据量：{len(cleaned_df)}条")

    # 3. 拆分成交时间为【年/月/日】三列
    # 转换为时间格式（errors='coerce'：无法转换的标记为NaN，后续过滤）
    cleaned_df["成交时间_标准化"] = pd.to_datetime(cleaned_df["成交时间"], errors="coerce")
    # 拆分年、月、日（新增三列）
    cleaned_df["采购年"] = cleaned_df["成交时间_标准化"].dt.year
    cleaned_df["采购月"] = cleaned_df["成交时间_标准化"].dt.month
    cleaned_df["采购日"] = cleaned_df["成交时间_标准化"].dt.day
    # 过滤时间转换失败的无效数据
    cleaned_df = cleaned_df.dropna(subset=["采购年", "采购月", "采购日"])
    # 删去中间标准化列（无需保留）
    cleaned_df = cleaned_df.drop(columns=["成交时间_标准化"])
    # 重置索引
    cleaned_df = cleaned_df.reset_index(drop=True)
    print(f"📅 成交时间拆分完成，第一步处理后数据量：{len(cleaned_df)}条")

    # 保存第一步结果（临时文件）
    cleaned_df.to_excel(TEMP_MERGED_FILE, index=False)
    print(f"\n✅ 第一步完成！临时文件已保存至：{TEMP_MERGED_FILE}")
    return cleaned_df


def match_category_and_unify_unit(merged_df):
    """第二步：匹配品类、二级分类、品种名 + 统一采购单位为斤"""
    print("\n" + "=" * 80)
    print("开始第二步：匹配品类并统一采购单位")
    print("=" * 80)

    # 1. 读取商品分类表（p2），提取“链接-品类-二级分类-品种名”的映射
    try:
        category_df = pd.read_excel(CATEGORY_EXCEL_PATH)[["链接", "品类", "二级分类", "品种名"]]
    except FileNotFoundError:
        print(f"❌ 商品分类表不存在：{CATEGORY_EXCEL_PATH}，请检查路径！")
        return

    # 修复：商品分类表按链接去重，避免索引重复
    category_df = category_df.drop_duplicates(subset=["链接"], keep="first")
    # 构建链接到分类的字典映射（避免重复匹配）
    category_map = category_df.set_index("链接").to_dict("index")

    print(f"✅ 读取商品分类表（去重后）：{len(category_df)}条")
    print(f"✅ 待匹配成交数据：{len(merged_df)}条")

    # 2. 匹配品类、二级分类、品种名（通过商品链接）
    def get_category_info(link):
        # 从映射中取对应信息，无匹配则返回空
        info = category_map.get(link, {})
        return info.get("品类", ""), info.get("二级分类", ""), info.get("品种名", "")

    # 新增三列：品类、二级分类、品种名
    merged_df[["品类", "二级分类", "品种名"]] = merged_df["商品链接"].apply(
        lambda x: pd.Series(get_category_info(x))
    )
    print(f"📌 品类匹配完成，已新增品类/二级分类/品种名列")

    # 3. 提取采购单位 + 统一为“斤”
    # 提取采购量的数值和单位
    merged_df["采购量数值"] = merged_df["采购量"].str.extract(r"(\d+)").astype(float)  # 提取数字
    merged_df["原始单位"] = merged_df["采购量"].str.extract(r"(\D+)$").fillna("")  # 提取末尾单位，空值填充

    # 定义单位转换规则（统一为“斤”）
    unit_convert_rules = {
        "斤": 1,  # 本身是斤，无需转换
        "公斤": 2,  # 1公斤=2斤
        "箱": 10,  # 重点：1箱=10斤
        "袋": 5,
        "棵": 1,
        "只": 1,
        "件": 5,
    }

    # 转换为以“斤”为单位的数值
    def convert_to_jin(row):
        unit = row["原始单位"].strip()  # 去除单位前后空格，避免匹配失败
        value = row["采购量数值"]
        if pd.isna(value):  # 处理空值
            return None
        if unit in unit_convert_rules:
            return value * unit_convert_rules[unit]
        return value  # 无规则则保留原数值

    merged_df["统一单位（斤）"] = merged_df.apply(convert_to_jin, axis=1)
    print(f"📏 采购单位已统一为“斤”（箱自动换算为10斤）")

    # 4. 数据清洗（过滤无品类/无单位的无效行）
    final_df = merged_df.dropna(subset=["品类", "统一单位（斤）"])
    # 过滤品类为空的行
    final_df = final_df[final_df["品类"] != ""]
    # 重置索引
    final_df = final_df.reset_index(drop=True)
    print(f"🧹 最终数据清洗完成，有效数据量：{len(final_df)}条")

    # 5. 保存最终结果
    final_df.to_excel(FINAL_OUTPUT_FILE, index=False)
    print(f"\n🎉 全部处理完成！最终结果已保存至：{FINAL_OUTPUT_FILE}")
    print(f"📋 最终数据包含列：{list(final_df.columns)}")


if __name__ == "__main__":
    # 执行第一步：整合数据+拆分时间
    first_step_df = merge_and_split_date()

    # 如果第一步成功，执行第二步：匹配品类+统一单位
    if first_step_df is not None and len(first_step_df) > 0:
        match_category_and_unify_unit(first_step_df)
    else:
        print("\n❌ 第一步处理失败，终止执行！")