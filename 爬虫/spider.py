from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import random
import logging
import re
# 导入自定义配置
import config


# ========== 日志初始化（读取配置） ==========
def init_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, config.LOG_LEVEL))

    # 清空已有处理器
    logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)

    # 文件处理器（如果配置开启）
    if config.SAVE_LOG_TO_FILE:
        file_handler = logging.FileHandler(config.LOG_FILE_PATH, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

    return logger


logger = init_logger()


# ========== 浏览器工具类（读取配置） ==========
class BrowserManager:
    @staticmethod
    def create_driver():
        """创建Chrome驱动（读取配置文件参数）"""
        try:
            chrome_options = Options()

            # 基础配置
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument(f'user-agent={config.USER_AGENT}')

            # 无头模式（按配置）
            if config.HEADLESS_MODE:
                chrome_options.add_argument('--headless=new')

            # 禁用图片（按配置）
            if config.DISABLE_IMAGE_LOAD:
                chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})

            # 驱动初始化
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # 隐藏自动化特征
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
            })

            driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
            logger.info("Chrome浏览器初始化成功")
            return driver
        except Exception as e:
            logger.error(f"浏览器初始化失败: {str(e)}")
            raise


# ========== 数据提取工具类 ==========
class DataExtractor:
    def __init__(self, driver):
        self.driver = driver

    def close_popups(self):
        """关闭弹窗"""
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
            time.sleep(config.BASE_WAIT_TIME)
            tab.click()
            time.sleep(config.BASE_WAIT_TIME)
            return True
        except NoSuchElementException:
            logger.error("未找到在线成交标签")
            return False

    def get_total_pages(self):
        """获取商品分页总数"""
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
                    return min(total_pages, config.MAX_PAGES_PER_PRODUCT)

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
        """翻页操作"""
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
                        time.sleep(config.PAGE_TURN_WAIT_TIME)
                        return True
            return False
        except:
            return False


# ========== 主爬虫类 ==========
class HuiNongDealSpider:
    def __init__(self):
        self.driver = None
        self.extractor = None
        self.stats = {
            'category_stats': {cat: {'success': 0, 'failed': 0, 'total_records': 0} for cat in
                               config.TARGET_CATEGORIES},
            'total_time': 0
        }

    def load_category_urls(self):
        """按品类加载指定数量的URL（读取配置）"""
        if not os.path.exists(config.INPUT_EXCEL_PATH):
            logger.error(f"Excel文件不存在: {config.INPUT_EXCEL_PATH}")
            return {}

        df = pd.read_excel(config.INPUT_EXCEL_PATH)
        required_cols = ['链接', '品类']
        if not all(col in df.columns for col in required_cols):
            logger.error("Excel缺少'链接'或'品类'列")
            return {}

        # 筛选目标品类并取指定数量
        category_urls = {}
        for cat in config.TARGET_CATEGORIES:
            cat_df = df[df['品类'].str.strip() == cat].dropna(subset=['链接'])
            cat_urls = cat_df['链接'].head(config.LIMIT_PER_CATEGORY).tolist()
            category_urls[cat] = [str(url).strip() for url in cat_urls if str(url).startswith('http')]
            logger.info(f"品类[{cat}]加载{len(category_urls[cat])}条URL")

        return category_urls

    def crawl_single_product(self, url):
        """爬取单个商品成交数据"""
        product_data = []
        try:
            self.driver.get(url)
            time.sleep(random.uniform(*config.PRODUCT_DELAY_RANGE[:2]))  # 读取配置的延迟范围

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

    def run(self):
        """运行爬虫"""
        start_time = datetime.now()
        try:
            # 初始化资源
            self.driver = BrowserManager.create_driver()
            self.extractor = DataExtractor(self.driver)
            category_urls = self.load_category_urls()
            all_data = []

            # 按品类爬取
            for category, urls in category_urls.items():
                logger.info(f"\n{'=' * 50} 开始爬取品类[{category}] {'=' * 50}")
                for idx, url in enumerate(urls, 1):
                    logger.info(f"[{idx}/{len(urls)}] 爬取商品: {url}")
                    product_data = self.crawl_single_product(url)

                    if product_data:
                        all_data.extend(product_data)
                        self.stats['category_stats'][category]['success'] += 1
                        self.stats['category_stats'][category]['total_records'] += len(product_data)
                    else:
                        self.stats['category_stats'][category]['failed'] += 1

                    # 商品间延迟（按配置）
                    if idx < len(urls):
                        time.sleep(random.uniform(*config.PRODUCT_DELAY_RANGE))

            # 保存结果
            if all_data:
                pd.DataFrame(all_data).to_excel(config.OUTPUT_EXCEL_PATH, index=False)
                logger.info(f"\n数据已保存到: {config.OUTPUT_EXCEL_PATH}，总记录数: {len(all_data)}")
            else:
                logger.warning("未获取到任何成交数据")

            # 输出统计
            self.stats['total_time'] = (datetime.now() - start_time).total_seconds()
            logger.info(f"\n{'=' * 60} 爬取统计 {'=' * 60}")
            for cat, stats in self.stats['category_stats'].items():
                logger.info(
                    f"{cat}: 成功{stats['success']}个 | 失败{stats['failed']}个 | 数据{stats['total_records']}条")
            logger.info(f"总耗时: {self.stats['total_time']:.0f}秒 ({self.stats['total_time'] / 60:.1f}分钟)")

        except Exception as e:
            logger.error(f"爬虫运行异常: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("浏览器已关闭")


# ========== 主程序 ==========
if __name__ == "__main__":
    spider = HuiNongDealSpider()
    spider.run()