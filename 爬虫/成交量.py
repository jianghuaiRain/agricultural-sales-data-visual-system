# from selenium import webdriver #控制浏览器
# from selenium.webdriver.common.by import By #定位元素的方式（id xpath
# from selenium.webdriver.support.ui import WebDriverWait #显式等待（等待元素加载
# from selenium.webdriver.support import expected_conditions as EC #等待的条件（元素可点击
# from selenium.webdriver.chrome.options import Options #谷歌浏览器配置项
# import pandas as pd #读写excel文件
# import time #固定延迟
# import random #生成随机数，用于反爬
# import logging #日志记录（记录爬取过程
#
# # 配置日志
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# #配置日志格式和级别
# # loggin.INFO只输出警告错误级别的日志
# # format：日志包含时间+级别+内容（2025-12-20 10:00:00 - INFO - 开始爬取商品 XXX
# logger = logging.getLogger(__name__)
# # 创建日志实例，后续用 logger.info()/logger.error() 输出信息。
#
# # 3. 爬虫类初始化（__init__方法）
# class HuiNongDealSpider:
#     def __init__(self):
#         # 初始化Selenium浏览器（隐藏自动化标识）
#         chrome_options = Options()# # 禁用“自动化控制”提示（避免被网站识别为爬虫）
#         chrome_options.add_argument('--disable-blink-features=AutomationControlled')
#         chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
#         chrome_options.add_experimental_option('useAutomationExtension', False)
#         #启动谷歌浏览器
#         self.driver = webdriver.Chrome(options=chrome_options)
#         self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
#             'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
#         })
#
#     def extract_deal_data(self, url):
#         """提取单个商品的所有成交数据（多页）"""
#         all_deal_data = [] #存储当前商品的所有成交数据
#         try:
#             # 访问商品详情页
#             self.driver.get(url)
#             time.sleep(random.uniform(2, 4))  # 等待页面加载随机延迟2-4秒
#
#             # 1. 切换到“在线成交”标签显式等待十秒，指导标签可点击
#             try:
#                 deal_tab = WebDriverWait(self.driver, 10).until(
#                     EC.element_to_be_clickable((By.XPATH, '//div[contains(@class, "tab-item") and contains(text(), "在线成交")]'))
#                 )
#                 #基于这些通用特征，用 **“文本包含 + 标签类型 + 模糊 class”** 的组合 XPath，就能适配所有商品：
#                 deal_tab.click() #点击标签
#                 time.sleep(random.uniform(1, 2))#等待标签切换完成
#             except Exception as e:
#                 logger.error(f"切换到在线成交标签失败 {url}: {str(e)}")
#                 return all_deal_data #失败则返回空列表
#
#             # 2. 获取总页数
#             try:
#                 # 定位分页区域的“共XX条”（结合class+文本，避免误匹配）
#                 total_page_text = self.driver.find_element(By.XPATH,
#                                                            '//span[contains(@class, "eye-pagination__total") and contains(text(),"共") and contains(text(),"条")]').text
#                 # 提取总条数（如“共75条”→提取75）
#                 total_count = int(total_page_text.split('共')[1].split('条')[0])
#                 # 计算总页数（每页10条）
#                 total_page = total_count // 10 + 1 if total_count % 10 != 0 else total_count // 10
#                 logger.info(f"商品 {url} 共 {total_count} 条成交数据，分 {total_page} 页")
#             except Exception as e:
#                 logger.warning(f"无法获取总页数，默认爬取1页 {url}: {str(e)}")
#                 total_page = 1
#
#             for page in range(1, total_page + 1):
#                 logger.info(f"正在爬取商品 {url} 的第 {page}/{total_page} 页成交数据")
#                 try:
#                     # 1. 定位页码输入框（结合“跳转到”文本+输入框class）
#                     # 逻辑：先找到“跳转到”文本的容器，再定位其后方的input（class为eye-input__inner）
#                     page_input = WebDriverWait(self.driver, 5).until(
#                         EC.element_to_be_clickable((By.XPATH,
#                                                     '//span[contains(text(),"跳转到")]/following-sibling::input[@class="eye-input__inner"]'))
#                     )
#                     page_input.clear()  # 清空输入框原有内容
#                     page_input.send_keys(str(page))  # 输入目标页码
#
#                     # 2. 定位“确定”按钮（结合class+文本，精准匹配截图中的span标签）
#                     confirm_btn = WebDriverWait(self.driver, 5).until(
#                         EC.element_to_be_clickable((By.XPATH,
#                                                     '//span[@class="eye-pagination__submit" and text()="确定"]'))
#                     )
#                     confirm_btn.click()  # 点击确定按钮
#
#                     # 等待页面加载完成（确保成交数据刷新）
#                     time.sleep(random.uniform(1.5, 2.5))
#
#                     # 3. 提取当前页的成交数据（后续逻辑保持不变）
#                     deal_rows = self.driver.find_elements(By.XPATH, '//table/tbody/tr')
#                     for row in deal_rows:
#                         try:
#                             goods_spec = row.find_element(By.XPATH, './td[2]').text
#                             purchase_quantity = row.find_element(By.XPATH, './td[3]').text
#                             deal_time = row.find_element(By.XPATH, './td[4]').text
#
#                             price = "无价格信息"
#                             if '元' in goods_spec:
#                                 price = goods_spec.split('元')[0].split()[-1] + '元'
#
#                             all_deal_data.append({
#                                 '商品链接': url,
#                                 '货品规格': goods_spec,
#                                 '采购量': purchase_quantity,
#                                 '成交时间': deal_time,
#                                 '成交价格': price
#                             })
#                         except Exception as e:
#                             logger.error(f"提取成交行数据失败 {url} 第{page}页: {str(e)}")
#                             continue
#                 except Exception as e:
#                     logger.error(f"爬取第 {page} 页失败 {url}: {str(e)}")
#                     continue
#
#         except Exception as e:
#             logger.error(f"提取成交数据失败 {url}: {str(e)}")
#         finally:
#             return all_deal_data
#
#     def run(self, input_excel, output_excel, limit=10):  # 新增limit参数，默认10个商品
#         """批量爬取Excel中指定数量商品的成交数据"""
#         # 读取商品URL列表
#         df = pd.read_excel(input_excel)
#         urls = df['链接'].tolist()
#         urls = [url for url in urls if pd.notna(url) and isinstance(url, str) and url.strip()]
#
#         # 核心修改：只取前limit个URL（默认10个）
#         urls = urls[:limit]
#         logger.info(f"共加载 {len(urls)} 个商品URL（限制只爬取{limit}个）")
#
#         # 爬取指定数量商品的成交数据
#         all_data = []
#         for idx, url in enumerate(urls, 1):
#             logger.info(f"【{idx}/{limit}】开始爬取商品 {url} 的成交数据")
#             deal_data = self.extract_deal_data(url)
#             all_data.extend(deal_data)
#             time.sleep(random.uniform(3, 5))  # 商品间延迟，避免被封
#
#         # 保存结果
#         result_df = pd.DataFrame(all_data)
#         result_df.to_excel(output_excel, index=False)
#         logger.info(f"所有成交数据已保存到 {output_excel}，共 {len(result_df)} 条成交记录")
#
#         # 关闭浏览器
#         self.driver.quit()
#
#
# if __name__ == "__main__":
#     # 输入：包含商品链接的Excel；输出：成交数据Excel；限制爬取10个商品
#     spider = HuiNongDealSpider()
#     spider.run('惠农网全品类数据2.xlsx', '惠农网商品成交数据.xlsx', limit=10)
#
#
#
#
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# service=Service(executable_path="C:\Program Files\Google\Chrome\Application\chromedriver.exe")
# driver = webdriver.Chrome(service=service)
# driver.get("https://www.baidu.com")
# print(f"Chrome版本：{driver.capabilities['browserVersion']}")
# print(f"驱动版本：{driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0]}")
# print("驱动适配成功！")
# driver.quit()


