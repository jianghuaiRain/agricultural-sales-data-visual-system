

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import random
import logging
import os
from datetime import datetime
import re
import json

# ========== 基础配置 ==========
# 日志配置（精简输出）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 目标品类配置（按需求指定）
TARGET_CATEGORIES = [
    "蔬菜", "禽畜肉蛋", "农副加工", "水产",
    "粮油米面", "水果", "种子种苗"
]
LIMIT_PER_CATEGORY = 500  # 修改：每个品类取前500条数据
MAX_PAGES_PER_PRODUCT = 50  # 单个商品最大爬取页数
# 断点续爬配置
CHECKPOINT_FILE = "crawl_checkpoint.json"  # 断点文件路径
SAVE_INTERVAL = 1  # 每爬取1个商品就保存（即爬完就存）


# ========== 浏览器工具类（精简冗余配置） ==========
class BrowserManager:
    @staticmethod
    def create_driver():
        """创建轻量Chrome驱动"""
        try:
            chrome_options = Options()
            # 核心反爬+性能配置
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument(
                f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # 禁用图片加载
            chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})

            # 驱动自动适配
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # 隐藏自动化特征
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
            })

            driver.set_page_load_timeout(25)
            logger.info("Chrome浏览器初始化成功")
            return driver
        except Exception as e:
            logger.error(f"浏览器初始化失败: {str(e)}")
            raise


