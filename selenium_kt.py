import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def fetch_kt_jobs():
    print("🚀 크롤링 실행 중...")

    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=service, options=options)
    url = "https://recruit.kt.com/careers"
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article.ebox")))
        print("✅ 채용 공고 로딩 완료")
    except:
        print("❌ 채용 공고를 찾을 수 없음")
        driver.quit()
        return []

    jobs = []
    for job in driver.find_elements(By.CSS_SELECTOR, "article.ebox"):
        try:
            # 제목 찾기: h4 태그를 우선 시도하고, 없으면 h3, a, 등 대체
            try:
                title_tag = WebDriverWait(job, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h4"))
                )
                title = title_tag.text.strip()
            except:
                try:
                    title_tag = job.find_element(By.CSS_SELECTOR, "h3")
                    title = title_tag.text.strip()
                except:
                    try:
                        title_tag = job.find_element(By.CSS_SELECTOR, "a")
                        title = title_tag.text.strip()
                    except:
                        # 오류 메시지 출력 대신 그냥 건너뛰기
                        continue

            # 링크 찾기
            try:
                link_tag = job.find_element(By.CSS_SELECTOR, "a")
                raw_link = link_tag.get_attribute("href")
            except:
                raw_link = "/careers/fallback"
            link = raw_link if raw_link.startswith("http") else "https://recruit.kt.com" + raw_link

            # 기간과 D-Day 정보 가져오기
            date_tag = job.find_element(By.CSS_SELECTOR, ".date")
            dday_tag = job.find_element(By.CSS_SELECTOR, ".d-day")
            date = date_tag.text.strip()
            dday = dday_tag.text.strip()

            # 회사명 추출 (대괄호 [] 안의 내용)
            company_match = re.search(r"\[(.*?)\]", title)
            company = company_match.group(1) if company_match else "KT"

            jobs.append({"title": title, "company": company, "date": date, "dday": dday, "link": link})
        except:
            # 오류가 발생해도 오류 메시지를 출력하지 않고 건너뜀
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