# from selenium import webdriver  # 控制浏览器
# from selenium.webdriver.chrome.service import Service  # 新增：导入Service类
# from selenium.webdriver.common.by import By  # 定位元素的方式（id/xpath等）
# from selenium.webdriver.support.ui import WebDriverWait  # 显式等待（等待元素加载）
# from selenium.webdriver.support import expected_conditions as EC  # 等待的条件（元素可点击）
# from selenium.webdriver.chrome.options import Options  # 谷歌浏览器配置项
# import pandas as pd  # 读写excel文件
# import time  # 固定延迟
# import random  # 生成随机数，用于反爬
# import logging  # 日志记录（记录爬取过程）
#
# # 配置日志
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
#
#
# class HuiNongDealSpider:
#     def __init__(self):
#         # 初始化Chrome配置（增强反爬）
#         chrome_options = Options()
#         # 隐藏自动化标识
#         chrome_options.add_argument('--disable-blink-features=AutomationControlled')
#         chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
#         chrome_options.add_experimental_option('useAutomationExtension', False)
#         # 伪装浏览器UA（避免被识别为爬虫）
#         chrome_options.add_argument(
#             'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
#         # 窗口最大化（避免元素因窗口过小不可见）
#         chrome_options.add_argument('--start-maximized')
#         # 禁用图片加载（提升爬取速度）
#         chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
#
#         # ========== 核心修改：显式指定ChromeDriver路径 ==========
#         # 配置Service，指定驱动exe路径（注意路径转义：\ → \\ 或用r前缀）
#         service = Service(executable_path=r"C:\Program Files\Google\Chrome\Application\chromedriver.exe")
#         # 启动浏览器（传入service和options）
#         self.driver = webdriver.Chrome(service=service, options=chrome_options)
#         # ======================================================
#
#         # 终极反爬：修改navigator.webdriver为undefined
#         self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
#             'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
#         })
#
#     def extract_deal_data(self, url):
#         all_deal_data = []
#         try:
#             self.driver.get(url)
#             time.sleep(random.uniform(2, 4))
#
#             # 1. 切换到“在线成交”标签
#             deal_tab = WebDriverWait(self.driver, 10).until(
#                 EC.element_to_be_clickable((By.XPATH, '//*[contains(text(), "在线成交")]'))
#             )
#             deal_tab.click()
#             time.sleep(2)
#
#             # ========== 新增：关闭弹窗（先尝试定位并关闭弹窗） ==========
#             try:
#                 # 定位弹窗的关闭按钮（基于截图中class：iconfont icon-guanbi）
#                 close_btn = WebDriverWait(self.driver, 5).until(
#                     EC.element_to_be_clickable((By.XPATH, '//i[@class="iconfont icon-guanbi"]'))
#                 )
#                 close_btn.click()
#                 logger.info(f"成功关闭商品 {url} 的弹窗")
#                 time.sleep(1)
#             except Exception as e:
#                 logger.warning(f"商品 {url} 无弹窗或关闭失败: {str(e)}")
#             # ======================================================
#
#             # ========== 调整：滚动到页面1/3位置 ==========
#             self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.33);")
#             time.sleep(random.uniform(1, 2))  # 等待滚动后加载元素
#             # ======================================================
#
#             # 2. 获取总页数（滚动+关弹窗后定位）
#             total_page = 1
#             try:
#                 total_page_text = WebDriverWait(self.driver, 8).until(
#                     EC.presence_of_element_located((By.XPATH,
#                                                     '//span[@class="eye-pagination__total" and contains(text(),"共") and contains(text(),"条")]'))
#                 ).text
#                 total_count = int(total_page_text.split('共')[1].split('条')[0])
#                 total_page = total_count // 10 + 1 if total_count % 10 != 0 else total_count // 10
#                 logger.info(f"商品 {url} 共 {total_count} 条成交数据，分 {total_page} 页")
#             except Exception as e:
#                 logger.warning(f"无法获取总页数，默认爬取1页 {url}: {str(e)}")
#                 total_page = 1
#
#             # 后续分页、提取数据逻辑保持不变...
#
#
#             # 3. 逐页爬取数据
#             for page in range(1, total_page + 1):
#                 logger.info(f"正在爬取商品 {url} 的第 {page}/{total_page} 页成交数据")
#                 try:
#                     # 分页跳转（仅非第1页执行）
#                     if page > 1:
#                         # 定位页码输入框
#                         page_input = WebDriverWait(self.driver, 5).until(
#                             EC.element_to_be_clickable((By.XPATH,
#                                                         '//span[contains(text(),"跳转到")]/following-sibling::input[@class="eye-input__inner"]'))
#                         )
#                         page_input.clear()
#                         page_input.send_keys(str(page))
#                         # 定位确定按钮
#                         confirm_btn = WebDriverWait(self.driver, 5).until(
#                             EC.element_to_be_clickable((By.XPATH,
#                                                         '//span[@class="eye-pagination__submit" and text()="确定"]'))
#                         )
#                         confirm_btn.click()
#                         # 等待页面刷新
#                         WebDriverWait(self.driver, 8).until(
#                             EC.presence_of_element_located((By.XPATH, '//span[@class="eye-pagination__total"]'))
#                         )
#                         time.sleep(2)
#
#                     # 提取当前页成交数据（排除表头行）
#                     deal_rows = WebDriverWait(self.driver, 8).until(
#                         EC.presence_of_all_elements_located((By.XPATH, '//table//tr[position() > 1]'))
#                     )
#                     for row in deal_rows:
#                         try:
#                             goods_spec = row.find_element(By.XPATH, './td[2]').text.strip()
#                             purchase_quantity = row.find_element(By.XPATH, './td[3]').text.strip()
#                             deal_time = row.find_element(By.XPATH, './td[4]').text.strip()
#
#                             # 提取价格
#                             price = "无价格信息"
#                             if '元' in goods_spec:
#                                 import re
#                                 price_match = re.search(r'(\d+\.?\d*)元', goods_spec)
#                                 if price_match:
#                                     price = price_match.group(1) + '元'
#
#                             all_deal_data.append({
#                                 '商品链接': url,
#                                 '货品规格': goods_spec,
#                                 '采购量': purchase_quantity,
#                                 '成交时间': deal_time,
#                                 '成交价格': price
#                             })
#                         except Exception as e:
#                             logger.error(f"提取行数据失败 {url} 第{page}页: {str(e)}")
#                             continue
#                 except Exception as e:
#                     logger.error(f"爬取第 {page} 页失败 {url}: {str(e)}")
#                     continue
#
#         except Exception as e:
#             logger.error(f"提取商品数据失败 {url}: {str(e)}")
#         finally:
#             return all_deal_data
#
#     def run(self, input_excel, output_excel, limit=10):
#         """批量爬取指定数量商品的成交数据"""
#         # 读取URL并过滤无效值
#         try:
#             df = pd.read_excel(input_excel)
#         except Exception as e:
#             logger.error(f"读取输入Excel失败: {str(e)}")
#             return
#
#         urls = df['链接'].tolist()
#         urls = [url for url in urls if pd.notna(url) and isinstance(url, str) and url.strip()]
#         urls = urls[:limit]  # 限制爬取数量
#         logger.info(f"共加载 {len(urls)} 个有效商品URL（限制爬取{limit}个）")
#
#         # 爬取数据
#         all_data = []
#         for idx, url in enumerate(urls, 1):
#             logger.info(f"【{idx}/{limit}】开始爬取 {url}")
#             deal_data = self.extract_deal_data(url)
#             all_data.extend(deal_data)
#             # 商品间随机延迟（增强反爬）
#             time.sleep(random.uniform(3, 6))
#
#         # 保存数据
#         if all_data:
#             result_df = pd.DataFrame(all_data)
#             result_df.to_excel(output_excel, index=False)
#             logger.info(f"爬取完成！共 {len(result_df)} 条成交数据，已保存到 {output_excel}")
#         else:
#             logger.warning("未爬取到任何成交数据！")
#
#         # 关闭浏览器
#         self.driver.quit()
#
#
# if __name__ == "__main__":
#     # 实例化并运行爬虫
#     try:
#         spider = HuiNongDealSpider()
#         spider.run('惠农网全品类数据2.xlsx', '惠农网商品成交数据.xlsx', limit=10)
#     except Exception as e:
#         logger.error(f"爬虫运行失败: {str(e)}")
#         # 确保浏览器关闭
#         try:
#             spider.driver.quit()
#         except:
#             pass