# ========== 分页与数据提取工具（合并精简） ==========
class DataExtractor:
    def __init__(self, driver):
        self.driver = driver

    def close_popups(self):
        """关闭弹窗（精简选择器）"""
        try:
            close_selectors = [
                '//i[contains(@class, "icon-guanbi")]',
                '//button[contains(@class, "close")]',
                '//div[contains(@class, "modal-close")]'
            ]
            for selector in close_selectors:
                for elem in self.driver.find_elements(By.XPATH, selector):
                    if elem.is_displayed():
                        self.driver.execute_script("arguments[0].click();", elem)
                        time.sleep(0.5)
                        return
        except:
            pass

    def switch_to_deal_tab(self):
        """切换在线成交标签"""
        try:
            tab = self.driver.find_element(By.XPATH, '//*[contains(text(), "在线成交")]')
            self.driver.execute_script("arguments[0].scrollIntoView();", tab)
            time.sleep(1)
            tab.click()
            time.sleep(3)
            return True
        except NoSuchElementException:
            logger.error("未找到在线成交标签")
            return False

    def get_total_pages(self):
        """获取商品分页总数（精简逻辑）"""
        try:
            # 统计当前页有效数据行
            valid_rows = len([row for row in self.driver.find_elements(By.XPATH, '//div[@class="line-item"]')
                              if len(row.find_elements(By.XPATH, './div')) >= 4])
            if valid_rows == 0:
                return 1

            # 提取总记录数计算页数
            for elem in self.driver.find_elements(By.XPATH, "//*[contains(text(), '共') and contains(text(), '条')]"):
                match = re.search(r'共\s*(\d+)\s*条', elem.text)
                if match:
                    total_records = int(match.group(1))
                    total_pages = (total_records + valid_rows - 1) // valid_rows
                    return min(total_pages, MAX_PAGES_PER_PRODUCT)

            # 检测下一页按钮
            has_next = any(
                btn.is_displayed() for btn in self.driver.find_elements(By.XPATH, '//*[contains(text(), "下一页")]'))
            return 10 if has_next else 1
        except:
            return 1

    def extract_page_data(self, url, page_num):
        """提取当前页成交数据"""
        data = []
        try:
            for row in self.driver.find_elements(By.XPATH, '//div[@class="line-item"]'):
                cols = row.find_elements(By.XPATH, './div')
                if len(cols) >= 4:
                    purchase_quantity = cols[2].text.strip()
                    deal_time = cols[3].text.strip()
                    if purchase_quantity or deal_time:
                        data.append({
                            '商品链接': url,
                            '采购量': purchase_quantity,
                            '成交时间': deal_time,
                            '页码': page_num,
                            '采集时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
            logger.info(f"第{page_num}页提取{len(data)}条有效数据")
        except Exception as e:
            logger.warning(f"提取第{page_num}页数据失败: {str(e)}")
        return data

    def go_to_next_page(self, current_page):
        """翻页操作（精简重试逻辑）"""
        try:
            # 尝试点击页码或下一页按钮
            selectors = [
                f'//*[text()="{current_page + 1}"]',
                '//*[contains(text(), "下一页")]'
            ]
            for selector in selectors:
                for elem in self.driver.find_elements(By.XPATH, selector):
                    if elem.is_displayed() and elem.is_enabled():
                        self.driver.execute_script("arguments[0].click();", elem)
                        time.sleep(3)
                        return True
            return False
        except:
            return False


# ========== 主爬虫类（精简冗余属性） ==========
class HuiNongDealSpider:
    def __init__(self):
        self.driver = None
        self.extractor = None
        self.stats = {
            'category_stats': {cat: {'success': 0, 'failed': 0, 'total_records': 0} for cat in TARGET_CATEGORIES},
            'total_time': 0
        }
        self.checkpoint = {
            'current_category': None,
            'current_index': 0,
            'processed_urls': []  # 已处理的URL列表
        }
        self.all_data = []  # 存储所有爬取数据
        self.output_excel = None  # 输出文件路径

    def save_checkpoint(self):
        """保存断点信息到文件"""
        try:
            with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.checkpoint, f, ensure_ascii=False, indent=2)
            logger.info(f"断点已保存: {CHECKPOINT_FILE}")
        except Exception as e:
            logger.error(f"保存断点失败: {str(e)}")

    def load_checkpoint(self):
        """加载断点信息"""
        if os.path.exists(CHECKPOINT_FILE):
            try:
                with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                    self.checkpoint = json.load(f)
                logger.info(
                    f"已加载断点: 当前品类[{self.checkpoint['current_category']}]，当前索引[{self.checkpoint['current_index']}]")
            except Exception as e:
                logger.error(f"加载断点失败，将从头开始: {str(e)}")
        else:
            logger.info("未找到断点文件，将从头开始爬取")

    def delete_checkpoint(self):
        """爬取完成后删除断点文件"""
        if os.path.exists(CHECKPOINT_FILE):
            try:
                os.remove(CHECKPOINT_FILE)
                logger.info("爬取完成，已删除断点文件")
            except Exception as e:
                logger.error(f"删除断点文件失败: {str(e)}")

    def save_data(self):
        """保存当前爬取的数据到Excel"""
        try:
            if self.all_data:
                # 如果文件已存在，先读取原有数据，避免覆盖
                if os.path.exists(self.output_excel):
                    existing_df = pd.read_excel(self.output_excel)
                    new_df = pd.DataFrame(self.all_data)
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                    # 去重（防止断点续爬时重复保存）
                    combined_df = combined_df.drop_duplicates(subset=['商品链接', '成交时间', '采购量'], keep='first')
                    combined_df.to_excel(self.output_excel, index=False)
                else:
                    pd.DataFrame(self.all_data).to_excel(self.output_excel, index=False)

                # 保存后清空内存中的数据（避免内存占用过大）
                self.all_data = []
                logger.info(f"数据已保存到: {self.output_excel}")
            else:
                logger.warning("暂无新数据可保存")
        except Exception as e:
            logger.error(f"保存数据失败: {str(e)}")

    def load_category_urls(self, excel_path):
        """按品类加载前500条URL（核心功能）"""
        if not os.path.exists(excel_path):
            logger.error(f"Excel文件不存在: {excel_path}")
            return {}

        df = pd.read_excel(excel_path)
        required_cols = ['链接', '品类']
        if not all(col in df.columns for col in required_cols):
            logger.error("Excel缺少'链接'或'品类'列")
            return {}

        # 筛选目标品类并取前500条
        category_urls = {}
        for cat in TARGET_CATEGORIES:
            cat_df = df[df['品类'].str.strip() == cat].dropna(subset=['链接'])
            cat_urls = cat_df['链接'].head(LIMIT_PER_CATEGORY).tolist()
            category_urls[cat] = [str(url).strip() for url in cat_urls if str(url).startswith('http')]
            logger.info(f"品类[{cat}]加载{len(category_urls[cat])}条URL")

        return category_urls

    def crawl_single_product(self, url):
        """爬取单个商品成交数据"""
        product_data = []
        try:
            self.driver.get(url)
            time.sleep(random.uniform(4, 6))

            self.extractor.close_popups()
            if not self.extractor.switch_to_deal_tab():
                return product_data

            total_pages = self.extractor.get_total_pages()
            for page_num in range(1, total_pages + 1):
                page_data = self.extractor.extract_page_data(url, page_num)
                product_data.extend(page_data)

                if page_num < total_pages and not self.extractor.go_to_next_page(page_num):
                    logger.warning(f"商品{url}翻页失败，停止爬取")
                    break
        except TimeoutException:
            logger.warning(f"商品{url}加载超时")
        except Exception as e:
            logger.error(f"商品{url}爬取失败: {str(e)}")
        return product_data

    def run(self, input_excel, output_excel):
        """运行爬虫（按品类批量爬取，支持断点续爬）"""
        start_time = datetime.now()
        self.output_excel = output_excel

        try:
            # 初始化资源
            self.driver = BrowserManager.create_driver()
            self.extractor = DataExtractor(self.driver)
            category_urls = self.load_category_urls(input_excel)

            # 加载断点
            self.load_checkpoint()

            # 读取已保存的数据（如果有）
            if os.path.exists(self.output_excel):
                try:
                    self.all_data = pd.read_excel(self.output_excel).to_dict('records')
                    logger.info(f"已加载原有数据，共{len(self.all_data)}条")
                except Exception as e:
                    logger.error(f"读取原有数据失败: {str(e)}")
                    self.all_data = []

            # 按品类爬取（支持断点续爬）
            categories_to_process = TARGET_CATEGORIES.copy()

            # 如果有断点，从指定品类开始
            if self.checkpoint['current_category'] and self.checkpoint['current_category'] in categories_to_process:
                # 移除断点品类之前的所有品类
                idx = categories_to_process.index(self.checkpoint['current_category'])
                categories_to_process = categories_to_process[idx:]
            else:
                # 重置断点
                self.checkpoint['current_category'] = categories_to_process[0] if categories_to_process else None
                self.checkpoint['current_index'] = 0

            for category in categories_to_process:
                logger.info(f"\n{'=' * 50} 开始爬取品类[{category}] {'=' * 50}")
                urls = category_urls.get(category, [])

                # 设置当前品类的起始索引
                start_idx = self.checkpoint['current_index'] if self.checkpoint['current_category'] == category else 0

                for idx in range(start_idx, len(urls)):
                    url = urls[idx]

                    # 跳过已处理的URL
                    if url in self.checkpoint['processed_urls']:
                        logger.info(f"[{idx + 1}/{len(urls)}] 商品{url}已处理，跳过")
                        continue

                    logger.info(f"[{idx + 1}/{len(urls)}] 爬取商品: {url}")

                    # 爬取单个商品
                    product_data = self.crawl_single_product(url)

                    # 更新统计和数据
                    if product_data:
                        self.all_data.extend(product_data)
                        self.stats['category_stats'][category]['success'] += 1
                        self.stats['category_stats'][category]['total_records'] += len(product_data)
                    else:
                        self.stats['category_stats'][category]['failed'] += 1

                    # 标记URL为已处理
                    self.checkpoint['processed_urls'].append(url)
                    # 更新当前断点
                    self.checkpoint['current_category'] = category
                    self.checkpoint['current_index'] = idx + 1  # 下次从下一个开始

                    # 保存断点
                    self.save_checkpoint()

                    # 爬完一个商品就保存数据
                    self.save_data()

                    # 商品间延迟
                    if idx < len(urls) - 1:
                        time.sleep(random.uniform(8, 12))

                # 重置当前品类索引，处理下一个品类
                self.checkpoint['current_index'] = 0

            # 最终保存数据
            self.save_data()

            # 爬取完成，删除断点文件
            self.delete_checkpoint()

            # 输出统计
            self.stats['total_time'] = (datetime.now() - start_time).total_seconds()
            logger.info(f"\n{'=' * 60} 爬取统计 {'=' * 60}")
            for cat, stats in self.stats['category_stats'].items():
                logger.info(
                    f"{cat}: 成功{stats['success']}个 | 失败{stats['failed']}个 | 数据{stats['total_records']}条")
            logger.info(f"总耗时: {self.stats['total_time']:.0f}秒 ({self.stats['total_time'] / 60:.1f}分钟)")

        except Exception as e:
            logger.error(f"爬虫运行异常: {str(e)}")
            # 异常时保存断点和已爬取数据
            self.save_checkpoint()
            self.save_data()
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("浏览器已关闭")


# ========== 主程序 ==========
if __name__ == "__main__":
    spider = HuiNongDealSpider()
    spider.run(
        input_excel="惠农网商品详情全品类精准分类.xlsx",
        output_excel=f"惠农网多品类成交数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )