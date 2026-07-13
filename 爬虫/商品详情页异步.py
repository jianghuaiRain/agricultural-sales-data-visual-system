# import asyncio
# import aiohttp
# from lxml import etree
# import pandas as pd
# from tqdm.asyncio import tqdm_asyncio
# import time
# import random
# from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
# import logging
#
# # 配置日志
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
#
#
# class HuiNongSpider:
#     def __init__(self, max_concurrent=5, timeout=30):
#         self.max_concurrent = max_concurrent
#         self.timeout = aiohttp.ClientTimeout(total=timeout)
#         self.semaphore = asyncio.Semaphore(max_concurrent)
#
#     def load_urls(self, excel_path, limit=1000):
#         """加载URL列表"""
#         df = pd.read_excel(excel_path)
#         urls = df['链接'].tolist()
#         return urls[:limit]
#
#     def extract_all_specifications(self, content):
#         """提取所有规格信息并合并为一个字符串"""
#         spec_container = content.xpath('//div[@class="batch-num mar spec-bg"]')
#
#         if not spec_container:
#             return "无规格信息"
#
#         spec_items = content.xpath('//div[@class="spec-items flex-c"]')
#         all_specs = []
#
#         for item in spec_items:
#             name = item.xpath('.//div[@class="s-name"]/text()')
#             price = item.xpath('.//div[@class="s-price"]/text()')
#             unit = item.xpath('.//div[@class="s-unit"]/text()')
#
#             name_text = name[0].strip() if name else "未知规格"
#             price_text = price[0].strip() if price else "价格未知"
#             unit_text = unit[0].strip() if unit else "起批量未知"
#
#             spec_text = f"{name_text} - {price_text} ({unit_text})"
#             all_specs.append(spec_text)
#
#         return "；".join(all_specs)
#
#     def parse_content(self, content, url):
#         """解析页面内容"""
#         try:
#             price = content.xpath('//div[@class="active-p"]/text()')
#             qipi_num = content.xpath('//div[@class="flex-c batch-item"]/div/text()')
#             fahuodi = content.xpath(
#                 '//div[contains(@class, "batch-num") and contains(., "发货地址")]/div[@class="line-val"]/text()')
#             xunjia = content.xpath("//div[@class='line-val' and contains(., '询价')]/span[@class='s1']/text()")
#             dealed = content.xpath('//div[@class="line-val" and contains(., "成交")]/span[@class="s1"]/text()')
#             conment_nun = content.xpath('//div[@class="line-val" and contains(., "评价")]/span[@class="s1"]/text()')
#             specifications = self.extract_all_specifications(content)
#
#             return {
#                 '链接': url,
#                 '价格': price[0].strip() if price else "无价格信息",
#                 '起批量': qipi_num[0].strip() if qipi_num else "无起批量信息",
#                 '发货地': fahuodi[0].strip() if fahuodi else "无发货地信息",
#                 '询价': xunjia[0].strip() if xunjia else "无询价信息",
#                 '成交': dealed[0].strip() if dealed else "无成交信息",
#                 '评价': conment_nun[0].strip() if conment_nun else "无评价信息",
#                 '规格': specifications
#             }
#         except Exception as e:
#             logger.error(f"解析页面内容失败 {url}: {str(e)}")
#             return {
#                 '链接': url,
#                 '价格': "解析失败",
#                 '起批量': "解析失败",
#                 '发货地': "解析失败",
#                 '询价': "解析失败",
#                 '成交': "解析失败",
#                 '评价': "解析失败",
#                 '规格': "解析失败"
#             }
#
#     @retry(
#         stop=stop_after_attempt(3),  # 最多重试3次
#         wait=wait_exponential(multiplier=1, min=2, max=10),  # 指数退避等待
#         retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
#         before_sleep=lambda retry_state: logger.warning(
#             f"第{retry_state.attempt_number}次重试: {retry_state.outcome.exception()}")
#     )
#     async def fetch_url(self, session, url, pbar):
#         """获取单个URL的内容，包含重试机制"""
#         headers = {
#             'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
#             'Cookie': 'deviceId=e2e918e-5c55-48db-8400-c171803cf; Hm_lvt_b99541cbfb0edd202bb49abf3a0bef84=1762239771,1762417484; Hm_lvt_b2daa4a53a78af99c4a57c440f46d069=1763467426; sessionId=S_0MJ14V2VY4TLN49D; Hm_lvt_0e023fed85d2150e7d419b5b1f2e7c0f=1763467071,1765439109; HMACCOUNT=F1D67AF373D4EF14; Hm_lvt_91cf34f62b9bedb16460ca36cf192f4c=1763463548,1765439110; Hm_lvt_a6458082fb548e5ca7ff77d177d2d88d=1763463548,1765439110; hnUserTicket=58ed88d8-a4de-4a78-9abd-d52fd8eaf898; hnUserId=781226109; tfstk=gbnnpXxZr2zBMWSC-LqB8lRI2NLOAkZ77bI8wuFy75P196IKU70oOfp7zBZKqfcs1XHKekWI5jHVvDLQ2gqQVuRvMnKxpvZ74hW7n55C78w22MPFYkZZ7iliMnKxdvWLLKHwD2LNzdyzauzUzNSa1-Pz477eI5yuha5EauJMI-wR4azUTN-aU8EzabryIAP_UuyrauJiQ5wrMZ_UO0oKbQUmdP7q6nmaKyVqLWkKBcW38wMasgjoj2z3ggVG4gogKYzTXhSDySub9rFs_hI3qAyoi-ch_CqrIDi07DR1qjciul2s5Qbui4kKl4zMLHkgxW4mXyxW9k0rO04I-T9jQklslSae5CwivmUuGPfwTAHgTr0o9Csz9qDZsrnO6iEZ3VqG4r7NuFnfVRJ-ja_78RwgMhMWwj6C6KOJIdbVFyy_LSpMIa_78RwgMdvGogaUCJPA.; Hm_lpvt_a6458082fb548e5ca7ff77d177d2d88d=1765439168; Hm_lpvt_91cf34f62b9bedb16460ca36cf192f4c=1765439176; Hm_lpvt_0e023fed85d2150e7d419b5b1f2e7c0f=1765439176',
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
#             'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
#             'Referer': 'https://www.cnhnb.com/',
#             'Connection': 'keep-alive'
#         }
#
#         async with self.semaphore:  # 控制并发数
#             try:
#                 async with session.get(url, headers=headers, timeout=self.timeout) as response:
#                     if response.status == 200:
#                         html = await response.text()
#                         content = etree.HTML(html)
#                         data = self.parse_content(content, url)
#
#                         # 随机延迟，避免请求过快
#                         await asyncio.sleep(random.uniform(1, 3))
#                         pbar.update(1)
#                         return data
#                     else:
#                         raise aiohttp.ClientError(f"HTTP状态码错误: {response.status}")
#
#             except Exception as e:
#                 logger.error(f"请求失败 {url}: {str(e)}")
#                 pbar.update(1)
#                 return {
#                     '链接': url,
#                     '价格': "请求失败",
#                     '起批量': "请求失败",
#                     '发货地': "请求失败",
#                     '询价': "请求失败",
#                     '成交': "请求失败",
#                     '评价': "请求失败",
#                     '规格': "请求失败"
#                 }
#
#     async def process_urls(self, urls):
#         """处理所有URL"""
#         connector = aiohttp.TCPConnector(limit=self.max_concurrent, limit_per_host=3)
#
#         async with aiohttp.ClientSession(connector=connector) as session:
#             tasks = []
#
#             with tqdm_asyncio(total=len(urls), desc="爬取进度") as pbar:
#                 for url in urls:
#                     task = asyncio.create_task(self.fetch_url(session, url, pbar))
#                     tasks.append(task)
#
#                 results = await asyncio.gather(*tasks, return_exceptions=True)
#
#             # 处理结果，过滤掉异常
#             valid_results = []
#             for result in results:
#                 if isinstance(result, Exception):
#                     logger.error(f"任务执行异常: {str(result)}")
#                 else:
#                     valid_results.append(result)
#
#             return valid_results
#
#     async def run(self, excel_path, output_filename):
#         """运行爬虫"""
#         logger.info("开始加载URL...")
#         urls = self.load_urls(excel_path)
#         logger.info(f"共加载 {len(urls)} 个URL")
#
#         logger.info("开始异步爬取...")
#         start_time = time.time()
#
#         all_data = await self.process_urls(urls)
#
#         end_time = time.time()
#         logger.info(f"爬取完成，耗时: {end_time - start_time:.2f}秒")
#         logger.info(f"成功爬取: {len([d for d in all_data if d.get('价格') not in ['请求失败', '解析失败']])} 条数据")
#
#         # 保存结果
#         result_df = pd.DataFrame(all_data)
#         result_df.to_excel(output_filename, index=False)
#         logger.info(f"数据已成功保存到 '{output_filename}'")
#
#
# async def main():
#     """主函数"""
#     spider = HuiNongSpider(max_concurrent=5, timeout=30)
#
#     try:
#         await spider.run('惠农网全品类数据2.xlsx', '惠农网商品详情2.xlsx')
#     except Exception as e:
#         logger.error(f"程序执行异常: {str(e)}")
#     finally:
#         logger.info("程序执行完成")
#
#
# if __name__ == "__main__":
#     # 运行异步主函数
#     asyncio.run(main())








