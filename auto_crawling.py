#!/usr/bin/env python3
import re
import json
import os
import base64
import requests
from selenium_kt import fetch_kt_jobs  # 채용 공고 크롤링 함수 모듈

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

# GitHub API 관련 설정 (환경 변수에서 가져오기)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")      # Personal Access Token
REPO_OWNER = os.environ.get("GITHUB_REPO_OWNER")     # 예: "Soong22"
REPO_NAME = os.environ.get("GITHUB_REPO_NAME")       # 예: "New_Posting_Alert"
FILE_PATH = DATA_FILE  # 저장소 내 파일 경로

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

# GitHub API를 사용해 job_postings.json 파일을 업데이트하는 함수
def update_file_on_github(commit_message="Update job_postings.json"):
    """GitHub API를 이용하여 파일 내용을 업데이트"""
    if not GITHUB_TOKEN or not REPO_OWNER or not REPO_NAME:
        print("❌ GitHub 관련 환경 변수가 설정되어 있지 않습니다.")
        return

    # 1. 현재 파일 내용을 base64 인코딩
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        file_content = f.read()
    encoded_content = base64.b64encode(file_content.encode("utf-8")).decode("utf-8")

    # 2. 기존 파일 정보를 조회하여 SHA 값 가져오기
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    get_resp = requests.get(url, headers=headers)
    if get_resp.status_code == 200:
        file_info = get_resp.json()
        sha = file_info["sha"]
    elif get_resp.status_code == 404:
        # 파일이 없으면 새로 생성할 수 있음
        sha = None
    else:
        print("❌ 파일 정보를 가져오지 못했습니다:", get_resp.text)
        return

    # 3. 파일 업데이트 API 호출 (PUT)
    data = {
        "message": commit_message,
        "content": encoded_content,
    }
    if sha:
        data["sha"] = sha

    put_resp = requests.put(url, headers=headers, json=data)
    if put_resp.status_code in (200, 201):
        print("✅ GitHub 파일 업데이트 성공!")
    else:
        print("❌ GitHub 파일 업데이트 실패:", put_resp.text)

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
    
    # GitHub API를 통해 JSON 파일 업데이트 (커밋 및 푸시 효과)
    update_file_on_github()

if __name__ == "__main__":
    main()
