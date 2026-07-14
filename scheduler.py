#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EP 자동 갱신 스케줄러
이 파일을 실행하면 1시간마다 crawler.py를 자동으로 실행합니다.
창을 닫지 않고 계속 켜두면 됩니다.
"""

import time
from datetime import datetime
from crawler import run_once

INTERVAL_HOURS = 1   # 갱신 주기 (시간)
INTERVAL_SEC   = INTERVAL_HOURS * 3600


def main():
    print("=" * 55)
    print("  EP 자동 갱신 스케줄러 시작")
    print(f"  갱신 주기: {INTERVAL_HOURS}시간마다")
    print("  종료하려면 이 창을 닫거나 Ctrl+C 를 누르세요.")
    print("=" * 55)

    while True:
        run_once()

        next_run = datetime.fromtimestamp(time.time() + INTERVAL_SEC)
        print(f"\n다음 실행 예정: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"({INTERVAL_HOURS}시간 대기 중... 창을 닫지 마세요)\n")

        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n스케줄러를 종료합니다.")