# 修改333333333333333333333333

# from selenium import webdriver  # 控制浏览器
# from selenium.webdriver.chrome.service import Service  # 新增：导入Service类
# from selenium.webdriver.common.by import By  # 定位元素的方式（id/xpath等）
# from selenium.webdriver.support.ui import WebDriverWait  # 显式等待（等待元素加载）
# from selenium.webdriver.support import expected_conditions as EC  # 等待的条件（元素可点击）
# from selenium.webdriver.chrome.options import Options  # 谷歌浏览器配置项
# import pandas as pd  # 读写excel文件
# import time  # 固定延迟
# import random  # 生成随机数，用于反爬
# import logging  # 日志记录（记录爬取过程）
#
# # 配置日志
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
#
#
# class HuiNongDealSpider:
#     def __init__(self):
#         # 初始化Chrome配置（增强反爬）
#         chrome_options = Options()
#         # 隐藏自动化标识
#         chrome_options.add_argument('--disable-blink-features=AutomationControlled')
#         chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
#         chrome_options.add_experimental_option('useAutomationExtension', False)
#         # 伪装浏览器UA（避免被识别为爬虫）
#         chrome_options.add_argument(
#             'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
#         # 窗口最大化（避免元素因窗口过小不可见）
#         chrome_options.add_argument('--start-maximized')
#         # 禁用图片加载（提升爬取速度）
#         chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
#
#         # 显式指定ChromeDriver路径
#         service = Service(executable_path=r"C:\Program Files\Google\Chrome\Application\chromedriver.exe")
#         self.driver = webdriver.Chrome(service=service, options=chrome_options)
#
#         # 终极反爬：修改navigator.webdriver为undefined
#         self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
#             'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
#         })
#
#     def extract_deal_data(self, url):
#         all_deal_data = []
#         try:
#             self.driver.get(url)
#             time.sleep(random.uniform(2, 4))
#
#             # 1. 切换到“在线成交”标签
#             deal_tab = WebDriverWait(self.driver, 10).until(
#                 EC.element_to_be_clickable((By.XPATH, '//*[contains(text(), "在线成交")]'))
#             )
#             deal_tab.click()
#             time.sleep(2)
#
#             # 2. 关闭弹窗
#             try:
#                 close_btn = WebDriverWait(self.driver, 5).until(
#                     EC.element_to_be_clickable((By.XPATH, '//i[@class="iconfont icon-guanbi"]'))
#                 )
#                 close_btn.click()
#                 logger.info(f"成功关闭商品 {url} 的弹窗")
#                 time.sleep(1)
#             except Exception as e:
#                 logger.warning(f"商品 {url} 无弹窗或关闭失败: {str(e)}")
#
#             # 3. 滚动到页面（保持原逻辑）
#             self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.4);")
#             time.sleep(random.uniform(1, 2))
#
#             # ========== 重构：循环点击“下一页”按钮直到不可用 ==========
#             current_page = 1
#             while True:
#                 logger.info(f"正在爬取商品 {url} 的第 {current_page} 页成交数据")
#
#                 # 提取当前页数据（保持原逻辑）
#                 try:
#                     deal_rows = WebDriverWait(self.driver, 8).until(
#                         EC.presence_of_all_elements_located((By.XPATH, '//div[@class="line-item"]'))
#                     )
#                     for row in deal_rows:
#                         try:
#                             purchase_quantity = row.find_element(By.XPATH,
#                                                                  './/div[@class="col-3 user-name"]').text.strip()
#                             deal_time = row.find_element(By.XPATH, './/div[@class="col-4 line-time"]').text.strip()
#                             all_deal_data.append({
#                                 '商品链接': url,
#                                 '采购量': purchase_quantity,
#                                 '成交时间': deal_time
#                             })
#                         except Exception as e:
#                             logger.error(f"提取行数据失败 {url} 第{current_page}页: {str(e)}")
#                             continue
#                 except Exception as e:
#                     logger.error(f"提取当前页数据失败 {url} 第{current_page}页: {str(e)}")
#                     break  # 数据提取失败则终止分页
#
#                 # 定位“下一页”按钮，判断是否可点击
#                 # 定位“下一页”按钮（适配截图中的>符号按钮）
#                 try:
#                     # 调试：打印按钮信息（方便排查）
#                     next_btn_elements = self.driver.find_elements(By.XPATH, '//button[@class="btn-next"]')
#                     logger.info(f"商品 {url} 第{current_page}页找到 {len(next_btn_elements)} 个btn-next按钮")
#
#                     # 精准定位：class=btn-next的button（截图中“>”对应的按钮）
#                     next_btn = WebDriverWait(self.driver, 5).until(
#                         EC.element_to_be_clickable((By.XPATH, '//button[@class="btn-next" and not(@disabled)]'))
#                     )
#                     logger.info(
#                         f"成功定位到下一页按钮：标签={next_btn.tag_name}，Class={next_btn.get_attribute('class')}")
#
#                     # 强制滚动到按钮位置（确保按钮在可视区域）
#                     self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
#                     time.sleep(0.5)
#
#                     # 模拟真人点击（移动鼠标+点击）
#                     from selenium.webdriver.common.action_chains import ActionChains
#                     ActionChains(self.driver).move_to_element(next_btn).click(next_btn).perform()
#                     logger.info(f"成功点击商品 {url} 第{current_page}页的下一页按钮（>符号）")
#
#                     current_page += 1
#
#                     # 等待新页面数据加载
#                     WebDriverWait(self.driver, 8).until(
#                         EC.presence_of_element_located((By.XPATH, '//div[@class="line-item"]'))
#                     )
#                     time.sleep(random.uniform(1.5, 2.5))
#
#                 except Exception as e:
#                     logger.error(f"商品 {url} 第{current_page}页点击下一页失败：{str(e)}")
#                     logger.info(f"商品 {url} 已爬取到最后一页（共 {current_page} 页）")
#                     break
#             # ======================================================
#
#         except Exception as e:
#             logger.error(f"提取商品数据失败 {url}: {str(e)}")
#         finally:
#             return all_deal_data
#
#     def run(self, input_excel, output_excel, limit=10):
#         """批量爬取指定数量商品的成交数据"""
#         try:
#             df = pd.read_excel(input_excel)
#         except Exception as e:
#             logger.error(f"读取输入Excel失败: {str(e)}")
#             return
#
#         urls = df['链接'].tolist()
#         urls = [url for url in urls if pd.notna(url) and isinstance(url, str) and url.strip()]
#         urls = urls[:limit]
#         logger.info(f"共加载 {len(urls)} 个有效商品URL（限制爬取{limit}个）")
#
#         all_data = []
#         for idx, url in enumerate(urls, 1):
#             logger.info(f"【{idx}/{limit}】开始爬取 {url}")
#             deal_data = self.extract_deal_data(url)
#             all_data.extend(deal_data)
#             time.sleep(random.uniform(3, 6))
#
#         if all_data:
#             result_df = pd.DataFrame(all_data)
#             result_df.to_excel(output_excel, index=False)
#             logger.info(f"爬取完成！共 {len(result_df)} 条成交数据，已保存到 {output_excel}")
#         else:
#             logger.warning("未爬取到任何成交数据！")
#
#         self.driver.quit()
#
#
# if __name__ == "__main__":
#     try:
#         spider = HuiNongDealSpider()
#         spider.run('惠农网全品类数据2.xlsx', '惠农网商品成交数据.xlsx', limit=10)
#     except Exception as e:
#         logger.error(f"爬虫运行失败: {str(e)}")
#         try:
#             spider.driver.quit()
#         except:
#             pass

