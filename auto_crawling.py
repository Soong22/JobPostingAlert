#!/usr/bin/env python3
import re
import json
import os
import subprocess
from selenium_kt import fetch_kt_jobs  # 채용 공고 크롤링 함수 모듈
import requests

# 텔레그램 메시지 전송 함수 (requests 이용)
def send_message(token, chat_id, text):
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': text}
    response = requests.post(url, data=payload)
    return response

# 설정
TOKEN = "7801153388:AAFgEMsO4hNvjKMu468i5mAgTtaFtdOEl7E"  # BotFather로 받은 봇 토큰
CHAT_ID = "7692140662"  # 확인한 채팅 ID (문자열)
DATA_FILE = "job_postings.json"  # 이전 공고를 저장할 파일

def load_previous_jobs():
    """이전 실행 시 저장된 공고 데이터를 JSON 파일에서 로드"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return []

def save_jobs(jobs):
    """현재 공고 데이터를 JSON 파일에 저장"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

def get_new_jobs(current_jobs, previous_jobs):
    """
    현재 크롤링된 공고 목록과 이전에 저장된 공고 목록을 비교하여,
    이전에 없던 새로운 공고 목록을 반환합니다.
    여기서는 공고의 'link' 값을 고유 식별자로 사용합니다.
    """
    previous_links = {job["link"] for job in previous_jobs}
    new_jobs = [job for job in current_jobs if job["link"] not in previous_links]
    return new_jobs

def git_push():
    """job_postings.json 파일의 변경사항을 Git에 커밋하고 Heroku 원격 저장소로 푸시"""
    try:
        # 모든 변경사항 스테이징
        subprocess.run(["git", "add", "."], check=True)
        # 커밋
        subprocess.run(["git", "commit", "-m", "Update job_postings.json"], check=True)
        # Heroku 원격 저장소로 푸시 (브랜치 이름은 master로 가정)
        subprocess.run(["git", "push", "heroku", "master"], check=True)
        print("✅ Git push 완료")
    except subprocess.CalledProcessError as e:
        print("❌ Git push 실패:", e)

def main():
    print("🚀 크롤링 실행 중...")
    current_jobs = fetch_kt_jobs()
    print(f"✅ 크롤링 완료: {len(current_jobs)}개 공고 수집됨")
    
    previous_jobs = load_previous_jobs()
    new_jobs = get_new_jobs(current_jobs, previous_jobs)
    
    if new_jobs:
        for job in new_jobs:
            title = job.get("title", "No Title")
            company = job.get("company", "Unknown Company")
            date = job.get("date", "")
            dday = job.get("dday", "")
            link = job.get("link", "")
            message = f"{title}\n{company} | {date} | {dday}\n{link}"
            response = send_message(TOKEN, CHAT_ID, message)
            try:
                result = response.json()
                print("✅ 텔레그램 메시지 전송 완료:", result)
            except Exception as e:
                print("❌ 텔레그램 메시지 전송 실패:", e)
    else:
        print("🚀 새로운 공고 없음")
    
    # 현재 크롤링 결과를 저장 (다음 실행 시 비교용)
    save_jobs(current_jobs)
    print("✅ 스크립트 실행 완료")
    
    # Git에 변경 사항을 커밋하고 푸시
    git_push()

if __name__ == "__main__":
    main()
