#新增断点续爬
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException
)
import pandas as pd
import time
import random
import logging
import os
from datetime import datetime
import json
import re


# ========== 配置日志 ==========
def setup_logging():
    """配置日志系统"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_filename = os.path.join(log_dir, f"huinong_spider_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)


logger = setup_logging()


# ========== 浏览器管理器 ==========
class BrowserManager:
    @staticmethod
    def create_driver():
        """创建Chrome浏览器驱动"""
        try:
            chrome_options = Options()

            # 基础设置
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 性能优化
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-web-security')

            # 用户代理
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            ]
            chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')

            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-infobars')

            # 禁用图片和视频
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.managed_default_content_settings.stylesheets": 2,
                "profile.managed_default_content_settings.javascript": 1,
                "profile.default_content_setting_values.notifications": 2,
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False
            }
            chrome_options.add_experimental_option("prefs", prefs)

            # Chrome驱动路径
            driver_paths = [
                r"C:\Program Files\Google\Chrome\Application\chromedriver.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe",
                os.path.join(os.getcwd(), "chromedriver.exe")
            ]

            service = None
            for path in driver_paths:
                if os.path.exists(path):
                    try:
                        service = Service(executable_path=path)
                        logger.info(f"使用Chrome驱动: {path}")
                        break
                    except Exception as e:
                        logger.warning(f"驱动路径 {path} 不可用: {str(e)}")
                        continue

            if service is None:
                logger.warning("未找到指定的Chrome驱动，尝试自动检测")
                service = Service()

            # 创建驱动
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # 隐藏自动化特征
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                '''
            })

            driver.set_page_load_timeout(30)
            driver.set_script_timeout(30)

            logger.info("Chrome浏览器初始化成功")
            return driver

        except Exception as e:
            logger.error(f"Chrome浏览器初始化失败: {str(e)}")
            # 尝试更简化的方式
            try:
                logger.info("尝试使用简化方式初始化Chrome...")
                chrome_options = Options()
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--start-maximized')
                chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})

                service = Service(executable_path=r"C:\Program Files\Google\Chrome\Application\chromedriver.exe")
                driver = webdriver.Chrome(service=service, options=chrome_options)

                driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
                })

                logger.info("Chrome浏览器初始化成功（简化模式）")
                return driver
            except Exception as e2:
                logger.error(f"简化方式初始化也失败: {str(e2)}")
                raise


# ========== 分页检测器 ==========
class PaginationDetector:
    """专门用于检测分页的类"""

    def __init__(self, driver):
        self.driver = driver

    def detect_all_pagination_elements(self):
        """检测所有可能的分页元素"""
        logger.info("开始检测分页元素...")

        # 存储所有找到的元素信息
        found_elements = []

        # 1. 首先等待可能的动态加载
        time.sleep(3)

        # 2. 滚动到页面底部（分页通常在底部）
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # 3. 尝试多种分页选择器
        pagination_patterns = [
            # 类名包含 pagination
            ("CSS", "[class*='pagination']"),
            ("CSS", "[class*='Pagination']"),
            ("CSS", ".pagination"),
            ("CSS", ".Pagination"),

            # 类名包含 page
            ("CSS", "[class*='page']"),
            ("CSS", "[class*='Page']"),

            # 包含页码的容器
            ("XPATH", "//div[contains(@class, 'list-pagination')]"),
            ("XPATH", "//div[contains(@class, 'eye-pagination')]"),
            ("XPATH", "//div[contains(@class, 'pagination-container')]"),
            ("XPATH", "//div[contains(@class, 'pagination-wrapper')]"),

            # ul/li 分页
            ("XPATH", "//ul[contains(@class, 'pagination')]"),
            ("XPATH", "//ul[@class='pagination']"),
            ("XPATH", "//div/ul[contains(@class, 'pagination')]"),

            # 按钮组
            ("XPATH", "//div[@class='btn-group']"),
            ("XPATH", "//div[contains(@class, 'pager')]"),

            # 包含"页"字的元素
            ("XPATH", "//*[contains(text(), '页')]"),
            ("XPATH", "//*[contains(text(), 'Page')]"),
            ("XPATH", "//*[contains(text(), 'page')]"),

            # 数字按钮
            ("XPATH", "//button[text()='1']"),
            ("XPATH", "//button[text()='2']"),
            ("XPATH", "//li[text()='1']"),
            ("XPATH", "//li[text()='2']"),

            # 下一页按钮
            ("XPATH", "//button[contains(text(), '下一页')]"),
            ("XPATH", "//button[contains(text(), 'Next')]"),
            ("XPATH", "//a[contains(text(), '下一页')]"),
            ("XPATH", "//li[contains(text(), '下一页')]"),
        ]

        for by, selector in pagination_patterns:
            try:
                if by == "CSS":
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                else:  # XPATH
                    elements = self.driver.find_elements(By.XPATH, selector)

                for idx, element in enumerate(elements):
                    try:
                        if element.is_displayed():
                            text = element.text.strip()
                            html = element.get_attribute('outerHTML')[:200]  # 取前200个字符
                            found_elements.append({
                                'selector': f"{by}: {selector}",
                                'index': idx,
                                'text': text,
                                'html': html,
                                'element': element
                            })
                            logger.info(f"找到分页元素: {by}:{selector}, 文本: '{text}'")
                    except:
                        continue

            except Exception as e:
                continue

        logger.info(f"总共找到 {len(found_elements)} 个分页相关元素")

        # 打印详细信息
        for elem in found_elements:
            logger.debug(f"元素: {elem['selector']}, 文本: '{elem['text']}'")

        return found_elements

    def count_valid_data_rows(self):
        """统计有效的交易数据行数（去除表头、空行等）"""
        try:
            # 查找所有可能的交易数据行
            rows = self.driver.find_elements(By.XPATH, '//div[@class="line-item"]')

            if not rows:
                logger.warning("未找到line-item元素")
                return 0

            valid_count = 0
            logger.info(f"找到 {len(rows)} 个line-item元素，开始筛选有效行...")

            for idx, row in enumerate(rows):
                try:
                    # 检查行是否可见
                    if not row.is_displayed():
                        continue

                    # 获取行内所有列
                    cols = row.find_elements(By.XPATH, './div')

                    # 检查是否有足够的列（至少4列）
                    if len(cols) < 4:
                        continue

                    # 检查关键列是否有内容
                    # 第3列：采购量，第4列：成交时间
                    purchase_quantity = cols[2].text.strip() if cols[2].text else ""
                    deal_time = cols[3].text.strip() if cols[3].text else ""

                    # 如果两列都有内容，或者至少有一列有内容，认为是有效数据行
                    if purchase_quantity or deal_time:
                        valid_count += 1
                        if valid_count <= 3:  # 只打印前3行的信息用于调试
                            logger.debug(f"有效行 {valid_count}: 采购量='{purchase_quantity}', 成交时间='{deal_time}'")

                except Exception as e:
                    logger.debug(f"检查行 {idx + 1} 失败: {str(e)}")
                    continue

            logger.info(f"统计到有效数据行数: {valid_count} 行")

            # 如果有效行数为0，但总行数>0，可能是页面结构不同
            if valid_count == 0 and len(rows) > 0:
                logger.warning("未找到有效数据行，尝试备用方法...")
                # 备用方法：检查是否有包含特定内容的行
                for idx, row in enumerate(rows):
                    try:
                        text = row.text.strip()
                        # 如果行文本包含数字（可能是成交数据）
                        if re.search(r'\d', text) and len(text) > 10:
                            valid_count += 1
                    except:
                        continue
                logger.info(f"备用方法统计到: {valid_count} 行")

            return valid_count

        except Exception as e:
            logger.error(f"统计有效数据行数失败: {str(e)}")
            return 0

    def extract_pagination_info(self):
        """专门提取分页信息，避免混淆条数和页数"""
        info = {
            'total_records': 0,
            'rows_per_page': 0,
            'total_pages': 1,
            'current_page': 1,
            'page_size_detected': False,
            'has_next_page': False
        }

        try:
            # 获取当前页有效的交易数据行数（关键修复）
            info['rows_per_page'] = self.count_valid_data_rows()
            logger.info(f"当前页有效数据行数: {info['rows_per_page']} 行")

            if info['rows_per_page'] == 0:
                logger.warning("当前页没有有效数据，无法计算分页")
                return info

            # 查找所有可能包含分页信息的元素
            possible_elements = self.driver.find_elements(By.XPATH,
                                                          "//*[contains(text(), '条') or contains(text(), '页') or contains(text(), 'record') or contains(text(), 'page')]"
                                                          )

            for elem in possible_elements:
                text = elem.text.strip()
                if not text:
                    continue

                logger.debug(f"检查文本: '{text}'")

                # 1. 匹配"共XX条"（总记录数）- 关键修复点
                match = re.search(r'共\s*(\d+)\s*条', text)
                if match:
                    info['total_records'] = int(match.group(1))
                    logger.info(f"找到总记录数: {info['total_records']} 条")
                    info['page_size_detected'] = True

                # 2. 匹配"X/Y页"或"X of Y"（当前页/总页数）
                match = re.search(r'(\d+)\s*[/|]\s*(\d+)\s*[页|$]', text) or re.search(r'page\s*(\d+)\s*of\s*(\d+)',
                                                                                       text, re.IGNORECASE)
                if match:
                    info['current_page'] = int(match.group(1))
                    info['total_pages'] = int(match.group(2))
                    logger.info(f"找到页码信息: 第{info['current_page']}页/共{info['total_pages']}页")
                    info['page_size_detected'] = True

                # 3. 匹配"跳转到 X 页"中的最大页码
                match = re.search(r'跳转到\s*(\d+)\s*页', text)
                if match:
                    possible_max = int(match.group(1))
                    if possible_max > info['total_pages']:
                        info['total_pages'] = possible_max
                        logger.info(f"从跳转框找到最大页码: {info['total_pages']}")
                        info['page_size_detected'] = True

            # 检查是否有下一页按钮
            try:
                next_buttons = self.driver.find_elements(By.XPATH,
                                                         "//button[contains(text(), '下一页')] | "
                                                         "//button[contains(text(), 'Next')] | "
                                                         "//a[contains(text(), '下一页')]"
                                                         )

                for btn in next_buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        info['has_next_page'] = True
                        logger.info("检测到下一页按钮")
                        break
            except:
                pass

            # 如果找到了总记录数和每页行数，计算总页数（这是最可靠的方法）
            if info['total_records'] > 0 and info['rows_per_page'] > 0:
                calculated_pages = (info['total_records'] + info['rows_per_page'] - 1) // info['rows_per_page']
                logger.info(
                    f"计算总页数: {calculated_pages} (总{info['total_records']}条，每页{info['rows_per_page']}行)")

                # 优先使用计算出的页数，因为它更准确
                info['total_pages'] = calculated_pages
                logger.info(f"使用计算出的总页数: {info['total_pages']}")

                # 验证计算出的页数是否合理
                if info['total_pages'] > 200:
                    logger.warning(f"计算出的页数 {info['total_pages']} 过大，尝试验证")
                    # 如果每页行数过少（小于5），可能是统计错误
                    if info['rows_per_page'] < 5:
                        logger.warning(f"每页只有 {info['rows_per_page']} 行，可能统计有误")
                        # 尝试使用常见的每页行数（10, 20, 50）
                        common_page_sizes = [10, 20, 50]
                        for page_size in common_page_sizes:
                            calculated_with_common = (info['total_records'] + page_size - 1) // page_size
                            logger.info(f"假设每页{page_size}行，计算页数: {calculated_with_common}")

            # 如果没有找到总记录数，但有下一页按钮，假设至少有多页
            elif info['has_next_page'] and not info['page_size_detected']:
                logger.info("未找到总记录数但有下一页按钮，假设有多页")
                info['total_pages'] = 10  # 保守估计10页

        except Exception as e:
            logger.error(f"提取分页信息失败: {str(e)}")

        return info

    def get_total_pages(self):
        """获取总页数 - 修复版，正确统计每页行数，并修改为50页限制"""
        logger.info("开始获取总页数...")

        # 使用专门的提取方法
        pagination_info = self.extract_pagination_info()

        total_pages = pagination_info['total_pages']

        # 如果没有获取到有效的页数信息，尝试其他方法
        if total_pages <= 0:
            logger.info("未能获取到有效页数信息，尝试其他方法...")

            # 方法1: 从分页元素中获取纯数字页码
            pagination_elements = self.detect_all_pagination_elements()
            page_numbers = set()

            for elem in pagination_elements:
                text = elem['text']

                # 寻找纯数字的页码按钮（不是"共XX条"中的数字）
                if re.match(r'^\d+$', text):  # 纯数字
                    try:
                        page_num = int(text)
                        if 1 <= page_num <= 100:  # 合理的页码范围
                            page_numbers.add(page_num)
                            logger.info(f"从分页按钮找到页码: {page_num}")
                    except:
                        pass

            # 如果找到了页码数字
            if page_numbers:
                max_page = max(page_numbers)
                logger.info(f"从分页元素中检测到最大页码: {max_page}")
                total_pages = max_page
            else:
                # 检查是否有下一页按钮
                if pagination_info['has_next_page']:
                    logger.info("检测到下一页按钮，假设有多页")
                    # 保守估计，先设为10页
                    total_pages = 10
                else:
                    logger.info("未检测到下一页按钮，默认为1页")
                    total_pages = 1

        # 最终验证和限制
        if total_pages <= 0:
            logger.info("页数无效，使用默认值1")
            total_pages = 1

        # 限制最大页数，防止误识别导致无限翻页
        MAX_PAGES = 100
        if total_pages > MAX_PAGES:
            logger.warning(f"页数 {total_pages} 超过限制，限制为 {MAX_PAGES}")
            total_pages = MAX_PAGES

        # 验证合理性：如果有总记录数，检查每页行数是否合理
        if pagination_info['total_records'] > 0 and total_pages > 0:
            calculated_rows_per_page = pagination_info['total_records'] // total_pages
            logger.info(f"根据总记录数和页数计算每页应有: {calculated_rows_per_page} 行")

            # 如果计算出的每页行数异常（过小或过大），可能需要调整
            if calculated_rows_per_page < 5:
                logger.warning(f"计算出的每页行数({calculated_rows_per_page})过小，可能页数过多")
                # 重新计算合理的页数（假设每页10-20行）
                reasonable_rows_per_page = 15  # 假设每页15行
                reasonable_pages = (pagination_info[
                                        'total_records'] + reasonable_rows_per_page - 1) // reasonable_rows_per_page
                logger.info(f"假设每页{reasonable_rows_per_page}行，重新计算页数: {reasonable_pages}")
                total_pages = min(reasonable_pages, MAX_PAGES)
            elif calculated_rows_per_page > 50:
                logger.warning(f"计算出的每页行数({calculated_rows_per_page})过大，可能页数过少")

        # 修改为50页限制：如果超过50页，只返回50页（爬取全部50页）
        MAX_ALLOWED_PAGES = 50
        CRAWL_LIMIT_PAGES = 50  # 修改为50页，爬取全部50页数据

        original_pages = total_pages  # 保存原始页数用于日志

        if total_pages > MAX_ALLOWED_PAGES:
            total_pages = CRAWL_LIMIT_PAGES
            logger.warning(f"页数 {original_pages} 超过阈值 {MAX_ALLOWED_PAGES}，爬虫将只处理前 {CRAWL_LIMIT_PAGES} 页")
        else:
            logger.info(f"页数 {total_pages} 未超过阈值，将爬取全部页面")

        logger.info(f"最终确定总页数: {total_pages}")
        return total_pages


# ========== 数据提取器 ==========
class DataExtractor:
    def __init__(self, driver):
        self.driver = driver
        self.pagination_detector = PaginationDetector(driver)

    def close_popups(self):
        """关闭弹窗"""
        try:
            selectors = [
                '//i[contains(@class, "icon-guanbi")]',
                '//div[contains(@class, "modal-close")]',
                '//button[contains(@class, "close")]',
                '//span[contains(@class, "close")]',
                '//div[contains(@class, "close-btn")]'
            ]

            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            try:
                                element.click()
                                time.sleep(0.5)
                            except:
                                self.driver.execute_script("arguments[0].click();", element)
                            logger.info("关闭弹窗成功")
                            break
                except:
                    continue
        except Exception as e:
            logger.warning(f"关闭弹窗失败: {str(e)}")

    def switch_to_deal_tab(self):
        """切换到在线成交标签"""
        logger.info("正在切换到在线成交标签...")

        try:
            time.sleep(2)

            tab_selectors = [
                '//*[contains(text(), "在线成交")]',
                '//div[contains(text(), "在线成交")]',
                '//span[contains(text(), "在线成交")]',
                '//button[contains(text(), "在线成交")]',
                '//a[contains(text(), "在线成交")]'
            ]

            for selector in tab_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            self.driver.execute_script("arguments[0].scrollIntoView();", element)
                            time.sleep(1)

                            try:
                                element.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", element)

                            logger.info("成功切换到在线成交标签")
                            time.sleep(3)
                            return True
                except:
                    continue

            logger.error("未找到在线成交标签")
            return False

        except Exception as e:
            logger.error(f"切换标签失败: {str(e)}")
            return False

    def extract_page_data(self, url, page_num):
        """提取当前页数据"""
        data = []

        try:
            time.sleep(2)

            # 使用更精确的方法查找数据行
            rows = self.driver.find_elements(By.XPATH, '//div[@class="line-item"]')

            if not rows:
                logger.warning(f"第{page_num}页未找到数据行")
                return data

            logger.info(f"第{page_num}页找到 {len(rows)} 个line-item元素")

            valid_count = 0
            for idx, row in enumerate(rows):
                try:
                    cols = row.find_elements(By.XPATH, './div')

                    if len(cols) >= 4:
                        purchase_quantity = cols[2].text.strip() if cols[2].text else ""
                        deal_time = cols[3].text.strip() if cols[3].text else ""

                        # 只添加有数据的行
                        if purchase_quantity or deal_time:
                            data.append({
                                '商品链接': url,
                                '采购量': purchase_quantity,
                                '成交时间': deal_time,
                                '页码': page_num,
                                '行号': idx + 1,
                                '采集时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            valid_count += 1
                except Exception as e:
                    logger.warning(f"提取行数据失败: {str(e)}")
                    continue

            logger.info(f"第{page_num}页提取到 {valid_count} 条有效数据 (共{len(rows)}个元素)")

        except Exception as e:
            logger.error(f"提取第{page_num}页数据失败: {str(e)}")

        return data

    def go_to_next_page(self, current_page):
        """翻到下一页"""
        next_page_num = current_page + 1
        logger.info(f"尝试翻到第 {next_page_num} 页")

        try:
            # 首先尝试直接点击具体页码
            next_selectors = [
                f'//button[text()="{next_page_num}"]',
                f'//li[text()="{next_page_num}"]',
                f'//a[text()="{next_page_num}"]',
                f'//button[@data-page="{next_page_num}"]',
                f'//li[@data-page="{next_page_num}"]',
            ]

            # 然后尝试下一页按钮
            next_selectors.extend([
                '//button[contains(text(), "下一页")]',
                '//button[contains(text(), "Next")]',
                '//li[contains(text(), "下一页")]',
                '//button[contains(@class, "next")]',
                '//li[contains(@class, "next")]',
                '//a[contains(@class, "next")]'
            ])

            for selector in next_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # 保存当前数据用于验证
                            original_count = self.pagination_detector.count_valid_data_rows()

                            # 滚动并点击
                            self.driver.execute_script("arguments[0].scrollIntoView();", element)
                            time.sleep(1)

                            self.driver.execute_script("arguments[0].click();", element)

                            # 等待新数据加载
                            time.sleep(3)

                            # 验证是否翻页成功
                            new_count = self.pagination_detector.count_valid_data_rows()
                            if new_count > 0:
                                logger.info(f"成功翻到第 {next_page_num} 页，新页有 {new_count} 行有效数据")
                                return True
                            else:
                                logger.warning(f"翻页后未找到有效数据，可能不是有效翻页")
                except:
                    continue

            logger.error(f"翻到第 {next_page_num} 页失败")
            return False

        except Exception as e:
            logger.error(f"翻页失败: {str(e)}")
            return False


# ========== 主爬虫类 ==========
class HuiNongDealSpider:
    def __init__(self):
        self.driver = None
        self.data_extractor = None
        self.stats = {
            'total_urls': 0,
            'success_urls': 0,
            'failed_urls': 0,
            'skipped_urls': 0,  # 新增：跳过的URL数（已爬取过的）
            'total_records': 0,
            'total_pages': 0,
            'actual_pages_crawled': 0,
            'rows_per_page': 0,
            'pages_limited': 0,  # 记录被限制页数的商品数量
            'start_time': None,
            'end_time': None,
            'resume_mode': False  # 新增：是否为续爬模式
        }
        self.processed_urls = set()  # 记录已处理过的URL
        self.existing_data = pd.DataFrame()  # 已存在的数据

    def init_browser(self):
        """初始化浏览器"""
        logger.info("=" * 60)
        logger.info("惠农网成交数据爬虫启动 - 断点续爬版")
        logger.info("说明：")
        logger.info("1. 将爬取Excel文件中所有商品的成交数据")
        logger.info("2. 当商品页数超过50页时，只爬取前50页数据")
        logger.info("3. 支持断点续爬，自动跳过已爬取的商品")
        logger.info("4. 每个商品间有随机延迟，防止被封IP")
        logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        try:
            self.driver = BrowserManager.create_driver()
            self.data_extractor = DataExtractor(self.driver)
            logger.info("Chrome浏览器初始化完成")
        except Exception as e:
            logger.error(f"Chrome浏览器初始化失败: {str(e)}")
            raise

    def load_existing_data(self, output_excel):
        """加载已存在的数据，用于断点续爬"""
        try:
            if os.path.exists(output_excel):
                self.existing_data = pd.read_excel(output_excel)
                # 提取已处理过的URL
                if '商品链接' in self.existing_data.columns:
                    self.processed_urls = set(self.existing_data['商品链接'].unique())
                    logger.info(f"发现已有数据文件，包含 {len(self.processed_urls)} 个已处理的商品链接")
                    logger.info(f"已有数据记录数: {len(self.existing_data)}")
                    self.stats['resume_mode'] = True
                    return True
            return False
        except Exception as e:
            logger.error(f"加载已有数据失败: {str(e)}")
            return False

    def load_urls(self, excel_path):
        """从Excel加载URL - 移除了limit参数"""
        try:
            if not os.path.exists(excel_path):
                logger.error(f"Excel文件不存在: {excel_path}")
                return []

            df = pd.read_excel(excel_path)

            if '链接' not in df.columns:
                logger.error("Excel中缺少'链接'列")
                return []

            urls = []
            for url in df['链接']:
                if pd.isna(url):
                    continue

                url_str = str(url).strip()
                if url_str and url_str.startswith('http'):
                    urls.append(url_str)

            logger.info(f"从Excel加载 {len(urls)} 个URL (全部商品)")

            # 如果处于续爬模式，过滤掉已处理的URL
            if self.stats['resume_mode']:
                new_urls = [url for url in urls if url not in self.processed_urls]
                skipped_count = len(urls) - len(new_urls)
                if skipped_count > 0:
                    logger.info(f"续爬模式：跳过 {skipped_count} 个已处理的商品链接")
                    self.stats['skipped_urls'] = skipped_count
                urls = new_urls

            logger.info(f"实际需要爬取的URL数量: {len(urls)}")
            return urls

        except Exception as e:
            logger.error(f"加载URL失败: {str(e)}")
            return []

    def crawl_single_product(self, url, product_idx, total_products):
        """爬取单个商品 - 修复分页检测问题"""
        logger.info(f"\n{'=' * 60}")
        logger.info(f"【{product_idx}/{total_products}】开始爬取商品")
        logger.info(f"URL: {url}")
        logger.info(f"{'=' * 60}")

        product_data = []
        actual_pages_crawled = 0
        is_pages_limited = False  # 记录是否被限制页数

        try:
            # 1. 访问页面
            logger.info("访问商品页面...")
            self.driver.get(url)
            time.sleep(random.uniform(5, 8))

            # 2. 关闭弹窗
            self.data_extractor.close_popups()

            # 3. 切换到在线成交标签
            if not self.data_extractor.switch_to_deal_tab():
                logger.error("无法切换到在线成交标签，跳过此商品")
                return product_data

            # 4. 再次关闭弹窗
            self.data_extractor.close_popups()
            time.sleep(2)

            # 5. 获取总页数（使用修复的分页检测，已包含50页限制）
            total_pages = self.data_extractor.pagination_detector.get_total_pages()
            logger.info(f"检测到总页数: {total_pages}")

            # 获取当前页信息用于验证
            current_rows = self.data_extractor.pagination_detector.count_valid_data_rows()
            logger.info(f"第一页有 {current_rows} 行有效数据")

            # 记录每页行数统计
            if current_rows > 0:
                self.stats['rows_per_page'] = current_rows

            # 如果第一页没有数据，直接返回
            if current_rows == 0:
                logger.warning("第一页没有有效数据，跳过此商品")
                return product_data

            # 6. 逐页爬取
            for page_num in range(1, total_pages + 1):
                logger.info(f"正在爬取第 {page_num}/{total_pages} 页")

                # 提取当前页数据
                page_data = self.data_extractor.extract_page_data(url, page_num)
                product_data.extend(page_data)
                actual_pages_crawled += 1

                logger.info(f"第{page_num}页完成，累计 {len(product_data)} 条数据")

                # 如果不是最后一页，尝试翻页
                if page_num < total_pages:
                    # 尝试翻页，最多重试3次
                    success = False
                    for retry in range(3):
                        logger.info(f"尝试翻页到第 {page_num + 1} 页 (重试 {retry + 1}/3)")

                        if self.data_extractor.go_to_next_page(page_num):
                            success = True
                            break
                        else:
                            logger.warning(f"翻页失败，等待后重试...")
                            time.sleep(2)

                    if not success:
                        logger.error(f"翻页重试次数用尽，停止翻页")
                        break
                else:
                    logger.info(f"已完成所有 {total_pages} 页的爬取")

            # 检查是否被限制页数
            if total_pages == 50:  # 如果正好是50页，可能是被限制了
                # 尝试获取总记录数来判断是否真的被限制了
                try:
                    # 尝试获取总记录数
                    total_text_elements = self.driver.find_elements(By.XPATH,
                                                                    "//*[contains(text(), '共') and contains(text(), '条')]")
                    for elem in total_text_elements:
                        text = elem.text.strip()
                        match = re.search(r'共\s*(\d+)\s*条', text)
                        if match:
                            total_records = int(match.group(1))
                            # 计算实际应有页数
                            actual_pages = (total_records + current_rows - 1) // current_rows
                            if actual_pages > 50:
                                is_pages_limited = True
                                logger.info(f"商品实际应有 {actual_pages} 页，已限制为50页")
                            break
                except:
                    pass

            logger.info(f"商品爬取完成，共获取 {len(product_data)} 条数据，实际爬取 {actual_pages_crawled} 页")

            # 记录实际爬取的页数
            self.stats['actual_pages_crawled'] += actual_pages_crawled

            # 记录被限制页数的商品
            if is_pages_limited:
                self.stats['pages_limited'] += 1

            return product_data

        except Exception as e:
            logger.error(f"爬取商品失败: {str(e)}")
            return product_data

    def save_results(self, data, output_path, append=False):
        """保存结果 - 支持追加模式"""
        try:
            if not data:
                logger.warning("没有数据需要保存")
                return

            # 创建新数据的DataFrame
            new_df = pd.DataFrame(data)

            if append and not self.existing_data.empty:
                # 追加模式：合并新旧数据
                combined_df = pd.concat([self.existing_data, new_df], ignore_index=True)
                # 去重（基于商品链接和成交时间）
                before_count = len(combined_df)
                combined_df = combined_df.drop_duplicates(subset=['商品链接', '成交时间', '采购量'], keep='first')
                after_count = len(combined_df)

                if before_count > after_count:
                    logger.info(f"去重后减少 {before_count - after_count} 条重复记录")

                final_df = combined_df
            else:
                final_df = new_df

            # 保存到Excel
            final_df.to_excel(output_path, index=False)

            logger.info(f"数据已保存到: {output_path}")
            logger.info(f"总记录数: {len(final_df)}")
            logger.info(f"本次新增记录: {len(new_df)}")

            # 统计信息
            if '页码' in final_df.columns:
                unique_pages = final_df['页码'].unique()
                logger.info(f"实际爬取的页码范围: {sorted(unique_pages)}")

                # 检查是否有异常页码
                max_page = max(unique_pages) if len(unique_pages) > 0 else 0
                if max_page > 100:
                    logger.warning(f"发现异常页码: {max_page}，可能分页检测有误")

        except Exception as e:
            logger.error(f"保存结果失败: {str(e)}")

    def run(self, input_excel=None, output_excel=None, resume=True):
        """运行爬虫 - 全量爬取所有商品，支持断点续爬"""

        if input_excel is None:
            input_excel = "惠农网全品类数据2.xlsx"
        if output_excel is None:
            output_excel = f"惠农网成交数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        all_data = []

        # 记录开始时间
        self.stats['start_time'] = datetime.now()

        try:
            # 1. 初始化浏览器
            self.init_browser()

            # 2. 如果是续爬模式，加载已有数据
            if resume:
                self.load_existing_data(output_excel)
                if self.stats['resume_mode']:
                    logger.info("✓ 已启用断点续爬模式")
                    logger.info(f"✓ 发现 {len(self.processed_urls)} 个已处理的商品")
                    logger.info(f"✓ 已有 {len(self.existing_data)} 条数据记录")

            # 3. 加载URL（全部商品）
            urls = self.load_urls(input_excel)
            if not urls:
                if self.stats['resume_mode'] and self.stats['skipped_urls'] > 0:
                    logger.info("所有商品都已处理完成，无需继续爬取")
                    logger.info("将合并并保存现有数据...")
                    if not self.existing_data.empty:
                        self.save_results([], output_excel, append=False)
                    return
                else:
                    logger.error("没有有效的URL需要处理")
                    return

            self.stats['total_urls'] = len(urls)

            if self.stats['resume_mode']:
                logger.info(f"开始续爬，剩余 {len(urls)} 个商品待处理")
            else:
                logger.info(f"开始爬取 {len(urls)} 个商品，请耐心等待...")

            # 4. 爬取每个商品
            for idx, url in enumerate(urls, 1):
                try:
                    # 显示进度信息
                    progress = f"{idx}/{len(urls)}"
                    percentage = (idx / len(urls)) * 100

                    if self.stats['resume_mode']:
                        total_with_skipped = idx + self.stats['skipped_urls']
                        total_all = len(urls) + self.stats['skipped_urls']
                        overall_percentage = (total_with_skipped / total_all) * 100
                        logger.info(
                            f"进度: {progress} ({percentage:.1f}%) | 总进度: {total_with_skipped}/{total_all} ({overall_percentage:.1f}%)")
                    else:
                        logger.info(f"进度: {progress} ({percentage:.1f}%)")

                    product_data = self.crawl_single_product(url, idx, len(urls))

                    if product_data:
                        all_data.extend(product_data)
                        self.stats['success_urls'] += 1
                        logger.info(f"商品 {idx} 爬取成功，获取 {len(product_data)} 条数据")
                    else:
                        self.stats['failed_urls'] += 1
                        logger.warning(f"商品 {idx} 未获取到数据")

                except Exception as e:
                    self.stats['failed_urls'] += 1
                    logger.error(f"商品 {idx} 爬取失败: {str(e)}")

                # 商品间延迟（防止请求过快被封）
                if idx < len(urls):
                    # 动态调整延迟时间，根据进度逐渐增加稳定性
                    if idx % 10 == 0:  # 每10个商品增加一次延迟
                        delay = random.uniform(15, 20)
                        logger.info(f"已处理 {idx} 个商品，增加延迟防止被封...")
                    else:
                        delay = random.uniform(10, 15)

                    logger.info(f"等待 {delay:.1f} 秒后处理下一个商品...")
                    time.sleep(delay)

                    # 每20个商品保存一次临时结果（续爬模式下合并数据）
                    if idx % 20 == 0 and (all_data or not self.existing_data.empty):
                        temp_output = f"惠农网成交数据_临时保存_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

                        # 如果是续爬模式，合并新旧数据
                        if self.stats['resume_mode'] and not self.existing_data.empty:
                            temp_df = pd.concat([self.existing_data, pd.DataFrame(all_data)], ignore_index=True)
                        else:
                            temp_df = pd.DataFrame(all_data)

                        temp_df.to_excel(temp_output, index=False)
                        logger.info(f"已保存临时结果到: {temp_output}，已爬取 {len(temp_df)} 条数据")

            # 5. 保存最终结果
            if all_data or not self.existing_data.empty:
                self.stats['total_records'] = len(all_data) + (
                    0 if self.existing_data.empty else len(self.existing_data))
                # 使用追加模式保存结果
                self.save_results(all_data, output_excel, append=self.stats['resume_mode'])
            else:
                logger.warning("未获取到任何数据")

            # 6. 显示统计信息
            self.stats['end_time'] = datetime.now()
            total_time = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

            logger.info(f"\n{'=' * 60}")
            logger.info("爬虫运行完成！")
            logger.info("=" * 60)
            logger.info("统计信息:")
            logger.info(f"开始时间: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"结束时间: {self.stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"总耗时: {total_time:.0f} 秒 ({total_time / 60:.1f} 分钟)")

            if self.stats['resume_mode']:
                logger.info(f"运行模式: 断点续爬")
                logger.info(f"已跳过商品: {self.stats['skipped_urls']}")

            logger.info(f"待处理商品总数: {self.stats['total_urls']}")
            logger.info(f"成功商品数: {self.stats['success_urls']}")
            logger.info(f"失败商品数: {self.stats['failed_urls']}")

            if self.stats['total_urls'] > 0:
                success_rate = (self.stats['success_urls'] / self.stats['total_urls'] * 100)
                logger.info(f"本次成功率: {success_rate:.1f}%")

            logger.info(f"本次新增记录: {len(all_data)}")
            logger.info(f"总数据记录: {self.stats['total_records']}")

            if self.stats['success_urls'] > 0:
                logger.info(
                    f"平均每商品爬取页数: {self.stats['actual_pages_crawled'] / self.stats['success_urls']:.1f}")
                if self.stats['rows_per_page'] > 0:
                    logger.info(f"平均每页行数: {self.stats['rows_per_page']}")
                logger.info(f"平均每商品数据量: {len(all_data) / self.stats['success_urls']:.1f} 条")

                if self.stats['pages_limited'] > 0:
                    logger.info(f"被限制页数的商品数: {self.stats['pages_limited']} (超过50页只爬前50页)")

            logger.info(f"输出文件: {output_excel}")
            logger.info(f"{'=' * 60}")

        except KeyboardInterrupt:
            logger.info("\n用户中断爬虫运行")
            # 保存已爬取的数据（续爬模式下合并数据）
            if all_data or not self.existing_data.empty:
                interrupt_output = f"惠农网成交数据_中断保存_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                # 如果是续爬模式，合并新旧数据
                if self.stats['resume_mode'] and not self.existing_data.empty:
                    combined_data = pd.concat([self.existing_data, pd.DataFrame(all_data)], ignore_index=True)
                else:
                    combined_data = pd.DataFrame(all_data)

                combined_data.to_excel(interrupt_output, index=False)
                logger.info(f"已保存中断前的数据到: {interrupt_output}")
                logger.info(f"建议下次使用此文件作为续爬起点")
        except Exception as e:
            logger.error(f"爬虫运行失败: {str(e)}")
            # 保存已爬取的数据
            if all_data or not self.existing_data.empty:
                error_output = f"惠农网成交数据_错误保存_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                # 如果是续爬模式，合并新旧数据
                if self.stats['resume_mode'] and not self.existing_data.empty:
                    combined_data = pd.concat([self.existing_data, pd.DataFrame(all_data)], ignore_index=True)
                else:
                    combined_data = pd.DataFrame(all_data)

                combined_data.to_excel(error_output, index=False)
                logger.info(f"已保存错误前的数据到: {error_output}")
        finally:
            self.cleanup()

    def cleanup(self):
        """清理资源"""
        try:
            if self.driver:
                logger.info("正在关闭Chrome浏览器...")
                self.driver.quit()
                logger.info("Chrome浏览器已关闭")
        except:
            pass


# ========== 主程序 ==========
if __name__ == "__main__":

    spider = HuiNongDealSpider()

    try:
        # 运行爬虫，爬取所有商品
        # 参数说明：
        # input_excel: 输入Excel文件路径
        # output_excel: 输出Excel文件路径（如果文件已存在，会自动续爬）
        # resume: 是否启用断点续爬（默认True）
        spider.run(
            input_excel="惠农网全品类数据.xlsx",
            output_excel=f"惠农网成交数据_中断保存_20260116_234306.xlsx",
            resume=True  # 启用断点续爬
        )
    except Exception as e:
        logger.error(f"程序运行失败: {str(e)}")

    logger.info("程序运行结束")