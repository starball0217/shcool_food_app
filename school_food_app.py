import streamlit as st
from datetime import datetime, timedelta
from ai_helper import ask_ai
from neis_helper import search_schools, get_meal_info, normalize_school_name
import os

st.set_page_config(page_title="급식알리미", layout="centered")

st.title("🍽️ 급식알리미")
st.subheader("학교의 급식을 알려드립니다")

# 세션 상태 초기화
if "meal_result" not in st.session_state:
    st.session_state.meal_result = None

# 메인 콘텐츠 - 중앙 검색 폼
st.divider()

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.subheader("📚 급식 검색")

    # 학교명 입력
    school_name = st.text_input(
        "학교명을 입력하세요",
        placeholder="예: 서울고등학교",
        label_visibility="collapsed"
    )

    # 날짜 선택
    search_date = st.date_input(
        "급식 날짜를 선택하세요",
        value=datetime.now(),
        min_value=datetime.now() - timedelta(days=30),
        max_value=datetime.now() + timedelta(days=30),
        label_visibility="collapsed"
    )

    st.write("")

    # 검색 버튼
    if st.button("🔍 급식 검색", use_container_width=True, type="primary"):
        if not school_name:
            st.error("❌ 학교명을 입력해주세요!")
        else:
            with st.spinner("검색 중입니다..."):
                # 학교 검색
                schools = search_schools(school_name)

                if not schools:
                    st.error(f"❌ 없습니다")
                else:
                    # 정확한 이름으로 학교 선택
                    normalized_input = normalize_school_name(school_name)
                    selected_school = None

                    # 1. 정확히 일치하는 학교 찾기
                    for s in schools:
                        if isinstance(s, dict) and s.get('SCHUL_NM') == normalized_input:
                            if 'ATPT_OFCDC_SC_CODE' in s and 'SD_SCHUL_CODE' in s:
                                selected_school = s
                                break

                    # 2. 정확한 일치가 없으면 첫 번째 유효한 데이터 사용
                    if not selected_school:
                        for s in schools:
                            if isinstance(s, dict) and 'SCHUL_NM' in s and 'ATPT_OFCDC_SC_CODE' in s and 'SD_SCHUL_CODE' in s:
                                selected_school = s
                                break

                    if selected_school:
                        # 급식정보 조회
                        meal_date_str = search_date.strftime("%Y%m%d")
                        meal_data = get_meal_info(
                            selected_school["ATPT_OFCDC_SC_CODE"],
                            selected_school["SD_SCHUL_CODE"],
                            meal_date_str,
                            selected_school["SCHUL_NM"]
                        )

                        # 결과 저장
                        st.session_state.meal_result = {
                            "school": selected_school,
                            "meal_data": meal_data,
                            "search_date": search_date
                        }
                        st.success(f"✅ 검색 완료!")
                    else:
                        st.error("❌ 없습니다")

st.divider()

# 결과 표시
if st.session_state.meal_result:
    result = st.session_state.meal_result
    school = result["school"]
    meal_data = result["meal_data"]
    search_date = result["search_date"]

    # 학교 정보 표시
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"🏫 **학교:** {school['SCHUL_NM']}")
    with col2:
        st.info(f"📅 **날짜:** {search_date.strftime('%Y년 %m월 %d일')}")

    st.info(f"📍 **지역:** {school.get('ATPT_OFCDC_SC_NM', '정보 없음')}")

    st.divider()

    # 급식 정보 표시
    if meal_data and "DDISH_NM" in meal_data:
        # Claude AI를 통해 정리
        prompt = f"""
{search_date.strftime('%Y년 %m월 %d일')} {school['SCHUL_NM']}의 급식 정보입니다.

급식 메뉴: {meal_data.get('DDISH_NM', '정보 없음')}
칼로리: {meal_data.get('CAL_INFO', '정보 없음')}
영양정보: {meal_data.get('NTR_INFO', '정보 없음')}
원산지: {meal_data.get('ORPLC_INFO', '정보 없음')}

이 정보를 사용자 친화적으로 정리해서 설명해줘.
메뉴는 줄바꿈으로 구분해서 보기 좋게 표시하고,
영양 정보도 함께 표시해줘.
        """

        try:
            response = ask_ai(prompt)
            st.success("✅ 급식 정보를 찾았습니다!")
            st.markdown("### 📋 오늘의 급식")
            st.markdown(response)

            # 원본 데이터 표시
            with st.expander("📊 상세 정보"):
                st.json(meal_data)

        except Exception as e:
            st.error(f"AI 처리 오류: {str(e)}")
    else:
        st.warning("⚠️ 해당 날짜의 급식 정보를 찾을 수 없습니다.")

        # 검색 결과가 있으면 학교 정보라도 표시
        if school:
            with st.expander("🏫 학교 기본정보"):
                school_info = {
                    "학교명": school.get('SCHUL_NM'),
                    "지역": school.get('ATPT_OFCDC_SC_NM'),
                }
                if 'SCHUL_KND_SC_NM' in school:
                    school_info["학교급"] = school.get('SCHUL_KND_SC_NM')
                st.json(school_info)

# 푸터
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🔗 NEIS 포털")
with col2:
    st.caption("💡 Claude Haiku")
with col3:
    st.caption("📱 Streamlit")
