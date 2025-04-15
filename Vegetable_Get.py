from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (WebDriverException,
                                        NoSuchElementException,
                                        TimeoutException,
                                        ElementNotInteractableException)
import pandas as pd
import time
import traceback
import random


def init_driver():
    """初始化带有详细配置的WebDriver"""
    try:
        print("🚀 正在初始化Chrome驱动...")
        options = webdriver.ChromeOptions()

        # 调试时可注释掉headless模式
        # options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')

        # 增强反爬设置
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # 设置随机用户代理
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_16_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
        ]
        options.add_argument(f'user-agent={random.choice(user_agents)}')

        # 初始化Service
        service = Service(executable_path=r'C:\Program Files\Google\Chrome\Application\chromedriver.exe')

        driver = webdriver.Chrome(service=service, options=options)

        # 修改webdriver属性防止被检测
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })

        # 设置随机等待时间（5-10秒）
        driver.implicitly_wait(random.randint(5, 10))
        print("✅ Chrome驱动初始化成功")
        return driver
    except Exception as e:
        print(f"❌ 驱动初始化失败: {str(e)}")
        print("⚠️ 请检查: 1. Chrome浏览器是否安装 2. ChromeDriver版本是否匹配")
        print(f"🔍 错误详情:\n{traceback.format_exc()}")
        return None


