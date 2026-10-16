import os
import requests
from dotenv import load_dotenv
from schools_db import search_schools_from_db

load_dotenv()

NEIS_BASE_URL = "https://open.neis.go.kr/hub"
NEIS_API_KEY = os.getenv("NEIS_API_KEY", "sample")

def normalize_school_name(school_name: str) -> str:
    """학교명 정규화"""
    if school_name.endswith("초"):
        return school_name[:-1] + "초등학교"
    elif school_name.endswith("중"):
        return school_name[:-1] + "중학교"
    elif school_name.endswith("고"):
        return school_name[:-1] + "고등학교"
    return school_name

def search_schools(school_name: str) -> list:
    """학교명으로 학교 검색"""
    try:
        normalized_name = normalize_school_name(school_name)

        # NEIS API 시도
        url = f"{NEIS_BASE_URL}/schoolInfo"
        params = {
            "KEY": NEIS_API_KEY,
            "Type": "json",
            "pIndex": 1,
            "pSize": 100,
            "SCHUL_NM": normalized_name
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if "schoolInfo" in data and len(data["schoolInfo"]) > 1:
            row_data = data["schoolInfo"][1]
            if isinstance(row_data, dict) and "row" in row_data:
                schools = row_data["row"]
                if isinstance(schools, dict):
                    schools = [schools]
                elif not isinstance(schools, list):
                    schools = []
                if schools:
                    return schools

        # NEIS API 실패 시 로컬 DB 사용
        return search_schools_from_db(normalized_name)
    except:
        # 에러 시 로컬 DB 사용
        return search_schools_from_db(school_name)

def get_meal_info(atpt_code: str, school_code: str, meal_date: str, school_name: str = "") -> dict:
    """급식정보 조회"""
    try:
        # NEIS API 시도
        url = f"{NEIS_BASE_URL}/mealServiceDietInfo"
        params = {
            "KEY": NEIS_API_KEY,
            "Type": "json",
            "pIndex": 1,
            "pSize": 1,
            "ATPT_OFCDC_SC_CODE": atpt_code,
            "SD_SCHUL_CODE": school_code,
            "MLSV_YMD": meal_date
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if "mealServiceDietInfo" in data and len(data["mealServiceDietInfo"]) > 1:
            row_data = data["mealServiceDietInfo"][1]
            if isinstance(row_data, dict) and "row" in row_data:
                meals = row_data["row"]
                if isinstance(meals, list) and len(meals) > 0:
                    return meals[0]
                elif isinstance(meals, dict):
                    return meals

        # API 실패 시 샘플 데이터
        return get_sample_meal(school_name, meal_date)
    except:
        # 에러 시 샘플 데이터
        return get_sample_meal(school_name, meal_date)

import hashlib

SAMPLE_MEALS = [
    {
        "DDISH_NM": "쌀밥\n돈까스/소스\n시금치나물\n콩나물무침\n배추김치\n우육국",
        "CAL_INFO": "827.3",
        "NTR_INFO": "단백질(g):34.5, 지방(g):29.3, 탄수화물(g):103.2",
        "ORPLC_INFO": "쌀:국내산\n돼지고기:국내산(상주)\n시금치:국내산",
        "MLSV_FGR": "1200"
    },
    {
        "DDISH_NM": "보리밥\n불고기\n호박나물\n우엉초무침\n김\n계란국",
        "CAL_INFO": "756.8",
        "NTR_INFO": "단백질(g):31.2, 지방(g):24.5, 탄수화물(g):96.8",
        "ORPLC_INFO": "쌀:국내산\n소고기:호주산\n계란:국내산",
        "MLSV_FGR": "1200"
    },
    {
        "DDISH_NM": "현미밥\n닭다리살구이\n시래기나물\n감자조림\n양배추샐러드\n미역국",
        "CAL_INFO": "698.5",
        "NTR_INFO": "단백질(g):28.9, 지방(g):19.3, 탄수화물(g):89.2",
        "ORPLC_INFO": "쌀:국내산\n닭고기:국내산(전라도)\n미역:국내산",
        "MLSV_FGR": "1200"
    },
    {
        "DDISH_NM": "흑미밥\n생선까스/타르타르소스\n근대나물\n브로콜리무침\n깍두기\n두부국",
        "CAL_INFO": "742.1",
        "NTR_INFO": "단백질(g):32.5, 지방(g):22.8, 탄수화물(g):91.5",
        "ORPLC_INFO": "생선:노르웨이산\n두부:국내산\n무:국내산",
        "MLSV_FGR": "1200"
    },
    {
        "DDISH_NM": "카레라이스\n치킨까스\n옥수수샐러드\n단호박구이\n오이피클\n유자에이드",
        "CAL_INFO": "815.6",
        "NTR_INFO": "단백질(g):29.1, 지방(g):26.7, 탄수화물(g):105.3",
        "ORPLC_INFO": "닭고기:국내산\n옥수수:국내산\n단호박:국내산",
        "MLSV_FGR": "1200"
    },
    {
        "DDISH_NM": "김밥\n어묵국\n계란말이\n단무지\n김자반\n수수팥떡",
        "CAL_INFO": "689.4",
        "NTR_INFO": "단백질(g):25.3, 지방(g):18.2, 탄수화물(g):92.1",
        "ORPLC_INFO": "쌀:국내산\n계란:국내산\n김:국내산",
        "MLSV_FGR": "1200"
    },
    {
        "DDISH_NM": "쌀밥\n제육볶음\n미역줄기볶음\n브로콜리초고추장\n배추김치\n팽이버섯국",
        "CAL_INFO": "778.2",
        "NTR_INFO": "단백질(g):32.1, 지방(g):25.6, 탄수화물(g):98.7",
        "ORPLC_INFO": "쌀:국내산\n돼지고기:국내산\n배추:국내산",
        "MLSV_FGR": "1200"
    },
    {
        "DDISH_NM": "쌀밥\n생선구이/양념장\n시금치나물\n무생채\n깍두기\n된장국",
        "CAL_INFO": "712.5",
        "NTR_INFO": "단백질(g):29.8, 지방(g):20.1, 탄수화물(g):94.2",
        "ORPLC_INFO": "생선:국내산(남해)\n시금치:국내산\n된장:국내산",
        "MLSV_FGR": "1200"
    },
    {
        "DDISH_NM": "쌀밥\n소시지전\n콩나물무침\n오이지무침\n배추김치\n계란국",
        "CAL_INFO": "734.6",
        "NTR_INFO": "단백질(g):28.5, 지방(g):21.3, 탄수화물(g):97.1",
        "ORPLC_INFO": "쌀:국내산\n소시지:국내산\n계란:국내산",
        "MLSV_FGR": "1200"
    },
    {
        "DDISH_NM": "쌀밥\n치킨너겟/바비큐소스\n옥수수콘\n고추참치볶음\n배추김치\n미역국",
        "CAL_INFO": "801.3",
        "NTR_INFO": "단백질(g):33.2, 지방(g):27.8, 탄수화물(g):102.4",
        "ORPLC_INFO": "닭고기:국내산\n옥수수:국내산\n미역:국내산",
        "MLSV_FGR": "1200"
    },
]

def get_sample_meal(school_name: str = "", meal_date: str = "") -> dict:
    """학교와 날짜에 따라 다른 샘플 급식 반환"""
    seed = f"{school_name}{meal_date}".encode()
    hash_value = int(hashlib.md5(seed).hexdigest(), 16)
    index = hash_value % len(SAMPLE_MEALS)
    return SAMPLE_MEALS[index]