# 22222222222222222222222222222222222222
# import asyncio
# import aiohttp
# from lxml import etree
# import pandas as pd
# from tqdm.asyncio import tqdm_asyncio
# import time
# import random
# from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
# import logging
#
# # 配置日志
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
#
#
# class HuiNongSpider:
#     def __init__(self, max_concurrent=10, timeout=60):  # 调高并发和超时
#         self.max_concurrent = max_concurrent
#         self.timeout = aiohttp.ClientTimeout(total=timeout)
#         self.semaphore = asyncio.Semaphore(max_concurrent)
#
#     def load_urls(self, excel_path):  # 移除limit限制
#         """加载URL列表（爬取全部URL）"""
#         df = pd.read_excel(excel_path)
#         urls = df['链接'].tolist()
#         # 可选：过滤空URL
#         urls = [url for url in urls if pd.notna(url) and isinstance(url, str) and url.strip()]
#         return urls
#
#
#     def extract_all_specifications(self, content):
#         """提取所有规格信息并合并为一个字符串"""
#         spec_container = content.xpath('//div[@class="batch-num mar spec-bg"]')
#
#         if not spec_container:
#             return "无规格信息"
#
#         spec_items = content.xpath('//div[@class="spec-items flex-c"]')
#         all_specs = []
#
#         for item in spec_items:
#             name = item.xpath('.//div[@class="s-name"]/text()')
#             price = item.xpath('.//div[@class="s-price"]/text()')
#             unit = item.xpath('.//div[@class="s-unit"]/text()')
#
#             name_text = name[0].strip() if name else "未知规格"
#             price_text = price[0].strip() if price else "价格未知"
#             unit_text = unit[0].strip() if unit else "起批量未知"
#
#             spec_text = f"{name_text} - {price_text} ({unit_text})"
#             all_specs.append(spec_text)
#
#         return "；".join(all_specs)
#
#     def parse_content(self, content, url):
#         """解析页面内容（删除询价、评价字段）"""
#         try:
#             price = content.xpath('//div[@class="active-p"]/text()')
#             qipi_num = content.xpath('//div[@class="flex-c batch-item"]/div/text()')
#             fahuodi = content.xpath(
#                 '//div[contains(@class, "batch-num") and contains(., "发货地址")]/div[@class="line-val"]/text()')
#             dealed = content.xpath('//div[@class="line-val" and contains(., "成交")]/span[@class="s1"]/text()')
#             specifications = self.extract_all_specifications(content)
#
#             return {
#                 '链接': url,
#                 '价格': price[0].strip() if price else "无价格信息",
#                 '起批量': qipi_num[0].strip() if qipi_num else "无起批量信息",
#                 '发货地': fahuodi[0].strip() if fahuodi else "无发货地信息",
#                 '成交': dealed[0].strip() if dealed else "无成交信息",
#                 '规格': specifications
#             }
#         except Exception as e:
#             logger.error(f"解析页面内容失败 {url}: {str(e)}")
#             return {
#                 '链接': url,
#                 '价格': "解析失败",
#                 '起批量': "解析失败",
#                 '发货地': "解析失败",
#                 '成交': "解析失败",
#                 '规格': "解析失败"
#             }
#
#     @retry(
#         stop=stop_after_attempt(3),  # 最多重试3次
#         wait=wait_exponential(multiplier=1, min=2, max=10),  # 指数退避等待
#         retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
#         before_sleep=lambda retry_state: logger.warning(
#             f"第{retry_state.attempt_number}次重试: {retry_state.outcome.exception()}")
#     )
#     async def fetch_url(self, session, url, pbar):
#         """获取单个URL的内容，包含重试机制"""
#         headers = {
#             'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
#             'Cookie': 'deviceId=e2e918e-5c55-48db-8400-c171803cf; Hm_lvt_b99541cbfb0edd202bb49abf3a0bef84=1762239771,1762417484; Hm_lvt_b2daa4a53a78af99c4a57c440f46d069=1763467426; sessionId=S_0MJ14V2VY4TLN49D; Hm_lvt_0e023fed85d2150e7d419b5b1f2e7c0f=1763467071,1765439109; HMACCOUNT=F1D67AF373D4EF14; Hm_lvt_91cf34f62b9bedb16460ca36cf192f4c=1763463548,1765439110; Hm_lvt_a6458082fb548e5ca7ff77d177d2d88d=1763463548,1765439110; hnUserTicket=58ed88d8-a4de-4a78-9abd-d52fd8eaf898; hnUserId=781226109; tfstk=gbnnpXxZr2zBMWSC-LqB8lRI2NLOAkZ77bI8wuFy75P196IKU70oOfp7zBZKqfcs1XHKekWI5jHVvDLQ2gqQVuRvMnKxpvZ74hW7n55C78w22MPFYkZZ7iliMnKxdvWLLKHwD2LNzdyzauzUzNSa1-Pz477eI5yuha5EauJMI-wR4azUTN-aU8EzabryIAP_UuyrauJiQ5wrMZ_UO0oKbQUmdP7q6nmaKyVqLWkKBcW38wMasgjoj2z3ggVG4gogKYzTXhSDySub9rFs_hI3qAyoi-ch_CqrIDi07DR1qjciul2s5Qbui4kKl4zMLHkgxW4mXyxW9k0rO04I-T9jQklslSae5CwivmUuGPfwTAHgTr0o9Csz9qDZsrnO6iEZ3VqG4r7NuFnfVRJ-ja_78RwgMhMWwj6C6KOJIdbVFyy_LSpMIa_78RwgMdvGogaUCJPA.; Hm_lpvt_a6458082fb548e5ca7ff77d177d2d88d=1765439168; Hm_lpvt_91cf34f62b9bedb16460ca36cf192f4c=1765439176; Hm_lpvt_0e023fed85d2150e7d419b5b1f2e7c0f=1765439176',
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
#             'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
#             'Referer': 'https://www.cnhnb.com/',
#             'Connection': 'keep-alive'
#         }
#
#         async with self.semaphore:  # 控制并发数
#             try:
#                 async with session.get(url, headers=headers, timeout=self.timeout) as response:
#                     if response.status == 200:
#                         html = await response.text()
#                         content = etree.HTML(html)
#                         data = self.parse_content(content, url)
#
#                         # 随机延迟，避免请求过快（适当延长）
#                         await asyncio.sleep(random.uniform(2, 5))
#                         pbar.update(1)
#                         return data
#                     else:
#                         raise aiohttp.ClientError(f"HTTP状态码错误: {response.status}")
#
#             except Exception as e:
#                 logger.error(f"请求失败 {url}: {str(e)}")
#                 pbar.update(1)
#                 return {
#                     '链接': url,
#                     '价格': "请求失败",
#                     '起批量': "请求失败",
#                     '发货地': "请求失败",
#                     '成交': "请求失败",
#                     '规格': "请求失败"
#                 }
#
#     async def process_urls(self, urls):
#         """处理所有URL"""
#         connector = aiohttp.TCPConnector(limit=self.max_concurrent, limit_per_host=5)  # 调高单主机并发
#
#         async with aiohttp.ClientSession(connector=connector) as session:
#             tasks = []
#
#             with tqdm_asyncio(total=len(urls), desc="爬取进度") as pbar:
#                 for url in urls:
#                     task = asyncio.create_task(self.fetch_url(session, url, pbar))
#                     tasks.append(task)
#
#                 results = await asyncio.gather(*tasks, return_exceptions=True)
#
#             # 处理结果，过滤掉异常
#             valid_results = []
#             for result in results:
#                 if isinstance(result, Exception):
#                     logger.error(f"任务执行异常: {str(result)}")
#                 else:
#                     valid_results.append(result)
#
#             return valid_results
#
#     async def run(self, excel_path, output_filename):
#         """运行爬虫"""
#         logger.info("开始加载URL...")
#         urls = self.load_urls(excel_path)  # 加载全部URL
#         logger.info(f"共加载 {len(urls)} 个URL")
#
#         logger.info("开始异步爬取...")
#         start_time = time.time()
#
#         all_data = await self.process_urls(urls)
#
#         end_time = time.time()
#         logger.info(f"爬取完成，耗时: {end_time - start_time:.2f}秒")
#         logger.info(f"成功爬取: {len([d for d in all_data if d.get('价格') not in ['请求失败', '解析失败']])} 条数据")
#
#         # 保存结果
#         result_df = pd.DataFrame(all_data)
#         result_df.to_excel(output_filename, index=False)
#         logger.info(f"数据已成功保存到 '{output_filename}'")
#
#
# async def main():
#     """主函数"""
#     spider = HuiNongSpider(max_concurrent=10, timeout=60)  # 优化并发和超时
#
#     try:
#         await spider.run('惠农网全品类数据2.xlsx', '惠农网商品详情2.xlsx')
#     except Exception as e:
#         logger.error(f"程序执行异常: {str(e)}")
#     finally:
#         logger.info("程序执行完成")
#
#
# if __name__ == "__main__":
#     # 运行异步主函数
#     asyncio.run(main())



