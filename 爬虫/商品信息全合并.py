# import pandas as pd
#
#
# def merge_excel_files(full_category_path, product_detail_path, output_path):
#     # 1. 读取全品类数据 + 对“链接”去重（保留每个链接的第一条记录）
#     try:
#         df_full = pd.read_excel(full_category_path)
#         df_full = df_full[["链接", "标题", "品类"]]
#         # 关键步骤：按“链接”去重，只保留每个链接的第一条数据
#         df_full = df_full.drop_duplicates(subset="链接", keep="first")
#         print(f"✅ 读取全品类数据（已去重）：共 {len(df_full)} 条唯一商品信息")
#     except Exception as e:
#         print(f"❌ 读取全品类数据失败：{str(e)}")
#         return
#
#     # 2. 读取商品详情2
#     try:
#         df_detail = pd.read_excel(product_detail_path)
#         print(f"✅ 读取商品详情2：共 {len(df_detail)} 条商品信息")
#     except Exception as e:
#         print(f"❌ 读取商品详情2失败：{str(e)}")
#         return
#
#     # 3. 按“链接”合并（此时全品类数据无重复链接，不会膨胀）
#     df_merged = pd.merge(
#         df_detail,
#         df_full,
#         on="链接",
#         how="left"
#     )
#
#     # 4. 保存合并文件
#     try:
#         df_merged.to_excel(output_path, index=False)
#         print(f"\n✅ 合并完成！新文件已保存至：{output_path}")
#         print(f"✅ 合并后字段：商品详情2原有所有字段 + 新增“标题、品类”字段")
#
#         # 重新统计匹配情况
#         matched_count = df_merged["标题"].notna().sum()
#         print(f"\n📊 合并匹配统计：")
#         print(f"- 商品详情2总记录数：{len(df_detail)}")
#         print(f"- 成功匹配到标题/品类的记录数：{matched_count}")
#         print(f"- 未匹配到的记录数：{len(df_detail) - matched_count}")
#     except Exception as e:
#         print(f"❌ 保存合并文件失败：{str(e)}")
#         return
#
#
# if __name__ == "__main__":
#     # 替换为你的实际文件路径
#     FULL_CATEGORY_FILE = "惠农网全品类数据2.xlsx"
#     PRODUCT_DETAIL_FILE = "惠农网商品详情2.xlsx"
#     OUTPUT_FILE = "惠农网商品详情合并全品类.xlsx"
#
#     merge_excel_files(FULL_CATEGORY_FILE, PRODUCT_DETAIL_FILE, OUTPUT_FILE)


import pandas as pd


def merge_excel_files(full_category_path, product_detail_path, output_path):
    # 1. 读取全品类数据：提取核心列 + 链接去重（保留第一条，避免匹配时重复）
    try:
        df_full = pd.read_excel(full_category_path)
        # 仅保留需要映射的核心列，避免冗余
        df_full = df_full[["链接", "标题", "品类"]].copy()
        # 全品类表按链接去重，确保一个链接仅对应一条品类/标题信息
        df_full = df_full.drop_duplicates(subset="链接", keep="first")
        print(f"✅ 读取全品类数据（已去重）：共 {len(df_full)} 条唯一商品信息")
    except Exception as e:
        print(f"❌ 读取全品类数据失败：{str(e)}")
        return

    # 2. 读取商品详情表（主表）：核心操作→先按链接去重，保证主表链接唯一
    try:
        df_detail = pd.read_excel(product_detail_path)
        # 关键步骤1：主表按链接去重，保留第一条（保证最终结果每个链接仅出现一次）
        df_detail = df_detail.drop_duplicates(subset="链接", keep="first")
        print(f"✅ 读取商品详情：共 {len(df_detail)} 条唯一商品信息")
    except Exception as e:
        print(f"❌ 读取商品详情失败：{str(e)}")
        return

    # 3. 按“链接”左连接（以商品详情主表为基准，映射全品类的标题/品类）
    # 左连接特性：保留主表所有去重后的链接，全品类表匹配到则补充信息，匹配不到则为NaN
    df_merged = pd.merge(
        df_detail,          # 左表（主表）：商品详情去重后数据
        df_full,            # 右表：全品类去重后数据
        on="链接",           # 关联键：商品链接
        how="left",         # 左连接（核心：以主表为基准，不丢失主表数据）
        suffixes=("", "_全品类")  # 若两表有同名列，给全品类表的列加后缀（避免冲突）
    )

    # 4. 保存合并文件（保证无重复链接）
    try:
        df_merged.to_excel(output_path, index=False)
        print(f"\n✅ 合并完成！新文件已保存至：{output_path}")
        print(f"✅ 合并后字段：商品详情2原有所有字段 + 新增“标题、品类”字段（全品类映射）")

        # 精准统计匹配情况
        total_unique = len(df_detail)  # 主表去重后的总唯一链接数
        matched_count = df_merged["标题"].notna().sum()  # 成功匹配到全品类信息的链接数
        unmatched_count = total_unique - matched_count  # 未匹配到的链接数
        print(f"\n📊 合并匹配统计（按唯一链接）：")
        print(f"- 商品详情主表（去重后）总唯一链接数：{total_unique}")
        print(f"- 成功匹配全品类标题/品类的链接数：{matched_count}")
        print(f"- 未匹配到全品类信息的链接数：{unmatched_count}")
        print(f"- 匹配率：{matched_count / total_unique * 100:.2f}%")
    except Exception as e:
        print(f"❌ 保存合并文件失败：{str(e)}")
        return


if __name__ == "__main__":
    # 替换为你的实际文件路径（相对路径/绝对路径均可，绝对路径建议加r避免转义）
    FULL_CATEGORY_FILE = "惠农网全品类数据.xlsx"    # 全品类数据表
    PRODUCT_DETAIL_FILE = "惠农网商品详情.xlsx"     # 主表：商品详情表
    OUTPUT_FILE = "惠农网商品详情合并全品类.xlsx"  # 输出文件（加标识区分唯一链接）

    # 执行合并
    merge_excel_files(FULL_CATEGORY_FILE, PRODUCT_DETAIL_FILE, OUTPUT_FILE)