# 修改^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.action_chains import ActionChains
# import pandas as pd
# import time
# import random
# import logging
#
# # 配置日志
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
#
#
# class HuiNongDealSpider:
#     def __init__(self):
#         chrome_options = Options()
#         chrome_options.add_argument('--disable-blink-features=AutomationControlled')
#         chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
#         chrome_options.add_experimental_option('useAutomationExtension', False)
#         chrome_options.add_argument(
#             'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
#         chrome_options.add_argument('--start-maximized')
#         chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
#
#         service = Service(executable_path=r"C:\Program Files\Google\Chrome\Application\chromedriver.exe")
#         self.driver = webdriver.Chrome(service=service, options=chrome_options)
#         self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
#             'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
#         })
#
#     def extract_deal_data(self, url):
#         all_deal_data = []
#         try:
#             self.driver.get(url)
#             time.sleep(random.uniform(2, 4))
#
#             # 1. 切换到“在线成交”标签
#             deal_tab = WebDriverWait(self.driver, 10).until(
#                 EC.element_to_be_clickable((By.XPATH, '//*[contains(text(), "在线成交")]'))
#             )
#             deal_tab.click()
#             time.sleep(2)
#
#             # 2. 关闭弹窗
#             try:
#                 close_btn = WebDriverWait(self.driver, 5).until(
#                     EC.element_to_be_clickable((By.XPATH, '//i[@class="iconfont icon-guanbi"]'))
#                 )
#                 close_btn.click()
#                 logger.info(f"成功关闭商品 {url} 的弹窗")
#                 time.sleep(1)
#             except Exception as e:
#                 logger.warning(f"商品 {url} 无弹窗或关闭失败: {str(e)}")
#
#             # 3. 滚动到成交数据区域
#             self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.4);")
#             time.sleep(random.uniform(1, 2))
#
#             current_page = 1
#             while True:
#                 logger.info(f"正在爬取商品 {url} 的第 {current_page} 页成交数据")
#
#                 # ========== 修复：简化数据提取XPath，恢复数据采集 ==========
#                 try:
#                     # 只定位line-item，不额外过滤（先恢复数据）
#                     deal_rows = WebDriverWait(self.driver, 8).until(
#                         EC.presence_of_all_elements_located((By.XPATH, '//div[@class="line-item"]'))
#                     )
#                     page_data = []
#                     for row in deal_rows:
#                         try:
#                             # 适配页面实际的列（如果class不对，可改为按索引定位）
#                             # 方案1：按class定位（优先）
#                             try:
#                                 purchase_quantity = row.find_element(By.XPATH, './/div[contains(@class, "col-3")]').text.strip()
#                                 deal_time = row.find_element(By.XPATH, './/div[contains(@class, "col-4")]').text.strip()
#                             # 方案2：按列索引定位（兜底）
#                             except:
#                                 cols = row.find_elements(By.XPATH, './div')
#                                 purchase_quantity = cols[2].text.strip() if len(cols)>=3 else ""
#                                 deal_time = cols[3].text.strip() if len(cols)>=4 else ""
#
#                             # 保留非空数据
#                             if purchase_quantity or deal_time:
#                                 page_data.append({
#                                     '商品链接': url,
#                                     '采购量': purchase_quantity,
#                                     '成交时间': deal_time
#                                 })
#                         except Exception as e:
#                             logger.error(f"提取行数据失败 {url} 第{current_page}页: {str(e)}")
#                             continue
#                     all_deal_data.extend(page_data)
#                     logger.info(f"商品 {url} 第{current_page}页提取到 {len(page_data)} 条数据")
#                 except Exception as e:
#                     logger.error(f"提取当前页数据失败 {url} 第{current_page}页: {str(e)}")
#                     break
#                 # ==========================================================
#
#                 # 定位下一页按钮（简化逻辑）
#                 try:
#                     next_btn = WebDriverWait(self.driver, 5).until(
#                         EC.element_to_be_clickable((By.XPATH, '//button[@class="btn-next"]'))
#                     )
#                     self.driver.execute_script("arguments[0].scrollIntoView();", next_btn)
#                     time.sleep(1)
#                     next_btn.click()
#                     current_page += 1
#                     time.sleep(random.uniform(2, 3))
#                 except:
#                     logger.info(f"商品 {url} 已爬取到最后一页（共 {current_page} 页）")
#                     break
#
#
#         except Exception as e:
#             logger.error(f"提取商品数据失败 {url}: {str(e)}")
#         finally:
#             return all_deal_data
#
#     def run(self, input_excel, output_excel, limit=10):
#         try:
#             df = pd.read_excel(input_excel)
#         except Exception as e:
#             logger.error(f"读取输入Excel失败: {str(e)}")
#             return
#
#         urls = df['链接'].tolist()
#         urls = [url for url in urls if pd.notna(url) and isinstance(url, str) and url.strip()]
#         urls = urls[:limit]
#         logger.info(f"共加载 {len(urls)} 个有效商品URL")
#
#         all_data = []
#         for idx, url in enumerate(urls, 1):
#             logger.info(f"【{idx}/{limit}】开始爬取 {url}")
#             deal_data = self.extract_deal_data(url)
#             all_data.extend(deal_data)
#             time.sleep(random.uniform(3, 6))
#
#         if all_data:
#             result_df = pd.DataFrame(all_data)
#             result_df.to_excel(output_excel, index=False)
#             logger.info(f"爬取完成！共 {len(result_df)} 条成交数据，已保存到 {output_excel}")
#         else:
#             logger.warning("未爬取到任何成交数据！")
#
#         self.driver.quit()
#
#
# if __name__ == "__main__":
#     try:
#         spider = HuiNongDealSpider()
#         spider.run('惠农网全品类数据2.xlsx', '惠农网商品成交数据.xlsx', limit=10)
#     except Exception as e:
#         logger.error(f"爬虫运行失败: {str(e)}")
#         try:
#             spider.driver.quit()
#         except:
#             pass

