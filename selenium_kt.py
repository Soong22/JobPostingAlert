import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Heroku buildpack에서 환경 변수가 설정되어야 함.
    # 만약 설정되지 않았다면, 기본 경로를 사용합니다.
    binary = os.environ.get("GOOGLE_CHROME_BIN")
    if not binary:
        # Heroku buildpack-chrome-for-testing의 기본 경로 중 하나일 수 있습니다.
        binary = "/app/.apt/usr/bin/google-chrome"
        print("GOOGLE_CHROME_BIN 환경변수가 설정되어 있지 않아 기본 경로를 사용합니다:", binary)
    chrome_options.binary_location = binary

    # CHROMEDRIVER_PATH 환경 변수도 사용
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
    if not chromedriver_path:
        raise Exception("CHROMEDRIVER_PATH 환경변수가 설정되어 있지 않습니다.")
    
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def fetch_kt_jobs():
    print("🚀 크롤링 실행 중...")
    driver = get_chrome_driver()
    url = "https://recruit.kt.com/careers"
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article.ebox"))
        )
        print("✅ 채용 공고 로딩 완료")
    except Exception as e:
        print("❌ 채용 공고를 찾을 수 없음:", e)
        driver.quit()
        return []

    jobs = []
    for job in driver.find_elements(By.CSS_SELECTOR, "article.ebox"):
        try:
            # 제목 찾기: h4 > h3 > a 순서로 시도
            try:
                title_tag = WebDriverWait(job, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h4"))
                )
                title = title_tag.text.strip()
            except Exception:
                try:
                    title_tag = job.find_element(By.CSS_SELECTOR, "h3")
                    title = title_tag.text.strip()
                except Exception:
                    try:
                        title_tag = job.find_element(By.CSS_SELECTOR, "a")
                        title = title_tag.text.strip()
                    except Exception:
                        continue

            try:
                link_tag = job.find_element(By.CSS_SELECTOR, "a")
                raw_link = link_tag.get_attribute("href")
            except Exception:
                raw_link = "/careers/fallback"
            link = raw_link if raw_link.startswith("http") else "https://recruit.kt.com" + raw_link

            date_tag = job.find_element(By.CSS_SELECTOR, ".date")
            dday_tag = job.find_element(By.CSS_SELECTOR, ".d-day")
            date = date_tag.text.strip()
            dday = dday_tag.text.strip()

            company_match = re.search(r"\[(.*?)\]", title)
            company = company_match.group(1) if company_match else "KT"

            jobs.append({"title": title, "company": company, "date": date, "dday": dday, "link": link})
        except Exception:
            continue

    driver.quit()
    print(f"✅ 크롤링 완료: {len(jobs)}개 공고 수집됨")
    return jobs

if __name__ == '__main__':
    jobs = fetch_kt_jobs()
    print("\n📢 KT 채용 공고 리스트")
    for i, job in enumerate(jobs[:5], 1):
        print(f"{i}. 제목: {job['title']}")
        print(f"   회사: {job['company']}")
        print(f"   기간: {job['date']}")
        print(f"   D-Day: {job['dday']}")
        print(f"   링크: {job['link']}\n")
