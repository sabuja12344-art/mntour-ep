#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
롯데관광 마운틴투어 → 네이버 쇼핑 EP 자동 생성기
실행하면 ep.txt 파일이 만들어집니다.
"""

import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime

# ───────────────────────────────────────────
# 설정값
# ───────────────────────────────────────────
BASE_URL   = "https://mntour.lottetour.com"
API_URL    = f"{BASE_URL}/pdtListAjax"
OUTPUT_FILE = "ep.txt"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": BASE_URL,
    "X-Requested-With": "XMLHttpRequest",
}

# 네이버 쇼핑 EP 필드 순서
EP_FIELDS = [
    "id", "title", "price_pc", "link", "mobile_link", "image",
    "category_name1", "category_name2", "shipping", "description"
]

# menuNo1 → 네이버 EP에 쓸 카테고리 이름 매핑
CATEGORY_NAME = {
    "604":  "유럽여행",
    "1085": "일본여행",
    "606":  "미주/중남미여행",
    "605":  "남태평양여행",
    "601":  "동남아여행",
    "951":  "중국/대만여행",
    "609":  "크루즈",
    "622":  "해외골프",
    "607":  "부산/지방출발",
    "1947": "국내여행",
    "834":  "제주여행",
}


# ───────────────────────────────────────────
# 1단계: 카테고리 목록 수집
# ───────────────────────────────────────────
def get_all_categories():
    """메인 메뉴 HTML에서 모든 카테고리 URL(menuNo1, menuNo2)을 추출합니다."""
    print("[ 1단계 ] 카테고리 목록 수집 중...")

    try:
        resp = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"  오류: 메인 페이지에 접속하지 못했습니다 → {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    categories = []
    seen = set()

    # /pdtList/{menuNo1}/{menuNo2} 형식의 링크 수집
    for a in soup.find_all("a", href=re.compile(r"^/pdtList/\d+/\d+")):
        m = re.match(r"^/pdtList/(\d+)/(\d+)", a["href"])
        if not m:
            continue
        no1, no2 = m.group(1), m.group(2)
        if (no1, no2) in seen:
            continue
        seen.add((no1, no2))
        categories.append({
            "menu_no1": no1,
            "menu_no2": no2,
            "sub_name": a.get_text(strip=True),
            "category_name2": CATEGORY_NAME.get(no1, a.get_text(strip=True)),
        })

    # /area/{menuNo1} 형식의 링크도 수집 (menuNo2=0 으로 호출)
    for a in soup.find_all("a", href=re.compile(r"^/area/\d+$")):
        m = re.match(r"^/area/(\d+)$", a["href"])
        if not m:
            continue
        no1 = m.group(1)
        if (no1, "0") in seen:
            continue
        seen.add((no1, "0"))
        categories.append({
            "menu_no1": no1,
            "menu_no2": "0",
            "sub_name": a.get_text(strip=True),
            "category_name2": CATEGORY_NAME.get(no1, a.get_text(strip=True)),
        })

    print(f"  {len(categories)}개 카테고리 발견")
    return categories


# ───────────────────────────────────────────
# 2단계: 카테고리별 상품 수집
# ───────────────────────────────────────────
def get_products(cat):
    """카테고리 하나에서 상품 목록을 가져옵니다."""
    url = (
        f"{API_URL}"
        f"?menuNo1={cat['menu_no1']}"
        f"&menuNo2={cat['menu_no2']}"
        f"&menuNo3=0&menuNo4=0&prdCnt=-1"
    )

    try:
        resp = requests.post(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"    [오류] {cat['sub_name']} - {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    products = []

    for li in soup.select("ul.list > li"):
        try:
            # 상품명
            title_tag = li.select_one("div.txt a strong")
            title = title_tag.get_text(strip=True) if title_tag else ""

            # 상품 URL
            link_tag = li.select_one("div.txt > a")
            href = link_tag.get("href", "") if link_tag else ""
            link = BASE_URL + href if href.startswith("/") else href

            # 상품 고유 ID (godId)
            god_id = ""
            tag = li.select_one("[godid]")
            if tag:
                god_id = tag.get("godid", "")
            if not god_id:
                m = re.search(r"godId=(\d+)", href)
                god_id = m.group(1) if m else ""

            # 가격 (숫자만 추출)
            price_tag = li.select_one("div.price_box strong")
            price_text = price_tag.get_text(strip=True) if price_tag else ""
            price = re.sub(r"[^\d]", "", price_text)

            # 이미지 URL
            img_tag = li.select_one("div.img img")
            image = img_tag.get("src", "") if img_tag else ""
            if image.startswith("//"):
                image = "https:" + image
            elif image.startswith("http://"):
                image = "https://" + image[7:]

            # 상품 설명 (탭·줄바꿈은 EP 규격 위반이므로 공백으로 교체)
            desc_tag = li.select_one("div.txt a p")
            description = desc_tag.get_text(strip=True) if desc_tag else ""
            description = re.sub(r"[\t\n\r]+", " ", description)
            title = re.sub(r"[\t\n\r]+", " ", title)

            # 필수 필드가 없으면 건너뜀
            if not god_id or not title or not price:
                continue

            mobile_link = link.replace("mntour.lottetour.com", "mmntour.lottetour.com")

            products.append({
                "id":             god_id,
                "title":          title,
                "price_pc":       price,
                "link":           link,
                "mobile_link":    mobile_link,
                "image":          image,
                "category_name1": "여행",
                "category_name2": cat["category_name2"],
                "shipping":       "0",
                "description":    description,
            })

        except Exception:
            continue

    return products


# ───────────────────────────────────────────
# 3단계: ep.txt 저장
# ───────────────────────────────────────────
def save_ep(products):
    """네이버 쇼핑 EP 3.0 규격으로 ep.txt를 저장합니다."""
    header = "\t".join(f"<<<{f}>>>" for f in EP_FIELDS)
    lines  = [header]

    for p in products:
        row = "\t".join(p.get(f, "") for f in EP_FIELDS)
        lines.append(row)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"  ep.txt 저장 완료: {len(products)}개 상품")


# ───────────────────────────────────────────
# 메인 실행
# ───────────────────────────────────────────
def run_once():
    print("=" * 55)
    print(f"  EP 생성 시작  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    # 1. 카테고리 수집
    categories = get_all_categories()
    if not categories:
        print("카테고리를 가져오지 못했습니다. 인터넷 연결을 확인해 주세요.")
        return

    # 2. 상품 수집 (godId 기준으로 중복 제거)
    print("\n[ 2단계 ] 상품 수집 중...")
    all_products = {}

    for i, cat in enumerate(categories, 1):
        print(f"  [{i:02d}/{len(categories):02d}] {cat['sub_name']}")
        products = get_products(cat)
        new = 0
        for p in products:
            if p["id"] not in all_products:
                all_products[p["id"]] = p
                new += 1
        print(f"         신규 {new}개  (누적 {len(all_products)}개)")
        time.sleep(0.4)   # 서버에 너무 빠르게 요청하지 않기 위한 딜레이

    # 3. EP 파일 저장
    print(f"\n[ 3단계 ] ep.txt 저장 중...")
    save_ep(list(all_products.values()))

    print(f"\n완료! 파일 위치: {OUTPUT_FILE}")
    print("=" * 55)


if __name__ == "__main__":
    run_once()
