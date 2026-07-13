# 拆分省市
import asyncio
import aiohttp
from lxml import etree
import pandas as pd
from tqdm.asyncio import tqdm_asyncio
import time
import random
import re  # 用于提取价格数字、处理发货地拆分
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HuiNongSpider:
    def __init__(self, max_concurrent=10, timeout=60):
        self.max_concurrent = max_concurrent
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.semaphore = asyncio.Semaphore(max_concurrent)

    def load_urls(self, excel_path):
        """加载URL列表"""
        df = pd.read_excel(excel_path)
        urls = df['链接'].tolist()
        urls = [url for url in urls if pd.notna(url) and isinstance(url, str) and url.strip()]
        return urls

    # ================ ✅ 新增核心函数：获取【仅新增】的URL（增量核心） ================
    def get_incremental_urls(self, source_excel, result_excel):
        """
        对比源表和结果表，只返回 新增未爬取 的URL
        :param source_excel: 惠农网全品类数据2.xlsx (源URL表)
        :param result_excel: 惠农网商品详情2.xlsx (已爬详情表)
        :return: 仅新增的、待爬取的URL列表
        """
        # 加载源表所有URL
        all_source_urls = self.load_urls(source_excel)
        # 去重源表URL，防止源表本身有重复链接
        all_source_urls = list(set(all_source_urls))
        logger.info(f"源文件【{source_excel}】共加载到 {len(all_source_urls)} 个去重后的商品URL")

        # 如果结果表不存在 → 返回全部URL（首次爬取逻辑）
        if not pd.io.common.file_exists(result_excel):
            logger.info(f"结果文件【{result_excel}】不存在，本次爬取【全部URL】")
            return all_source_urls

        # 加载结果表中【已爬取】的URL
        df_result = pd.read_excel(result_excel)
        crawled_urls = df_result['链接'].tolist()
        crawled_urls = [url for url in crawled_urls if pd.notna(url) and isinstance(url, str) and url.strip()]
        crawled_urls = set(crawled_urls)
        logger.info(f"结果文件【{result_excel}】共加载到 {len(crawled_urls)} 个已爬取的商品URL")

        # 求差集：源表有、结果表没有 → 【仅新增】的URL
        incremental_urls = [url for url in all_source_urls if url not in crawled_urls]
        logger.info(f"✅ 本次筛选出【新增未爬取】的URL数量：{len(incremental_urls)} 个")
        return incremental_urls

    def extract_all_specifications(self, content):
        """提取所有规格信息并合并为一个字符串"""
        spec_container = content.xpath('//div[@class="batch-num mar spec-bg"]')
        if not spec_container:
            return "无规格信息"
        spec_items = content.xpath('//div[@class="spec-items flex-c"]')
        all_specs = []
        for item in spec_items:
            name = item.xpath('.//div[@class="s-name"]/text()')
            price = item.xpath('.//div[@class="s-price"]/text()')
            unit = item.xpath('.//div[@class="s-unit"]/text()')
            name_text = name[0].strip() if name else "未知规格"
            price_text = price[0].strip() if price else "价格未知"
            unit_text = unit[0].strip() if unit else "起批量未知"
            spec_text = f"{name_text} - {price_text} ({unit_text})"
            all_specs.append(spec_text)
        return "；".join(all_specs)

    # ✅ 价格拆分：拆分为最低单价、最高单价、均价
    def split_price(self, price_str):
        if price_str in ["无价格信息", "解析失败", "请求失败"] or not price_str:
            return 0.0, 0.0, 0.0
        num_list = re.findall(r"\d+\.?\d*", str(price_str))
        num_list = [float(num) for num in num_list]

        if len(num_list) >= 2:
            min_price = round(num_list[0], 2)
            max_price = round(num_list[1], 2)
            avg_price = round((min_price + max_price) / 2, 2)
        elif len(num_list) == 1:
            single_price = round(num_list[0], 2)
            min_price = single_price
            max_price = single_price
            avg_price = single_price
        else:
            min_price = 0.0
            max_price = 0.0
            avg_price = 0.0
        return min_price, max_price, avg_price

    # ✅ 调整核心：发货地拆分（省份为完整名，市仅保留城市名）
    def split_address(self, address_str):
        """
        拆分发货地为 省份（完整名）、市（仅城市名）、区县 三个字段
        适配场景：① 河南省平顶山市鲁山县 → 省份=河南省、市=平顶山市、区县=鲁山县
                  ② 山东省临沂市 → 省份=山东省、市=临沂市、区县=未知
                  ③ 云南省 → 省份=云南省、市=未知、区县=未知
        """
        # 异常值直接返回 未知-未知-未知
        if address_str in ["无发货地信息", "解析失败", "请求失败"] or not address_str or address_str.strip() == "":
            return "未知", "未知", "未知"

        addr = address_str.strip()
        # 匹配全国完整省份名（含“省/自治区/直辖市”）
        province_key = [
            "北京市", "天津市", "上海市", "重庆市",
            "河北省", "山西省", "辽宁省", "吉林省", "黑龙江省",
            "江苏省", "浙江省", "安徽省", "福建省", "江西省", "山东省", "河南省", "湖北省", "湖南省",
            "广东省", "广西壮族自治区", "海南省", "四川省", "贵州省", "云南省",
            "陕西省", "甘肃省", "青海省", "内蒙古自治区", "宁夏回族自治区", "新疆维吾尔自治区", "西藏自治区"
        ]

        province = "未知"
        city = "未知"
        district = "未知"

        # 第一步：提取完整省份名
        for p in province_key:
            if addr.startswith(p):
                province = p
                addr = addr[len(p):]  # 去掉省份后，剩余部分是“市+区县”
                break

        # 第二步：提取市（仅保留城市名）
        if len(addr) > 0:
            if "市" in addr or "州" in addr or "盟" in addr:
                # 拆分出“市/州/盟”前的城市名
                city_split = re.split(r'市|州|盟', addr, 1)
                city_name = city_split[0].strip()
                # 拼接成“平顶山市”“西双版纳州”这类格式
                city_suffix = "市" if "市" in addr else "州" if "州" in addr else "盟"
                city = f"{city_name}{city_suffix}"
                # 提取区县
                district = city_split[1].strip() if len(city_split) > 1 else "未知"
                if district == "":
                    district = "未知"
            else:
                # 无市级时，剩余内容为区县
                district = addr.strip()

        return province, city, district

    def parse_content(self, content, url):
        """解析页面内容（仅保留品种名）"""
        try:
            price = content.xpath('//div[@class="active-p"]/text()')
            qipi_num = content.xpath('//div[@class="flex-c batch-item"]/div/text()')
            fahuodi = content.xpath(
                '//div[contains(@class, "batch-num") and contains(., "发货地址")]/div[@class="line-val"]/text()')
            dealed = content.xpath('//div[@class="line-val" and contains(., "成交")]/span[@class="s1"]/text()')
            specifications = self.extract_all_specifications(content)

            # 解析品种名
            attrs_items = content.xpath('//div[@class="detail-attrs-item"]')
            variety_name = "无"
            for item in attrs_items:
                attr_label = item.xpath('.//div[@class="t1"]/text()')
                if not attr_label:
                    continue
                attr_label = attr_label[0].strip()
                if attr_label == "品种名":
                    attr_value = item.xpath('.//div[@class="t2"]/text()')
                    variety_name = attr_value[0].strip() if attr_value else "无"

            # 原始字段取值
            raw_price = price[0].strip() if price else "无价格信息"
            raw_address = fahuodi[0].strip() if fahuodi else "无发货地信息"

            # ✅ 调用价格拆分
            min_price, max_price, avg_price = self.split_price(raw_price)
            # ✅ 调用发货地拆分（省份完整名+市仅城市名）
            province, city, district = self.split_address(raw_address)

            return {
                '链接': url,
                '价格': raw_price,  # 保留原始价格
                '最低单价': min_price,  # 新增价格字段1
                '最高单价': max_price,  # 新增价格字段2
                '均价': avg_price,  # 新增价格字段3
                '起批量': qipi_num[0].strip() if qipi_num else "无起批量信息",
                '发货地': raw_address,  # 保留原始发货地
                '省份': province,  # 完整省份名（如“河南省”）
                '市': city,  # 仅城市名（如“平顶山市”）
                '区县': district,  # 区县名
                '成交': dealed[0].strip() if dealed else "无成交信息",
                '规格': specifications,
                '品种名': variety_name
            }
        except Exception as e:
            logger.error(f"解析页面内容失败 {url}: {str(e)}")
            # 异常返回-补充所有新增字段，保证Excel列完整
            return {
                '链接': url,
                '价格': "解析失败",
                '最低单价': 0.0,
                '最高单价': 0.0,
                '均价': 0.0,
                '起批量': "解析失败",
                '发货地': "解析失败",
                '省份': "未知",
                '市': "未知",
                '区县': "未知",
                '成交': "解析失败",
                '规格': "解析失败",
                '品种名': "无"
            }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        before_sleep=lambda retry_state: logger.warning(
            f"第{retry_state.attempt_number}次重试: {retry_state.outcome.exception()}")
    )
    async def fetch_url(self, session, url, pbar):
        """获取单个URL的内容，包含重试机制"""
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
            'Cookie': 'deviceId=e2e918e-5c55-48db-8400-c171803cf; Hm_lvt_b99541cbfb0edd202bb49abf3a0bef84=1762239771,1762417484; Hm_lvt_b2daa4a53a78af99c4a57c440f46d069=1763467426; sessionId=S_0MJ14V2VY4TLN49D; Hm_lvt_0e023fed85d2150e7d419b5b1f2e7c0f=1763467071,1765439109; HMACCOUNT=F1D67AF373D4EF14; Hm_lvt_91cf34f62b9bedb16460ca36cf192f4c=1763463548,1765439110; Hm_lvt_a6458082fb548e5ca7ff77d177d2d88d=1763463548,1765439110; hnUserTicket=58ed88d8-a4de-4a78-9abd-d52fd8eaf898; hnUserId=781226109; tfstk=gbnnpXxZr2zBMWSC-LqB8lRI2NLOAkZ77bI8wuFy75P196IKU70oOfp7zBZKqfcs1XHKekWI5jHVvDLQ2gqQVuRvMnKxpvZ74hW7n55C78w22MPFYkZZ7iliMnKxdvWLLKHwD2LNzdyzauzUzNSa1-Pz477eI5yuha5EauJMI-wR4azUTN-aU8EzabryIAP_UuyrauJiQ5wrMZ_UO0oKbQUmdP7q6nmaKyVqLWkKBcW38wMasgjoj2z3ggVG4gogKYzTXhSDySub9rFs_hI3qAyoi-ch_CqrIDi07DR1qjciul2s5Qbui4kKl4zMLHkgxW4mXyxW9k0rO04I-T9jQklslSae5CwivmUuGPfwTAHgTr0o9Csz9qDZsrnO6iEZ3VqG4r7NuFnfVRJ-ja_78RwgMhMWwj6C6KOJIdbVFyy_LSpMIa_78RwgMdvGogaUCJPA.; Hm_lpvt_a6458082fb548e5ca7ff77d177d2d88d=1765439168; Hm_lpvt_91cf34f62b9bedb16460ca36cf192f4c=1765439176; Hm_lpvt_0e023fed85d2150e7d419b5b1f2e7c0f=1765439176',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.cnhnb.com/',
            'Connection': 'keep-alive'
        }

        async with self.semaphore:
            try:
                async with session.get(url, headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        html = await response.text()
                        content = etree.HTML(html)
                        data = self.parse_content(content, url)
                        await asyncio.sleep(random.uniform(2, 5))
                        pbar.update(1)
                        return data
                    else:
                        raise aiohttp.ClientError(f"HTTP状态码错误: {response.status}")
            except Exception as e:
                logger.error(f"请求失败 {url}: {str(e)}")
                pbar.update(1)
                # 请求失败-补充所有新增字段，保证Excel列完整
                return {
                    '链接': url,
                    '价格': "请求失败",
                    '最低单价': 0.0,
                    '最高单价': 0.0,
                    '均价': 0.0,
                    '起批量': "请求失败",
                    '发货地': "请求失败",
                    '省份': "未知",
                    '市': "未知",
                    '区县': "未知",
                    '成交': "请求失败",
                    '规格': "请求失败",
                    '品种名': "无"
                }

    async def process_urls(self, urls):
        """处理所有URL"""
        connector = aiohttp.TCPConnector(limit=self.max_concurrent, limit_per_host=5)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            with tqdm_asyncio(total=len(urls), desc="增量爬取进度") as pbar:
                for url in urls:
                    task = asyncio.create_task(self.fetch_url(session, url, pbar))
                    tasks.append(task)
                results = await asyncio.gather(*tasks, return_exceptions=True)
            valid_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"任务执行异常: {str(result)}")
                else:
                    valid_results.append(result)
            return valid_results

    # ================ ✅ 修改核心函数：增量追加写入，不覆盖历史数据 ================
    async def run(self, excel_path, output_filename):
        """运行爬虫 - 增量版"""
        logger.info("===== 开始增量爬取准备 =====")
        # 1. 获取【仅新增】的URL
        incremental_urls = self.get_incremental_urls(excel_path, output_filename)

        # 如果没有新增URL，直接结束程序
        if len(incremental_urls) == 0:
            logger.info("✅ 无任何新增URL需要爬取，程序结束！")
            return

        logger.info("开始异步增量爬取...")
        start_time = time.time()
        new_crawl_data = await self.process_urls(incremental_urls)
        end_time = time.time()
        success_count = len([d for d in new_crawl_data if d.get('价格') not in ['请求失败', '解析失败']])
        logger.info(f"增量爬取完成，耗时: {end_time - start_time:.2f}秒")
        logger.info(f"本次新增成功爬取: {success_count} 条数据")

        # 2. 增量追加写入：如果文件存在则追加，不存在则新建
        if pd.io.common.file_exists(output_filename):
            # 读取历史数据 + 合并新数据 + 保存
            old_df = pd.read_excel(output_filename)
            new_df = pd.DataFrame(new_crawl_data)
            final_df = pd.concat([old_df, new_df], ignore_index=True)
            final_df.to_excel(output_filename, index=False)
            logger.info(f"✅ 新数据已【追加】到 {output_filename} 末尾，总数据量: {len(final_df)} 条")
        else:
            # 首次爬取，直接保存
            result_df = pd.DataFrame(new_crawl_data)
            result_df.to_excel(output_filename, index=False)
            logger.info(f"✅ 首次爬取，数据已保存到 '{output_filename}'")


async def main():
    """主函数"""
    spider = HuiNongSpider(max_concurrent=10, timeout=60)
    try:
        await spider.run('惠农网全品类数据.xlsx', '惠农网商品详情.xlsx')
    except Exception as e:
        logger.error(f"程序执行异常: {str(e)}")
    finally:
        logger.info("增量爬取程序执行完成")


if __name__ == "__main__":
    asyncio.run(main())