# 3333333修改十条
# import asyncio
# import aiohttp
# from lxml import etree
# import pandas as pd
# from tqdm.asyncio import tqdm_asyncio
# import time
# import random
# from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
# import logging
#
# # 配置日志
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
#
#
# class HuiNongSpider:
#     def __init__(self, max_concurrent=10, timeout=60):  # 调高并发和超时
#         self.max_concurrent = max_concurrent
#         self.timeout = aiohttp.ClientTimeout(total=timeout)
#         self.semaphore = asyncio.Semaphore(max_concurrent)
#
#     def load_urls(self, excel_path, limit=10):  # 新增limit参数，默认取10条
#         """加载URL列表（限制只取指定数量的URL）"""
#         df = pd.read_excel(excel_path)
#         urls = df['链接'].tolist()
#         # 可选：过滤空URL
#         urls = [url for url in urls if pd.notna(url) and isinstance(url, str) and url.strip()]
#         # 核心修改：只取前limit条URL（这里limit=10）
#         urls = urls[:limit]
#         return urls
#
#     def extract_all_specifications(self, content):
#         """提取所有规格信息并合并为一个字符串"""
#         spec_container = content.xpath('//div[@class="batch-num mar spec-bg"]')
#
#         if not spec_container:
#             return "无规格信息"
#
#         spec_items = content.xpath('//div[@class="spec-items flex-c"]')
#         all_specs = []
#
#         for item in spec_items:
#             name = item.xpath('.//div[@class="s-name"]/text()')
#             price = item.xpath('.//div[@class="s-price"]/text()')
#             unit = item.xpath('.//div[@class="s-unit"]/text()')
#
#             name_text = name[0].strip() if name else "未知规格"
#             price_text = price[0].strip() if price else "价格未知"
#             unit_text = unit[0].strip() if unit else "起批量未知"
#
#             spec_text = f"{name_text} - {price_text} ({unit_text})"
#             all_specs.append(spec_text)
#
#         return "；".join(all_specs)
#
#     def parse_content(self, content, url):
#         """解析页面内容（删除询价、评价字段）"""
#         try:
#             price = content.xpath('//div[@class="active-p"]/text()')
#             qipi_num = content.xpath('//div[@class="flex-c batch-item"]/div/text()')
#             fahuodi = content.xpath(
#                 '//div[contains(@class, "batch-num") and contains(., "发货地址")]/div[@class="line-val"]/text()')
#             dealed = content.xpath('//div[@class="line-val" and contains(., "成交")]/span[@class="s1"]/text()')
#             specifications = self.extract_all_specifications(content)
#
#             return {
#                 '链接': url,
#                 '价格': price[0].strip() if price else "无价格信息",
#                 '起批量': qipi_num[0].strip() if qipi_num else "无起批量信息",
#                 '发货地': fahuodi[0].strip() if fahuodi else "无发货地信息",
#                 '成交': dealed[0].strip() if dealed else "无成交信息",
#                 '规格': specifications
#             }
#         except Exception as e:
#             logger.error(f"解析页面内容失败 {url}: {str(e)}")
#             return {
#                 '链接': url,
#                 '价格': "解析失败",
#                 '起批量': "解析失败",
#                 '发货地': "解析失败",
#                 '成交': "解析失败",
#                 '规格': "解析失败"
#             }
#
#     @retry(
#         stop=stop_after_attempt(3),  # 最多重试3次
#         wait=wait_exponential(multiplier=1, min=2, max=10),  # 指数退避等待
#         retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
#         before_sleep=lambda retry_state: logger.warning(
#             f"第{retry_state.attempt_number}次重试: {retry_state.outcome.exception()}")
#     )
#     async def fetch_url(self, session, url, pbar):
#         """获取单个URL的内容，包含重试机制"""
#         headers = {
#             'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
#             'Cookie': 'deviceId=e2e918e-5c55-48db-8400-c171803cf; Hm_lvt_b99541cbfb0edd202bb49abf3a0bef84=1762239771,1762417484; Hm_lvt_b2daa4a53a78af99c4a57c440f46d069=1763467426; sessionId=S_0MJ14V2VY4TLN49D; Hm_lvt_0e023fed85d2150e7d419b5b1f2e7c0f=1763467071,1765439109; HMACCOUNT=F1D67AF373D4EF14; Hm_lvt_91cf34f62b9bedb16460ca36cf192f4c=1763463548,1765439110; Hm_lvt_a6458082fb548e5ca7ff77d177d2d88d=1763463548,1765439110; hnUserTicket=58ed88d8-a4de-4a78-9abd-d52fd8eaf898; hnUserId=781226109; tfstk=gbnnpXxZr2zBMWSC-LqB8lRI2NLOAkZ77bI8wuFy75P196IKU70oOfp7zBZKqfcs1XHKekWI5jHVvDLQ2gqQVuRvMnKxpvZ74hW7n55C78w22MPFYkZZ7iliMnKxdvWLLKHwD2LNzdyzauzUzNSa1-Pz477eI5yuha5EauJMI-wR4azUTN-aU8EzabryIAP_UuyrauJiQ5wrMZ_UO0oKbQUmdP7q6nmaKyVqLWkKBcW38wMasgjoj2z3ggVG4gogKYzTXhSDySub9rFs_hI3qAyoi-ch_CqrIDi07DR1qjciul2s5Qbui4kKl4zMLHkgxW4mXyxW9k0rO04I-T9jQklslSae5CwivmUuGPfwTAHgTr0o9Csz9qDZsrnO6iEZ3VqG4r7NuFnfVRJ-ja_78RwgMhMWwj6C6KOJIdbVFyy_LSpMIa_78RwgMdvGogaUCJPA.; Hm_lpvt_a6458082fb548e5ca7ff77d177d2d88d=1765439168; Hm_lpvt_91cf34f62b9bedb16460ca36cf192f4c=1765439176; Hm_lpvt_0e023fed85d2150e7d419b5b1f2e7c0f=1765439176',
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
#             'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
#             'Referer': 'https://www.cnhnb.com/',
#             'Connection': 'keep-alive'
#         }
#
#         async with self.semaphore:  # 控制并发数
#             try:
#                 async with session.get(url, headers=headers, timeout=self.timeout) as response:
#                     if response.status == 200:
#                         html = await response.text()
#                         content = etree.HTML(html)
#                         data = self.parse_content(content, url)
#
#                         # 随机延迟，避免请求过快（适当延长）
#                         await asyncio.sleep(random.uniform(2, 5))
#                         pbar.update(1)
#                         return data
#                     else:
#                         raise aiohttp.ClientError(f"HTTP状态码错误: {response.status}")
#
#             except Exception as e:
#                 logger.error(f"请求失败 {url}: {str(e)}")
#                 pbar.update(1)
#                 return {
#                     '链接': url,
#                     '价格': "请求失败",
#                     '起批量': "请求失败",
#                     '发货地': "请求失败",
#                     '成交': "请求失败",
#                     '规格': "请求失败"
#                 }
#
#     async def process_urls(self, urls):
#         """处理所有URL"""
#         connector = aiohttp.TCPConnector(limit=self.max_concurrent, limit_per_host=5)  # 调高单主机并发
#
#         async with aiohttp.ClientSession(connector=connector) as session:
#             tasks = []
#
#             with tqdm_asyncio(total=len(urls), desc="爬取进度") as pbar:
#                 for url in urls:
#                     task = asyncio.create_task(self.fetch_url(session, url, pbar))
#                     tasks.append(task)
#
#                 results = await asyncio.gather(*tasks, return_exceptions=True)
#
#             # 处理结果，过滤掉异常
#             valid_results = []
#             for result in results:
#                 if isinstance(result, Exception):
#                     logger.error(f"任务执行异常: {str(result)}")
#                 else:
#                     valid_results.append(result)
#
#             return valid_results
#
#     async def run(self, excel_path, output_filename):
#         """运行爬虫"""
#         logger.info("开始加载URL...")
#         urls = self.load_urls(excel_path)  # 加载前10条URL
#         logger.info(f"共加载 {len(urls)} 个URL")
#
#         logger.info("开始异步爬取...")
#         start_time = time.time()
#
#         all_data = await self.process_urls(urls)
#
#         end_time = time.time()
#         logger.info(f"爬取完成，耗时: {end_time - start_time:.2f}秒")
#         logger.info(f"成功爬取: {len([d for d in all_data if d.get('价格') not in ['请求失败', '解析失败']])} 条数据")
#
#         # 保存结果
#         result_df = pd.DataFrame(all_data)
#         result_df.to_excel(output_filename, index=False)
#         logger.info(f"数据已成功保存到 '{output_filename}'")
#
#
# async def main():
#     """主函数"""
#     spider = HuiNongSpider(max_concurrent=10, timeout=60)  # 优化并发和超时
#
#     try:
#         await spider.run('惠农网全品类数据2.xlsx', '惠农网商品详情2.xlsx')
#     except Exception as e:
#         logger.error(f"程序执行异常: {str(e)}")
#     finally:
#         logger.info("程序执行完成")
#
#
# if __name__ == "__main__":
#     # 运行异步主函数
#     asyncio.run(main())