#
# # 豆包改
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.action_chains import ActionChains
# import pandas as pd
# import time
# import random
# import logging
#
# # 配置日志
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
#
#
# class HuiNongDealSpider:
#     def __init__(self):
#         chrome_options = Options()
#         chrome_options.add_argument('--disable-blink-features=AutomationControlled')
#         chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
#         chrome_options.add_experimental_option('useAutomationExtension', False)
#         chrome_options.add_argument(
#             'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
#         chrome_options.add_argument('--start-maximized')
#         chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
#
#         service = Service(executable_path=r"C:\Program Files\Google\Chrome\Application\chromedriver.exe")
#         self.driver = webdriver.Chrome(service=service, options=chrome_options)
#         self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
#             'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
#         })
#
#     def extract_deal_data(self, url):
#         all_deal_data = []
#         try:
#             self.driver.get(url)
#             time.sleep(random.uniform(2, 4))
#
#             # 1. 切换到“在线成交”标签
#             deal_tab = WebDriverWait(self.driver, 10).until(
#                 EC.element_to_be_clickable((By.XPATH, '//*[contains(text(), "在线成交")]'))
#             )
#             deal_tab.click()
#             time.sleep(2)
#
#             # 2. 关闭弹窗
#             try:
#                 close_btn = WebDriverWait(self.driver, 5).until(
#                     EC.element_to_be_clickable((By.XPATH, '//i[@class="iconfont icon-guanbi"]'))
#                 )
#                 close_btn.click()
#                 logger.info(f"成功关闭商品 {url} 的弹窗")
#                 time.sleep(1)
#             except Exception as e:
#                 logger.warning(f"商品 {url} 无弹窗或关闭失败: {str(e)}")
#
#             # 3. 滚动到成交数据区域 【你的原版代码，保留】
#             self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.4);")
#             time.sleep(random.uniform(1, 2))
#
#             current_page = 1
#             max_pages = 200  # 加安全限制，防止无限循环
#             while current_page <= max_pages:
#                 logger.info(f"正在爬取商品 {url} 的第 {current_page} 页成交数据")
#
#                 # ========== 你的原版数据提取逻辑，完全保留，不用改 ==========
#                 try:
#                     deal_rows = WebDriverWait(self.driver, 8).until(
#                         EC.presence_of_all_elements_located((By.XPATH, '//div[@class="line-item"]'))
#                     )
#                     page_data = []
#                     for row in deal_rows:
#                         try:
#                             try:
#                                 purchase_quantity = row.find_element(By.XPATH,
#                                                                      './/div[contains(@class, "col-3")]').text.strip()
#                                 deal_time = row.find_element(By.XPATH, './/div[contains(@class, "col-4")]').text.strip()
#                             except:
#                                 cols = row.find_elements(By.XPATH, './div')
#                                 purchase_quantity = cols[2].text.strip() if len(cols) >= 3 else ""
#                                 deal_time = cols[3].text.strip() if len(cols) >= 4 else ""
#
#                             if purchase_quantity or deal_time:
#                                 page_data.append({
#                                     '商品链接': url,
#                                     '采购量': purchase_quantity,
#                                     '成交时间': deal_time
#                                 })
#                         except Exception as e:
#                             logger.error(f"提取行数据失败 {url} 第{current_page}页: {str(e)}")
#                             continue
#                     all_deal_data.extend(page_data)
#                     logger.info(f"商品 {url} 第{current_page}页提取到 {len(page_data)} 条数据")
#                 except Exception as e:
#                     logger.error(f"提取当前页数据失败 {url} 第{current_page}页: {str(e)}")
#                     break
#                 # ==========================================================
#
#                 # ======================== 核心修复：翻页逻辑 全部重写 ========================
#                 try:
#                     # ✅ 修改1：使用你提供的【精准绝对XPATH】定位下一页按钮，唯一不重复，绝对正确
#                     next_btn_xpath = '/html/body/div[1]/div/div/div/div[3]/div[2]/div[2]/div[1]/div/div[3]/div[2]/div[13]/button[2]'
#                     next_btn = WebDriverWait(self.driver, 6).until(
#                         EC.element_to_be_clickable((By.XPATH, next_btn_xpath))
#                     )
#
#                     # ✅ 修改2：优化滚动，确保按钮完全显示在可视区，居中滚动，点击必中
#                     self.driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});",
#                                                next_btn)
#                     time.sleep(0.8)
#
#                     # ✅ 修改3：JS点击优先 + 原生点击兜底，稳定性拉满，必触发翻页事件
#                     try:
#                         # 最优方案：JS点击，无视嵌套/坐标/遮挡，100%触发按钮的点击事件
#                         self.driver.execute_script("arguments[0].click();", next_btn)
#                     except:
#                         # 兜底方案：模拟鼠标点击
#                         ActionChains(self.driver).move_to_element(next_btn).click().perform()
#
#                     logger.info(f"✅ 商品 {url} 成功点击第{current_page}页的下一页按钮")
#
#                     # ✅ 修改4：翻页后【关键校验】等待新数据加载完成，杜绝提取重复数据+判定失败
#                     # 等待新的成交数据行加载出来，证明翻页成功，且页面渲染完成
#                     WebDriverWait(self.driver, 10).until(
#                         EC.staleness_of(deal_rows[0])  # 校验：上一页的第一条数据已失效（新页面加载完成）
#                     )
#
#                     current_page += 1
#                     time.sleep(random.uniform(2, 3.5))  # 随机等待，防反爬+等待数据渲染
#
#                 except Exception as e:
#                     # 只有当按钮找不到/点击失败/加载超时，才判定为最后一页
#                     logger.info(f"商品 {url} 已爬取到最后一页（共 {current_page} 页），原因: {str(e)[:50]}")
#                     break
#
#         except Exception as e:
#             logger.error(f"提取商品数据失败 {url}: {str(e)}")
#         finally:
#             return all_deal_data
#
#     def run(self, input_excel, output_excel, limit=10):
#         try:
#             df = pd.read_excel(input_excel)
#         except Exception as e:
#             logger.error(f"读取输入Excel失败: {str(e)}")
#             return
#
#         urls = df['链接'].tolist()
#         urls = [url for url in urls if pd.notna(url) and isinstance(url, str) and url.strip()]
#         urls = urls[:limit]
#         logger.info(f"共加载 {len(urls)} 个有效商品URL")
#
#         all_data = []
#         for idx, url in enumerate(urls, 1):
#             logger.info(f"【{idx}/{limit}】开始爬取 {url}")
#             deal_data = self.extract_deal_data(url)
#             all_data.extend(deal_data)
#             time.sleep(random.uniform(3, 6))
#
#         if all_data:
#             result_df = pd.DataFrame(all_data)
#             result_df.to_excel(output_excel, index=False)
#             logger.info(f"爬取完成！共 {len(result_df)} 条成交数据，已保存到 {output_excel}")
#         else:
#             logger.warning("未爬取到任何成交数据！")
#
#         self.driver.quit()
#
#
# if __name__ == "__main__":
#     try:
#         spider = HuiNongDealSpider()
#         spider.run('惠农网全品类数据2.xlsx', '惠农网商品成交数据.xlsx', limit=10)
#     except Exception as e:
#         logger.error(f"爬虫运行失败: {str(e)}")
#         try:
#             spider.driver.quit()
#         except:
#             pass