def human_like_delay(min_sec=1, max_sec=3):
    """人类行为模拟延迟"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def scroll_to_element(driver, element):
    """平滑滚动到元素位置"""
    try:
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        human_like_delay(0.5, 1.5)
    except Exception as e:
        print(f"滚动出错: {str(e)}")


def setup_ajax_monitor(driver):
    """增强版AJAX请求监控（支持翻页请求）"""
    script = """
    window.__ajaxCompleted = false;
    window.__pageChanged = false;

    // 监控XHR请求
    const oldOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function() {
        this.addEventListener('load', function() {
            if(this.responseURL.includes('/getPriceData.html') || 
               this.responseURL.includes('/priceDetail.html')) {
                window.__ajaxCompleted = true;
                console.log('XHR请求完成:', this.responseURL);
            }
        });
        oldOpen.apply(this, arguments);
    };

    // 监控fetch请求
    const oldFetch = window.fetch;
    window.fetch = function() {
        return oldFetch.apply(this, arguments).then(res => {
            if(res.url.includes('/getPriceData.html') || 
               res.url.includes('/priceDetail.html')) {
                window.__ajaxCompleted = true;
                console.log('Fetch请求完成:', res.url);
            }
            return res;
        });
    };

    // 监控页面变化
    const observer = new MutationObserver(function(mutations) {
        const currentPage = document.querySelector('span.layui-laypage-curr em:last-child');
        if (currentPage && currentPage.textContent !== window.__lastPage) {
            window.__pageChanged = true;
            window.__lastPage = currentPage.textContent;
            console.log('页码变化:', window.__lastPage);
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true
    });
    """
    driver.execute_script(script)


def click_search_button(driver):
    """增强版查询按钮点击函数（支持AJAX监控）"""
    try:
        print("🔍 正在定位查询按钮...")

        # 设置AJAX监控
        setup_ajax_monitor(driver)

        # 定位查询按钮
        search_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input.formSearchBtn#search"))
        )

        # 滚动到按钮位置
        scroll_to_element(driver, search_btn)

        # 高亮按钮便于调试
        driver.execute_script("arguments[0].style.border='3px solid red';", search_btn)
        human_like_delay()

        # 模拟人类点击行为
        ActionChains(driver).move_to_element(search_btn).pause(0.5).click().perform()
        print("🖱️ 已点击查询按钮")

        # 等待AJAX请求完成
        print("⏳ 等待数据加载...")
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return window.__ajaxCompleted === true;")
        )

        # 额外等待表格渲染
        human_like_delay(1, 2)
        print("✅ 数据加载完成")
        return True

    except TimeoutException:
        print("⏰ 错误: 数据加载超时")
        driver.save_screenshot('timeout_after_search.png')
        return False
    except Exception as e:
        print(f"❌ 查询出错: {str(e)}")
        driver.save_screenshot('search_error.png')
        return False


def scrape_table_data(driver):
    try:
        print("📊 正在解析表格数据...")

        # 等待表格加载完成
        table = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.tablebox table"))
        )

        # 检查数据行
        rows = WebDriverWait(table, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tbody#tableBody tr"))
        )

        if not rows:
            print("⚠️ 表格中没有数据行")
            return []

        page_data = []
        for i, row in enumerate(rows, 1):
            try:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 10:
                    data = {
                        '一级分类': cols[0].text.strip() or "无",
                        '二级分类': cols[1].text.strip() or "无",
                        '品名': cols[2].text.strip(),
                        '最低价': cols[3].text.strip(),
                        '平均价': cols[4].text.strip(),
                        '最高价': cols[5].text.strip(),
                        '规格': cols[6].text.strip() or "无",
                        '产地': cols[7].text.strip() or "无",
                        '单位': cols[8].text.strip(),
                        '发布日期': cols[9].text.strip()
                    }
                    page_data.append(data)

                    # 每解析10行打印一次进度
                    if i % 10 == 0:
                        print(f"📝 已解析第{i}行数据: {cols[2].text[:20]}...")
                else:
                    print(f"⚠️ 第{i}行列数不足({len(cols)}列)")
            except Exception as e:
                print(f"❌ 解析第{i}行出错: {str(e)}")
                continue

        print(f"✅ 本页共解析到{len(page_data)}条有效数据")
        return page_data

    except TimeoutException:
        print("⏰ 错误: 表格加载超时")
        driver.save_screenshot('table_timeout.png')
        return []
    except Exception as e:
        print(f"❌ 表格解析出错: {str(e)}")
        driver.save_screenshot('table_error.png')
        return []


def navigate_to_next_page(driver):
    """完全重写的翻页功能"""
    try:
        print("⏩ 尝试翻页...")

        # 获取当前页码
        current_page = int(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.layui-laypage-curr em:last-child"))
        ).text)
        print(f"当前页码: {current_page}")

        # 重置监控状态
        driver.execute_script("""
            window.__ajaxCompleted = false;
            window.__pageChanged = false;
        """)

        # 定位下一页按钮
        next_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.layui-laypage-next:not(.layui-disabled)"))
        )

        # 高亮按钮便于调试
        driver.execute_script("arguments[0].style.border='2px solid red';", next_btn)
        human_like_delay(0.5, 1)

        # 使用JS点击确保可靠性
        driver.execute_script("arguments[0].click();", next_btn)
        print("🖱️ 已点击下一页按钮")

        # 双重等待机制
        print("⏳ 等待页码变化...")
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return window.__pageChanged === true;")
        )

        print("⏳ 等待数据加载完成...")
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return window.__ajaxCompleted === true;")
        )

        # 验证新页码
        new_page = int(driver.find_element(By.CSS_SELECTOR, "span.layui-laypage-curr em:last-child").text)
        if new_page <= current_page:
            raise Exception(f"页码未变化，当前仍为第{new_page}页")

        # 等待表格更新
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody#tableBody tr"))
        )

        print(f"✅ 成功翻页到第{new_page}页")
        return True

    except TimeoutException as e:
        driver.save_screenshot('page_timeout.png')
        return False
    except Exception as e:
        print(f"❌ 翻页出错: {str(e)}")
        driver.save_screenshot('page_error.png')
        return False


def scrape_xinfadi_with_selenium():
    """主爬虫函数"""
    print("\n" + "=" * 60)
    print("🌟 新发地价格爬虫开始运行")
    print("=" * 60)

    driver = init_driver()
    if not driver:
        return

    all_data = []
    max_pages = 5  # 测试时可设为较小的数字
    url = "http://www.xinfadi.com.cn/priceDetail.html"

    try:
        # 访问目标网址
        print(f"\n🌐 正在访问: {url}")
        driver.get(url)
        driver.save_screenshot('initial_page.png')

        # 初始页面验证
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.formSearchBtn#search"))
            )
            print("✅ 页面关键元素加载完成")
        except TimeoutException:
            print("⏰ 错误: 页面加载超时")
            driver.save_screenshot('page_load_failed.png')
            return

        # 执行查询
        if not click_search_button(driver):
            print("❌ 查询失败，终止爬取")
            return

        # 主爬取循环
        current_page = 1
        while current_page <= max_pages:
            print(f"\n📖 正在处理第 {current_page}/{max_pages} 页...")

            # 爬取当前页数据
            page_data = scrape_table_data(driver)
            if page_data:
                all_data.extend(page_data)
                print(f"📥 已累计收集 {len(all_data)} 条数据")
            else:
                print("⚠️ 当前页无数据，终止爬取")
                break

            # 尝试翻页
            if not navigate_to_next_page(driver):
                print("⏹️ 已到达最后一页")
                break

            current_page += 1

    except Exception as e:
        print(f"\n❌ 严重错误: {str(e)}")
        print(f"🔍 错误详情:\n{traceback.format_exc()}")
        driver.save_screenshot('critical_error.png')
    finally:
        driver.quit()
        print("\n🛑 浏览器已关闭")

    # 保存结果
    print("\n" + "=" * 60)
    if all_data:
        try:
            output_file = 'xinfadi_prices_selenium.csv'
            pd.DataFrame(all_data).to_csv(output_file, index=False, encoding='utf_8_sig')
            print(f"💾 成功保存 {len(all_data)} 条数据到 {output_file}")
        except Exception as e:
            print(f"❌ 保存数据失败: {str(e)}")
    else:
        print("⚠️ 警告: 未获取到任何有效数据")

    print("=" * 60)
    print("🏁 爬虫运行结束")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    scrape_xinfadi_with_selenium()