# 44444444444444444新增品类
# import asyncio
# import aiohttp
# from lxml import etree
# import pandas as pd
# from tqdm.asyncio import tqdm_asyncio
# import time
# import random
# from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
# import logging
#
# # 配置日志
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
#
#
# class HuiNongSpider:
#     def __init__(self, max_concurrent=10, timeout=60):
#         self.max_concurrent = max_concurrent
#         self.timeout = aiohttp.ClientTimeout(total=timeout)
#         self.semaphore = asyncio.Semaphore(max_concurrent)
#
#     def load_urls(self, excel_path, limit=10):
#         """加载URL列表（限制只取指定数量的URL）"""
#         df = pd.read_excel(excel_path)
#         urls = df['链接'].tolist()
#         urls = [url for url in urls if pd.notna(url) and isinstance(url, str) and url.strip()]
#         urls = urls[:limit]
#         return urls
#
#     def extract_all_specifications(self, content):
#         """提取所有规格信息并合并为一个字符串"""
#         spec_container = content.xpath('//div[@class="batch-num mar spec-bg"]')
#         if not spec_container:
#             return "无规格信息"
#         spec_items = content.xpath('//div[@class="spec-items flex-c"]')
#         all_specs = []
#         for item in spec_items:
#             name = item.xpath('.//div[@class="s-name"]/text()')
#             price = item.xpath('.//div[@class="s-price"]/text()')
#             unit = item.xpath('.//div[@class="s-unit"]/text()')
#             name_text = name[0].strip() if name else "未知规格"
#             price_text = price[0].strip() if price else "价格未知"
#             unit_text = unit[0].strip() if unit else "起批量未知"
#             spec_text = f"{name_text} - {price_text} ({unit_text})"
#             all_specs.append(spec_text)
#         return "；".join(all_specs)
#
#     def parse_content(self, content, url):
#         """解析页面内容（新增：品种名、货品类别）"""
#         try:
#             price = content.xpath('//div[@class="active-p"]/text()')
#             qipi_num = content.xpath('//div[@class="flex-c batch-item"]/div/text()')
#             fahuodi = content.xpath(
#                 '//div[contains(@class, "batch-num") and contains(., "发货地址")]/div[@class="line-val"]/text()')
#             dealed = content.xpath('//div[@class="line-val" and contains(., "成交")]/span[@class="s1"]/text()')
#             specifications = self.extract_all_specifications(content)
#
#             # ========== 新增：爬取品种名、货品类别 ==========
#             # 逻辑：定位class="detail-attrs-item"的容器，匹配“品种名”“货品种别”对应的t2值
#             # 1. 提取所有属性项（t1是标签名，t2是值）
#             attrs_items = content.xpath('//div[@class="detail-attrs-item"]')
#             variety_name = "无"  # 品种名
#             goods_category = "无"  # 货品类别
#             for item in attrs_items:
#                 # 获取当前项的标签名（t1）
#                 attr_label = item.xpath('.//div[@class="t1"]/text()')
#                 if not attr_label:
#                     continue
#                 attr_label = attr_label[0].strip()
#                 # 获取当前项的值（t2）
#                 attr_value = item.xpath('.//div[@class="t2"]/text()')
#                 attr_value = attr_value[0].strip() if attr_value else "无"
#
#                 # 匹配“品种名”或“货品种别”
#                 if attr_label == "品种名":
#                     variety_name = attr_value
#                 elif attr_label == "货品种别":
#                     goods_category = attr_value
#
#             return {
#                 '链接': url,
#                 '价格': price[0].strip() if price else "无价格信息",
#                 '起批量': qipi_num[0].strip() if qipi_num else "无起批量信息",
#                 '发货地': fahuodi[0].strip() if fahuodi else "无发货地信息",
#                 '成交': dealed[0].strip() if dealed else "无成交信息",
#                 '规格': specifications,
#                 '品种名': variety_name,  # 新增字段
#                 '货品类别': goods_category  # 新增字段
#             }
#         except Exception as e:
#             logger.error(f"解析页面内容失败 {url}: {str(e)}")
#             return {
#                 '链接': url,
#                 '价格': "解析失败",
#                 '起批量': "解析失败",
#                 '发货地': "解析失败",
#                 '成交': "解析失败",
#                 '规格': "解析失败",
#                 '品种名': "无",  # 异常时默认“无”
#                 '货品类别': "无"  # 异常时默认“无”
#             }
#
#     @retry(
#         stop=stop_after_attempt(3),
#         wait=wait_exponential(multiplier=1, min=2, max=10),
#         retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
#         before_sleep=lambda retry_state: logger.warning(
#             f"第{retry_state.attempt_number}次重试: {retry_state.outcome.exception()}")
#     )
#     async def fetch_url(self, session, url, pbar):
#         """获取单个URL的内容，包含重试机制"""
#         headers = {
#             'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
#             'Cookie': 'deviceId=e2e918e-5c55-48db-8400-c171803cf; Hm_lvt_b99541cbfb0edd202bb49abf3a0bef84=1762239771,1762417484; Hm_lvt_b2daa4a53a78af99c4a57c440f46d069=1763467426; sessionId=S_0MJ14V2VY4TLN49D; Hm_lvt_0e023fed85d2150e7d419b5b1f2e7c0f=1763467071,1765439109; HMACCOUNT=F1D67AF373D4EF14; Hm_lvt_91cf34f62b9bedb16460ca36cf192f4c=1763463548,1765439110; Hm_lvt_a6458082fb548e5ca7ff77d177d2d88d=1763463548,1765439110; hnUserTicket=58ed88d8-a4de-4a78-9abd-d52fd8eaf898; hnUserId=781226109; tfstk=gbnnpXxZr2zBMWSC-LqB8lRI2NLOAkZ77bI8wuFy75P196IKU70oOfp7zBZKqfcs1XHKekWI5jHVvDLQ2gqQVuRvMnKxpvZ74hW7n55C78w22MPFYkZZ7iliMnKxdvWLLKHwD2LNzdyzauzUzNSa1-Pz477eI5yuha5EauJMI-wR4azUTN-aU8EzabryIAP_UuyrauJiQ5wrMZ_UO0oKbQUmdP7q6nmaKyVqLWkKBcW38wMasgjoj2z3ggVG4gogKYzTXhSDySub9rFs_hI3qAyoi-ch_CqrIDi07DR1qjciul2s5Qbui4kKl4zMLHkgxW4mXyxW9k0rO04I-T9jQklslSae5CwivmUuGPfwTAHgTr0o9Csz9qDZsrnO6iEZ3VqG4r7NuFnfVRJ-ja_78RwgMhMWwj6C6KOJIdbVFyy_LSpMIa_78RwgMdvGogaUCJPA.; Hm_lpvt_a6458082fb548e5ca7ff77d177d2d88d=1765439168; Hm_lpvt_91cf34f62b9bedb16460ca36cf192f4c=1765439176; Hm_lpvt_0e023fed85d2150e7d419b5b1f2e7c0f=1765439176',
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
#             'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
#             'Referer': 'https://www.cnhnb.com/',
#             'Connection': 'keep-alive'
#         }
#
#         async with self.semaphore:
#             try:
#                 async with session.get(url, headers=headers, timeout=self.timeout) as response:
#                     if response.status == 200:
#                         html = await response.text()
#                         content = etree.HTML(html)
#                         data = self.parse_content(content, url)
#                         await asyncio.sleep(random.uniform(2, 5))
#                         pbar.update(1)
#                         return data
#                     else:
#                         raise aiohttp.ClientError(f"HTTP状态码错误: {response.status}")
#             except Exception as e:
#                 logger.error(f"请求失败 {url}: {str(e)}")
#                 pbar.update(1)
#                 return {
#                     '链接': url,
#                     '价格': "请求失败",
#                     '起批量': "请求失败",
#                     '发货地': "请求失败",
#                     '成交': "请求失败",
#                     '规格': "请求失败",
#                     '品种名': "无",
#                     '货品类别': "无"
#                 }
#
#     async def process_urls(self, urls):
#         """处理所有URL"""
#         connector = aiohttp.TCPConnector(limit=self.max_concurrent, limit_per_host=5)
#         async with aiohttp.ClientSession(connector=connector) as session:
#             tasks = []
#             with tqdm_asyncio(total=len(urls), desc="爬取进度") as pbar:
#                 for url in urls:
#                     task = asyncio.create_task(self.fetch_url(session, url, pbar))
#                     tasks.append(task)
#                 results = await asyncio.gather(*tasks, return_exceptions=True)
#             valid_results = []
#             for result in results:
#                 if isinstance(result, Exception):
#                     logger.error(f"任务执行异常: {str(result)}")
#                 else:
#                     valid_results.append(result)
#             return valid_results
#
#     async def run(self, excel_path, output_filename):
#         """运行爬虫"""
#         logger.info("开始加载URL...")
#         urls = self.load_urls(excel_path)
#         logger.info(f"共加载 {len(urls)} 个URL")
#         logger.info("开始异步爬取...")
#         start_time = time.time()
#         all_data = await self.process_urls(urls)
#         end_time = time.time()
#         success_count = len([d for d in all_data if d.get('价格') not in ['请求失败', '解析失败']])
#         logger.info(f"爬取完成，耗时: {end_time - start_time:.2f}秒")
#         logger.info(f"成功爬取: {success_count} 条数据")
#         result_df = pd.DataFrame(all_data)
#         result_df.to_excel(output_filename, index=False)
#         logger.info(f"数据已成功保存到 '{output_filename}'")
#
#
# async def main():
#     """主函数"""
#     spider = HuiNongSpider(max_concurrent=10, timeout=60)
#     try:
#         await spider.run('惠农网全品类数据2.xlsx', '惠农网商品详情2.xlsx')
#     except Exception as e:
#         logger.error(f"程序执行异常: {str(e)}")
#     finally:
#         logger.info("程序执行完成")
#
#
# if __name__ == "__main__":
#     asyncio.run(main())