# 文件，，，，页码出错
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from selenium.common.exceptions import (
#     TimeoutException,
#     NoSuchElementException,
#     ElementNotInteractableException,
#     StaleElementReferenceException
# )
# import pandas as pd
# import time
# import random
# import logging
# import os
# from datetime import datetime
# import json
# import re
#
#
# # ========== 配置日志 ==========
# def setup_logging():
#     """配置日志系统"""
#     log_dir = "logs"
#     if not os.path.exists(log_dir):
#         os.makedirs(log_dir)
#
#     log_filename = os.path.join(log_dir, f"huinong_spider_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
#
#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s - %(levelname)s - %(message)s',
#         handlers=[
#             logging.FileHandler(log_filename, encoding='utf-8'),
#             logging.StreamHandler()
#         ]
#     )
#
#     return logging.getLogger(__name__)
#
#
# logger = setup_logging()
#
#
# # ========== 浏览器管理器 ==========
# class BrowserManager:
#     @staticmethod
#     def create_driver():
#         """创建Chrome浏览器驱动"""
#         try:
#             chrome_options = Options()
#
#             # 基础设置
#             chrome_options.add_argument('--disable-blink-features=AutomationControlled')
#             chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
#             chrome_options.add_experimental_option('useAutomationExtension', False)
#
#             # 性能优化
#             chrome_options.add_argument('--disable-dev-shm-usage')
#             chrome_options.add_argument('--no-sandbox')
#             chrome_options.add_argument('--disable-gpu')
#             chrome_options.add_argument('--disable-web-security')
#
#             # 用户代理
#             user_agents = [
#                 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
#                 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
#                 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
#             ]
#             chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')
#
#             chrome_options.add_argument('--start-maximized')
#             chrome_options.add_argument('--disable-infobars')
#
#             # 禁用图片和视频
#             prefs = {
#                 "profile.managed_default_content_settings.images": 2,
#                 "profile.managed_default_content_settings.stylesheets": 2,
#                 "profile.managed_default_content_settings.javascript": 1,
#                 "profile.default_content_setting_values.notifications": 2,
#                 "credentials_enable_service": False,
#                 "profile.password_manager_enabled": False
#             }
#             chrome_options.add_experimental_option("prefs", prefs)
#
#             # Chrome驱动路径 - 设置为你提供的路径
#             driver_paths = [
#                 r"C:\Program Files\Google\Chrome\Application\chromedriver.exe",
#                 r"C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe",
#                 os.path.join(os.getcwd(), "chromedriver.exe")
#             ]
#
#             service = None
#             for path in driver_paths:
#                 if os.path.exists(path):
#                     try:
#                         service = Service(executable_path=path)
#                         logger.info(f"使用Chrome驱动: {path}")
#                         break
#                     except Exception as e:
#                         logger.warning(f"驱动路径 {path} 不可用: {str(e)}")
#                         continue
#
#             if service is None:
#                 logger.warning("未找到指定的Chrome驱动，尝试自动检测")
#                 # 如果不指定路径，Selenium会尝试自动查找
#                 service = Service()
#
#             # 创建驱动
#             driver = webdriver.Chrome(service=service, options=chrome_options)
#
#             # 隐藏自动化特征
#             driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
#                 'source': '''
#                     Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
#                     Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
#                     Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
#                 '''
#             })
#
#             driver.set_page_load_timeout(30)
#             driver.set_script_timeout(30)
#
#             logger.info("Chrome浏览器初始化成功")
#             return driver
#
#         except Exception as e:
#             logger.error(f"Chrome浏览器初始化失败: {str(e)}")
#             # 尝试更简化的方式
#             try:
#                 logger.info("尝试使用简化方式初始化Chrome...")
#                 chrome_options = Options()
#                 chrome_options.add_argument('--disable-blink-features=AutomationControlled')
#                 chrome_options.add_argument('--disable-dev-shm-usage')
#                 chrome_options.add_argument('--no-sandbox')
#                 chrome_options.add_argument('--disable-gpu')
#                 chrome_options.add_argument('--start-maximized')
#                 chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
#
#                 service = Service(executable_path=r"C:\Program Files\Google\Chrome\Application\chromedriver.exe")
#                 driver = webdriver.Chrome(service=service, options=chrome_options)
#
#                 driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
#                     'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
#                 })
#
#                 logger.info("Chrome浏览器初始化成功（简化模式）")
#                 return driver
#             except Exception as e2:
#                 logger.error(f"简化方式初始化也失败: {str(e2)}")
#                 raise
#
#
# # ========== 分页检测器 ==========
# class PaginationDetector:
#     """专门用于检测分页的类"""
#
#     def __init__(self, driver):
#         self.driver = driver
#
#     def detect_all_pagination_elements(self):
#         """检测所有可能的分页元素"""
#         logger.info("开始检测分页元素...")
#
#         # 存储所有找到的元素信息
#         found_elements = []
#
#         # 1. 首先等待可能的动态加载
#         time.sleep(3)
#
#         # 2. 滚动到页面底部（分页通常在底部）
#         self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(2)
#
#         # 3. 尝试多种分页选择器
#         pagination_patterns = [
#             # 类名包含 pagination
#             ("CSS", "[class*='pagination']"),
#             ("CSS", "[class*='Pagination']"),
#             ("CSS", ".pagination"),
#             ("CSS", ".Pagination"),
#
#             # 类名包含 page
#             ("CSS", "[class*='page']"),
#             ("CSS", "[class*='Page']"),
#
#             # 包含页码的容器
#             ("XPATH", "//div[contains(@class, 'list-pagination')]"),
#             ("XPATH", "//div[contains(@class, 'eye-pagination')]"),
#             ("XPATH", "//div[contains(@class, 'pagination-container')]"),
#             ("XPATH", "//div[contains(@class, 'pagination-wrapper')]"),
#
#             # ul/li 分页
#             ("XPATH", "//ul[contains(@class, 'pagination')]"),
#             ("XPATH", "//ul[@class='pagination']"),
#             ("XPATH", "//div/ul[contains(@class, 'pagination')]"),
#
#             # 按钮组
#             ("XPATH", "//div[@class='btn-group']"),
#             ("XPATH", "//div[contains(@class, 'pager')]"),
#
#             # 包含"页"字的元素
#             ("XPATH", "//*[contains(text(), '页')]"),
#             ("XPATH", "//*[contains(text(), 'Page')]"),
#             ("XPATH", "//*[contains(text(), 'page')]"),
#
#             # 数字按钮
#             ("XPATH", "//button[text()='1']"),
#             ("XPATH", "//button[text()='2']"),
#             ("XPATH", "//li[text()='1']"),
#             ("XPATH", "//li[text()='2']"),
#
#             # 下一页按钮
#             ("XPATH", "//button[contains(text(), '下一页')]"),
#             ("XPATH", "//button[contains(text(), 'Next')]"),
#             ("XPATH", "//a[contains(text(), '下一页')]"),
#             ("XPATH", "//li[contains(text(), '下一页')]"),
#         ]
#
#         for by, selector in pagination_patterns:
#             try:
#                 if by == "CSS":
#                     elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
#                 else:  # XPATH
#                     elements = self.driver.find_elements(By.XPATH, selector)
#
#                 for idx, element in enumerate(elements):
#                     try:
#                         if element.is_displayed():
#                             text = element.text.strip()
#                             html = element.get_attribute('outerHTML')[:200]  # 取前200个字符
#                             found_elements.append({
#                                 'selector': f"{by}: {selector}",
#                                 'index': idx,
#                                 'text': text,
#                                 'html': html,
#                                 'element': element
#                             })
#                             logger.info(f"找到分页元素: {by}:{selector}, 文本: '{text}'")
#                     except:
#                         continue
#
#             except Exception as e:
#                 continue
#
#         logger.info(f"总共找到 {len(found_elements)} 个分页相关元素")
#
#         # 打印详细信息
#         for elem in found_elements:
#             logger.debug(f"元素: {elem['selector']}, 文本: '{elem['text']}'")
#
#         return found_elements
#
#     def get_total_pages(self):
#         """获取总页数 - 增强版"""
#         logger.info("开始获取总页数...")
#
#         # 方法1: 通过分页元素获取
#         pagination_elements = self.detect_all_pagination_elements()
#
#         # 尝试从元素中提取页码
#         page_numbers = set()
#
#         for elem in pagination_elements:
#             text = elem['text']
#             html = elem['html']
#
#             # 提取数字（页码）
#             numbers = re.findall(r'\b\d+\b', text)
#             for num in numbers:
#                 try:
#                     page_num = int(num)
#                     if 1 <= page_num <= 100:  # 合理的页码范围
#                         page_numbers.add(page_num)
#                 except:
#                     pass
#
#             # 从HTML属性中提取
#             if 'html' in elem:
#                 html_numbers = re.findall(r'data-page=["\']?(\d+)["\']?', html)
#                 html_numbers += re.findall(r'page=["\']?(\d+)["\']?', html)
#                 html_numbers += re.findall(r'p=["\']?(\d+)["\']?', html)
#
#                 for num in html_numbers:
#                     try:
#                         page_num = int(num)
#                         if 1 <= page_num <= 100:
#                             page_numbers.add(page_num)
#                     except:
#                         pass
#
#         # 如果找到了页码数字
#         if page_numbers:
#             max_page = max(page_numbers)
#             logger.info(f"从分页元素中检测到最大页码: {max_page}")
#             return max_page
#
#         # 方法2: 通过数据量估算
#         try:
#             data_rows = self.driver.find_elements(By.XPATH, '//div[@class="line-item"]')
#             if data_rows:
#                 rows_per_page = len(data_rows)
#                 logger.info(f"当前页有 {rows_per_page} 行数据")
#
#                 # 尝试获取总数据量（如果有显示）
#                 try:
#                     total_text_elements = self.driver.find_elements(By.XPATH,
#                                                                     "//*[contains(text(), '共') and contains(text(), '条')] | "
#                                                                     "//*[contains(text(), 'total') and contains(text(), 'records')]"
#                                                                     )
#
#                     for elem in total_text_elements:
#                         text = elem.text
#                         match = re.search(r'(\d+)\s*条', text) or re.search(r'(\d+)\s*records', text)
#                         if match:
#                             total_records = int(match.group(1))
#                             estimated_pages = (total_records + rows_per_page - 1) // rows_per_page
#                             logger.info(f"估算总页数: {estimated_pages} (共{total_records}条，每页{rows_per_page}条)")
#                             return min(estimated_pages, 50)  # 限制最大50页
#                 except:
#                     pass
#
#                 # 如果有下一页按钮，假设至少有多页
#                 next_buttons = self.driver.find_elements(By.XPATH,
#                                                          "//button[contains(text(), '下一页')] | "
#                                                          "//button[contains(text(), 'Next')] | "
#                                                          "//a[contains(text(), '下一页')]"
#                                                          )
#
#                 for btn in next_buttons:
#                     if btn.is_displayed() and btn.is_enabled():
#                         logger.info("检测到下一页按钮，假设至少有多页")
#                         return 10  # 默认先爬10页
#         except Exception as e:
#             logger.warning(f"通过数据量估算失败: {str(e)}")
#
#         # 方法3: 尝试点击下一页看看
#         try:
#             logger.info("尝试点击下一页按钮进行测试...")
#             next_buttons = self.driver.find_elements(By.XPATH,
#                                                      "//button[contains(text(), '下一页')] | "
#                                                      "//button[contains(text(), 'Next')]"
#                                                      )
#
#             for btn in next_buttons:
#                 if btn.is_displayed() and btn.is_enabled():
#                     # 保存当前URL和数据
#                     original_url = self.driver.current_url
#                     original_data_count = len(self.driver.find_elements(By.XPATH, '//div[@class="line-item"]'))
#
#                     # 点击下一页
#                     self.driver.execute_script("arguments[0].click();", btn)
#                     time.sleep(3)
#
#                     # 检查是否翻页成功
#                     new_data_count = len(self.driver.find_elements(By.XPATH, '//div[@class="line-item"]'))
#
#                     if new_data_count > 0 and new_data_count != original_data_count:
#                         logger.info("下一页存在数据，至少有2页")
#
#                         # 返回第一页
#                         self.driver.get(original_url)
#                         time.sleep(3)
#                         return 10  # 至少有2页，默认爬10页
#                     else:
#                         # 返回原页面
#                         self.driver.get(original_url)
#                         time.sleep(3)
#                         break
#
#         except Exception as e:
#             logger.warning(f"测试下一页点击失败: {str(e)}")
#
#         logger.info("未检测到多页，默认为1页")
#         return 1
#
#
# # ========== 数据提取器 ==========
# class DataExtractor:
#     def __init__(self, driver):
#         self.driver = driver
#         self.pagination_detector = PaginationDetector(driver)
#
#     def close_popups(self):
#         """关闭弹窗"""
#         try:
#             selectors = [
#                 '//i[contains(@class, "icon-guanbi")]',
#                 '//div[contains(@class, "modal-close")]',
#                 '//button[contains(@class, "close")]',
#                 '//span[contains(@class, "close")]',
#                 '//div[contains(@class, "close-btn")]'
#             ]
#
#             for selector in selectors:
#                 try:
#                     elements = self.driver.find_elements(By.XPATH, selector)
#                     for element in elements:
#                         if element.is_displayed():
#                             try:
#                                 element.click()
#                                 time.sleep(0.5)
#                             except:
#                                 self.driver.execute_script("arguments[0].click();", element)
#                             logger.info("关闭弹窗成功")
#                             break
#                 except:
#                     continue
#         except Exception as e:
#             logger.warning(f"关闭弹窗失败: {str(e)}")
#
#     def switch_to_deal_tab(self):
#         """切换到在线成交标签"""
#         logger.info("正在切换到在线成交标签...")
#
#         try:
#             time.sleep(2)
#
#             tab_selectors = [
#                 '//*[contains(text(), "在线成交")]',
#                 '//div[contains(text(), "在线成交")]',
#                 '//span[contains(text(), "在线成交")]',
#                 '//button[contains(text(), "在线成交")]',
#                 '//a[contains(text(), "在线成交")]'
#             ]
#
#             for selector in tab_selectors:
#                 try:
#                     elements = self.driver.find_elements(By.XPATH, selector)
#                     for element in elements:
#                         if element.is_displayed() and element.is_enabled():
#                             self.driver.execute_script("arguments[0].scrollIntoView();", element)
#                             time.sleep(1)
#
#                             try:
#                                 element.click()
#                             except:
#                                 self.driver.execute_script("arguments[0].click();", element)
#
#                             logger.info("成功切换到在线成交标签")
#                             time.sleep(3)
#                             return True
#                 except:
#                     continue
#
#             logger.error("未找到在线成交标签")
#             return False
#
#         except Exception as e:
#             logger.error(f"切换标签失败: {str(e)}")
#             return False
#
#     def extract_page_data(self, url, page_num):
#         """提取当前页数据"""
#         data = []
#
#         try:
#             time.sleep(2)
#
#             rows = self.driver.find_elements(By.XPATH, '//div[@class="line-item"]')
#
#             if not rows:
#                 logger.warning(f"第{page_num}页未找到数据行")
#                 return data
#
#             logger.info(f"第{page_num}页找到 {len(rows)} 行数据")
#
#             for idx, row in enumerate(rows):
#                 try:
#                     cols = row.find_elements(By.XPATH, './div')
#
#                     if len(cols) >= 4:
#                         purchase_quantity = cols[2].text.strip() if cols[2].text else ""
#                         deal_time = cols[3].text.strip() if cols[3].text else ""
#
#                         if purchase_quantity or deal_time:
#                             data.append({
#                                 '商品链接': url,
#                                 '采购量': purchase_quantity,
#                                 '成交时间': deal_time,
#                                 '页码': page_num,
#                                 '行号': idx + 1,
#                                 '采集时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                             })
#                 except Exception as e:
#                     logger.warning(f"提取行数据失败: {str(e)}")
#                     continue
#
#             logger.info(f"第{page_num}页提取到 {len(data)} 条数据")
#
#         except Exception as e:
#             logger.error(f"提取第{page_num}页数据失败: {str(e)}")
#
#         return data
#
#     def go_to_next_page(self, current_page):
#         """翻到下一页"""
#         next_page_num = current_page + 1
#         logger.info(f"尝试翻到第 {next_page_num} 页")
#
#         try:
#             # 尝试多种下一页按钮
#             next_selectors = [
#                 f'//button[text()="{next_page_num}"]',
#                 f'//li[text()="{next_page_num}"]',
#                 f'//a[text()="{next_page_num}"]',
#                 '//button[contains(text(), "下一页")]',
#                 '//button[contains(text(), "Next")]',
#                 '//li[contains(text(), "下一页")]',
#                 '//button[contains(@class, "next")]',
#                 '//li[contains(@class, "next")]',
#                 '//a[contains(@class, "next")]'
#             ]
#
#             for selector in next_selectors:
#                 try:
#                     elements = self.driver.find_elements(By.XPATH, selector)
#                     for element in elements:
#                         if element.is_displayed() and element.is_enabled():
#                             # 保存当前数据用于验证
#                             original_data = self.driver.find_elements(By.XPATH, '//div[@class="line-item"]')
#
#                             # 滚动并点击
#                             self.driver.execute_script("arguments[0].scrollIntoView();", element)
#                             time.sleep(1)
#
#                             self.driver.execute_script("arguments[0].click();", element)
#
#                             # 等待新数据加载
#                             time.sleep(3)
#
#                             # 验证是否翻页成功
#                             new_data = self.driver.find_elements(By.XPATH, '//div[@class="line-item"]')
#                             if new_data:
#                                 logger.info(f"成功翻到第 {next_page_num} 页")
#                                 return True
#                 except:
#                     continue
#
#             logger.error(f"翻到第 {next_page_num} 页失败")
#             return False
#
#         except Exception as e:
#             logger.error(f"翻页失败: {str(e)}")
#             return False
#
#
# # ========== 主爬虫类 ==========
# class HuiNongDealSpider:
#     def __init__(self):
#         self.driver = None
#         self.data_extractor = None
#         self.stats = {
#             'total_urls': 0,
#             'success_urls': 0,
#             'failed_urls': 0,
#             'total_records': 0,
#             'total_pages': 0
#         }
#
#     def init_browser(self):
#         """初始化浏览器"""
#         logger.info("=" * 60)
#         logger.info("惠农网成交数据爬虫启动 - 分页检测增强版")
#         logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
#         logger.info("=" * 60)
#
#         try:
#             self.driver = BrowserManager.create_driver()
#             self.data_extractor = DataExtractor(self.driver)
#             logger.info("Chrome浏览器初始化完成")
#         except Exception as e:
#             logger.error(f"Chrome浏览器初始化失败: {str(e)}")
#             raise
#
#     def load_urls(self, excel_path, limit=None):
#         """从Excel加载URL"""
#         try:
#             if not os.path.exists(excel_path):
#                 logger.error(f"Excel文件不存在: {excel_path}")
#                 return []
#
#             df = pd.read_excel(excel_path)
#
#             if '链接' not in df.columns:
#                 logger.error("Excel中缺少'链接'列")
#                 return []
#
#             urls = []
#             for url in df['链接']:
#                 if pd.isna(url):
#                     continue
#
#                 url_str = str(url).strip()
#                 if url_str and url_str.startswith('http'):
#                     urls.append(url_str)
#
#             if limit and len(urls) > limit:
#                 urls = urls[:limit]
#
#             logger.info(f"加载 {len(urls)} 个URL")
#             return urls
#
#         except Exception as e:
#             logger.error(f"加载URL失败: {str(e)}")
#             return []
#
#     def crawl_single_product(self, url, product_idx, total_products):
#         """爬取单个商品"""
#         logger.info(f"\n{'=' * 60}")
#         logger.info(f"【{product_idx}/{total_products}】开始爬取商品")
#         logger.info(f"URL: {url}")
#         logger.info(f"{'=' * 60}")
#
#         product_data = []
#
#         try:
#             # 1. 访问页面
#             logger.info("访问商品页面...")
#             self.driver.get(url)
#             time.sleep(random.uniform(5, 8))
#
#             # 2. 关闭弹窗
#             self.data_extractor.close_popups()
#
#             # 3. 切换到在线成交标签
#             if not self.data_extractor.switch_to_deal_tab():
#                 logger.error("无法切换到在线成交标签，跳过此商品")
#                 return product_data
#
#             # 4. 再次关闭弹窗
#             self.data_extractor.close_popups()
#             time.sleep(2)
#
#             # 5. 获取总页数（使用增强的分页检测）
#             total_pages = self.data_extractor.pagination_detector.get_total_pages()
#             logger.info(f"检测到总页数: {total_pages}")
#
#             # 如果只有1页，但我们怀疑有多页，强制检查一下
#             if total_pages == 1:
#                 logger.warning("检测到只有1页，但怀疑可能有多页，将尝试额外检查...")
#
#                 # 额外检查：查看是否有"查看更多"或"加载更多"按钮
#                 load_more_selectors = [
#                     '//button[contains(text(), "加载更多")]',
#                     '//button[contains(text(), "查看更多")]',
#                     '//button[contains(text(), "Load More")]',
#                     '//div[contains(text(), "加载更多")]'
#                 ]
#
#                 for selector in load_more_selectors:
#                     try:
#                         elements = self.driver.find_elements(By.XPATH, selector)
#                         if elements:
#                             logger.info(f"发现'{selector}'，可能存在更多数据")
#                             total_pages = 10  # 假设有10页
#                             break
#                     except:
#                         continue
#
#             # 6. 逐页爬取
#             for page_num in range(1, total_pages + 1):
#                 logger.info(f"正在爬取第 {page_num}/{total_pages} 页")
#
#                 # 提取当前页数据
#                 page_data = self.data_extractor.extract_page_data(url, page_num)
#                 product_data.extend(page_data)
#
#                 logger.info(f"第{page_num}页完成，累计 {len(product_data)} 条数据")
#
#                 # 如果不是最后一页，尝试翻页
#                 if page_num < total_pages:
#                     # 尝试翻页，最多重试3次
#                     success = False
#                     for retry in range(3):
#                         logger.info(f"尝试翻页到第 {page_num + 1} 页 (重试 {retry + 1}/3)")
#
#                         if self.data_extractor.go_to_next_page(page_num):
#                             success = True
#                             break
#                         else:
#                             logger.warning(f"翻页失败，等待后重试...")
#                             time.sleep(2)
#
#                     if not success:
#                         logger.error(f"翻页重试次数用尽，停止翻页")
#                         break
#
#             logger.info(f"商品爬取完成，共获取 {len(product_data)} 条数据")
#
#             return product_data
#
#         except Exception as e:
#             logger.error(f"爬取商品失败: {str(e)}")
#             return product_data
#
#     def save_results(self, data, output_path):
#         """保存结果"""
#         try:
#             if not data:
#                 logger.warning("没有数据需要保存")
#                 return
#
#             df = pd.DataFrame(data)
#             df.to_excel(output_path, index=False)
#
#             logger.info(f"数据已保存到: {output_path}")
#             logger.info(f"总记录数: {len(df)}")
#
#             # 统计信息
#             if '页码' in df.columns:
#                 unique_pages = df['页码'].unique()
#                 logger.info(f"实际爬取的页码: {sorted(unique_pages)}")
#
#         except Exception as e:
#             logger.error(f"保存结果失败: {str(e)}")
#
#     def run(self, input_excel=None, output_excel=None, limit=5):
#         """运行爬虫"""
#
#         if input_excel is None:
#             input_excel = "惠农网全品类数据2.xlsx"
#         if output_excel is None:
#             output_excel = f"惠农网成交数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
#
#         all_data = []
#
#         try:
#             # 1. 初始化浏览器
#             self.init_browser()
#
#             # 2. 加载URL
#             urls = self.load_urls(input_excel, limit)
#             if not urls:
#                 logger.error("没有有效的URL需要处理")
#                 return
#
#             self.stats['total_urls'] = len(urls)
#
#             # 3. 爬取每个商品
#             for idx, url in enumerate(urls, 1):
#                 try:
#                     product_data = self.crawl_single_product(url, idx, len(urls))
#
#                     if product_data:
#                         all_data.extend(product_data)
#                         self.stats['success_urls'] += 1
#                         logger.info(f"商品 {idx} 爬取成功，获取 {len(product_data)} 条数据")
#                     else:
#                         self.stats['failed_urls'] += 1
#                         logger.warning(f"商品 {idx} 未获取到数据")
#
#                 except Exception as e:
#                     self.stats['failed_urls'] += 1
#                     logger.error(f"商品 {idx} 爬取失败: {str(e)}")
#
#                 # 商品间延迟
#                 if idx < len(urls):
#                     delay = random.uniform(8, 12)
#                     logger.info(f"等待 {delay:.1f} 秒后处理下一个商品...")
#                     time.sleep(delay)
#
#             # 4. 保存结果
#             if all_data:
#                 self.stats['total_records'] = len(all_data)
#                 self.save_results(all_data, output_excel)
#             else:
#                 logger.warning("未获取到任何数据")
#
#             # 5. 显示统计信息
#             logger.info(f"\n{'=' * 60}")
#             logger.info("爬虫运行完成")
#             logger.info(f"处理商品总数: {self.stats['total_urls']}")
#             logger.info(f"成功商品数: {self.stats['success_urls']}")
#             logger.info(f"失败商品数: {self.stats['failed_urls']}")
#             logger.info(f"总数据记录: {self.stats['total_records']}")
#             logger.info(f"{'=' * 60}")
#
#         except KeyboardInterrupt:
#             logger.info("\n用户中断爬虫运行")
#         except Exception as e:
#             logger.error(f"爬虫运行失败: {str(e)}")
#         finally:
#             self.cleanup()
#
#     def cleanup(self):
#         """清理资源"""
#         try:
#             if self.driver:
#                 logger.info("正在关闭Chrome浏览器...")
#                 self.driver.quit()
#                 logger.info("Chrome浏览器已关闭")
#         except:
#             pass
#
#
# # ========== 主程序 ==========
# if __name__ == "__main__":
#
#     spider = HuiNongDealSpider()
#
#     try:
#         spider.run(
#             input_excel="惠农网全品类数据2.xlsx",
#             output_excel=f"惠农网成交数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
#             limit=5
#         )
#     except Exception as e:
#         logger.error(f"程序运行失败: {str(e)}")
#
#     logger.info("程序运行结束")