#
# import asyncio
# import aiohttp
# from lxml import etree
# import pandas as pd
# from tqdm.asyncio import tqdm_asyncio
# import time
# import random
# from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
# import logging
#
# # 配置日志
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
#
#
# class HuiNongSpider:
#     def __init__(self, max_concurrent=10, timeout=60):
#         self.max_concurrent = max_concurrent
#         self.timeout = aiohttp.ClientTimeout(total=timeout)
#         self.semaphore = asyncio.Semaphore(max_concurrent)
#
#     def load_urls(self, excel_path, limit=10):
#         """加载URL列表（限制只取指定数量的URL）"""
#         df = pd.read_excel(excel_path)
#         urls = df['链接'].tolist()
#         urls = [url for url in urls if pd.notna(url) and isinstance(url, str) and url.strip()]
#         urls = urls[:limit]
#         return urls
#
#     def extract_all_specifications(self, content):
#         """提取所有规格信息并合并为一个字符串"""
#         spec_container = content.xpath('//div[@class="batch-num mar spec-bg"]')
#         if not spec_container:
#             return "无规格信息"
#         spec_items = content.xpath('//div[@class="spec-items flex-c"]')
#         all_specs = []
#         for item in spec_items:
#             name = item.xpath('.//div[@class="s-name"]/text()')
#             price = item.xpath('.//div[@class="s-price"]/text()')
#             unit = item.xpath('.//div[@class="s-unit"]/text()')
#             name_text = name[0].strip() if name else "未知规格"
#             price_text = price[0].strip() if price else "价格未知"
#             unit_text = unit[0].strip() if unit else "起批量未知"
#             spec_text = f"{name_text} - {price_text} ({unit_text})"
#             all_specs.append(spec_text)
#         return "；".join(all_specs)
#
#     def parse_content(self, content, url):
#         """解析页面内容（仅保留品种名，删除货品类别）"""
#         try:
#             price = content.xpath('//div[@class="active-p"]/text()')
#             qipi_num = content.xpath('//div[@class="flex-c batch-item"]/div/text()')
#             fahuodi = content.xpath('//div[contains(@class, "batch-num") and contains(., "发货地址")]/div[@class="line-val"]/text()')
#             dealed = content.xpath('//div[@class="line-val" and contains(., "成交")]/span[@class="s1"]/text()')
#             specifications = self.extract_all_specifications(content)
#
#             # ========== 仅保留品种名解析（删除货品类别） ==========
#             attrs_items = content.xpath('//div[@class="detail-attrs-item"]')
#             variety_name = "无"  # 品种名
#             for item in attrs_items:
#                 attr_label = item.xpath('.//div[@class="t1"]/text()')
#                 if not attr_label:
#                     continue
#                 attr_label = attr_label[0].strip()
#                 # 仅匹配“品种名”标签
#                 if attr_label == "品种名":
#                     attr_value = item.xpath('.//div[@class="t2"]/text()')
#                     variety_name = attr_value[0].strip() if attr_value else "无"
#
#             return {
#                 '链接': url,
#                 '价格': price[0].strip() if price else "无价格信息",
#                 '起批量': qipi_num[0].strip() if qipi_num else "无起批量信息",
#                 '发货地': fahuodi[0].strip() if fahuodi else "无发货地信息",
#                 '成交': dealed[0].strip() if dealed else "无成交信息",
#                 '规格': specifications,
#                 '品种名': variety_name  # 仅保留品种名字段
#             }
#         except Exception as e:
#             logger.error(f"解析页面内容失败 {url}: {str(e)}")
#             return {
#                 '链接': url,
#                 '价格': "解析失败",
#                 '起批量': "解析失败",
#                 '发货地': "解析失败",
#                 '成交': "解析失败",
#                 '规格': "解析失败",
#                 '品种名': "无"  # 异常时默认“无”
#             }
#
#     @retry(
#         stop=stop_after_attempt(3),
#         wait=wait_exponential(multiplier=1, min=2, max=10),
#         retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
#         before_sleep=lambda retry_state: logger.warning(f"第{retry_state.attempt_number}次重试: {retry_state.outcome.exception()}")
#     )
#     async def fetch_url(self, session, url, pbar):
#         """获取单个URL的内容，包含重试机制"""
#         headers = {
#             'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
#             'Cookie': 'deviceId=e2e918e-5c55-48db-8400-c171803cf; Hm_lvt_b99541cbfb0edd202bb49abf3a0bef84=1762239771,1762417484; Hm_lvt_b2daa4a53a78af99c4a57c440f46d069=1763467426; sessionId=S_0MJ14V2VY4TLN49D; Hm_lvt_0e023fed85d2150e7d419b5b1f2e7c0f=1763467071,1765439109; HMACCOUNT=F1D67AF373D4EF14; Hm_lvt_91cf34f62b9bedb16460ca36cf192f4c=1763463548,1765439110; Hm_lvt_a6458082fb548e5ca7ff77d177d2d88d=1763463548,1765439110; hnUserTicket=58ed88d8-a4de-4a78-9abd-d52fd8eaf898; hnUserId=781226109; tfstk=gbnnpXxZr2zBMWSC-LqB8lRI2NLOAkZ77bI8wuFy75P196IKU70oOfp7zBZKqfcs1XHKekWI5jHVvDLQ2gqQVuRvMnKxpvZ74hW7n55C78w22MPFYkZZ7iliMnKxdvWLLKHwD2LNzdyzauzUzNSa1-Pz477eI5yuha5EauJMI-wR4azUTN-aU8EzabryIAP_UuyrauJiQ5wrMZ_UO0oKbQUmdP7q6nmaKyVqLWkKBcW38wMasgjoj2z3ggVG4gogKYzTXhSDySub9rFs_hI3qAyoi-ch_CqrIDi07DR1qjciul2s5Qbui4kKl4zMLHkgxW4mXyxW9k0rO04I-T9jQklslSae5CwivmUuGPfwTAHgTr0o9Csz9qDZsrnO6iEZ3VqG4r7NuFnfVRJ-ja_78RwgMhMWwj6C6KOJIdbVFyy_LSpMIa_78RwgMdvGogaUCJPA.; Hm_lpvt_a6458082fb548e5ca7ff77d177d2d88d=1765439168; Hm_lpvt_91cf34f62b9bedb16460ca36cf192f4c=1765439176; Hm_lpvt_0e023fed85d2150e7d419b5b1f2e7c0f=1765439176',
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
#             'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
#             'Referer': 'https://www.cnhnb.com/',
#             'Connection': 'keep-alive'
#         }
#
#         async with self.semaphore:
#             try:
#                 async with session.get(url, headers=headers, timeout=self.timeout) as response:
#                     if response.status == 200:
#                         html = await response.text()
#                         content = etree.HTML(html)
#                         data = self.parse_content(content, url)
#                         await asyncio.sleep(random.uniform(2, 5))
#                         pbar.update(1)
#                         return data
#                     else:
#                         raise aiohttp.ClientError(f"HTTP状态码错误: {response.status}")
#             except Exception as e:
#                 logger.error(f"请求失败 {url}: {str(e)}")
#                 pbar.update(1)
#                 return {
#                     '链接': url,
#                     '价格': "请求失败",
#                     '起批量': "请求失败",
#                     '发货地': "请求失败",
#                     '成交': "请求失败",
#                     '规格': "请求失败",
#                     '品种名': "无"  # 仅保留品种名
#                 }
#
#     async def process_urls(self, urls):
#         """处理所有URL"""
#         connector = aiohttp.TCPConnector(limit=self.max_concurrent, limit_per_host=5)
#         async with aiohttp.ClientSession(connector=connector) as session:
#             tasks = []
#             with tqdm_asyncio(total=len(urls), desc="爬取进度") as pbar:
#                 for url in urls:
#                     task = asyncio.create_task(self.fetch_url(session, url, pbar))
#                     tasks.append(task)
#                 results = await asyncio.gather(*tasks, return_exceptions=True)
#             valid_results = []
#             for result in results:
#                 if isinstance(result, Exception):
#                     logger.error(f"任务执行异常: {str(result)}")
#                 else:
#                     valid_results.append(result)
#             return valid_results
#
#     async def run(self, excel_path, output_filename):
#         """运行爬虫"""
#         logger.info("开始加载URL...")
#         urls = self.load_urls(excel_path)
#         logger.info(f"共加载 {len(urls)} 个URL")
#         logger.info("开始异步爬取...")
#         start_time = time.time()
#         all_data = await self.process_urls(urls)
#         end_time = time.time()
#         success_count = len([d for d in all_data if d.get('价格') not in ['请求失败', '解析失败']])
#         logger.info(f"爬取完成，耗时: {end_time - start_time:.2f}秒")
#         logger.info(f"成功爬取: {success_count} 条数据")
#         result_df = pd.DataFrame(all_data)
#         result_df.to_excel(output_filename, index=False)
#         logger.info(f"数据已成功保存到 '{output_filename}'")
#
#
# async def main():
#     """主函数"""
#     spider = HuiNongSpider(max_concurrent=10, timeout=60)
#     try:
#         await spider.run('惠农网全品类数据2.xlsx', '惠农网商品详情2.xlsx')
#     except Exception as e:
#         logger.error(f"程序执行异常: {str(e)}")
#     finally:
#         logger.info("程序执行完成")
#
#
# if __name__ == "__main__":
#     asyncio.run(main())

