import requests
import json

base_url = "http://openapi.seoul.go.kr:8088"
api_key = "43674b49756b616538336f6e687846"


def get_year_months():
    year_months = []
    for year in range(2015, 2024+1):
        for month in range(1, 12+1):
            year_months.append(f'{year}/{month:02d}')
    return year_months

responses = []

for year_months in get_year_months():
    url = f"{base_url}/{api_key}/json/energyUseDataSummaryInfo/1/10/{year_months}"
    
    try:
        response = requests.get(url)
    
        if response.status_code == 200:
            # JSON 데이터 추출
            data = response.json()
            rows = data.get("energyUseDataSummaryInfo", {}).get("row", [])
            for row in rows:
                # 개인 유형의 데이터만 추출
                if row.get("MM_TYPE") == "개인":
                    # 현년 전기, 가스, 수도, 지역난방 에너지 사용량
                    result = {
                        "YEAR": row.get("YEAR"),
                        "MON": row.get("MON"),
                        "EUS": row.get("EUS"),
                        "GUS": row.get("GUS"),
                        "WUS": row.get("WUS"),
                        "HUS": row.get("HUS")
                    }
                    print(
                        f"{result['YEAR']}년 {result['MON']}월 "
                        f"EUS: {result['EUS']}, GUS: {result['GUS']}, WUS: {result['WUS']}, HUS: {result['HUS']}"
                    )
                    responses.append(result)
        else:
            print(f"{year_months}: API 호출 실패 ({response.status_code})")
                
    except requests.exceptions.RequestException as e:
        print(f"{year_months} 네트워크 오류: {e}")
    except json.JSONDecodeError as e:
        print(f"{year_months} JSON 파싱 실패: {e}")

print("api 호출 성공")
print(f"총 {len(responses)}개의 데이터 수집 완료")


import pandas as pd

# JSON 데이터를 pandasDataFrame으로 변환
df = pd.DataFrame(responses)


# 계절 함수 정의    
def get_season(month):
    month = int(month)
    if month in [3, 4, 5]:
        return '봄'
    elif month in [6, 7, 8]:
        return '여름'
    elif month in [9, 10, 11]:
        return '가을'
    else:
        return '겨울'
    
# MON 컬럼에 전처리 함수 적용하여 SEASON 컬럼 생성
df['SEASON'] = df['MON'].apply(get_season)
# 컬럼 순서 변경
df = df[['YEAR', 'MON', 'SEASON', 'EUS', 'GUS', 'WUS', 'HUS']]

print("\n====전처리 결과 데이터 확인====\n")
print(df.head(20))
print(df.info())
print(df.describe())


# 시각화
import matplotlib.pyplot as plt

plt.rc('font', family='NanumBarunGothic')

## 에너지 사용량 컬럼을 숫자형으로 변환
df['EUS'] = pd.to_numeric(df['EUS'], errors='coerce')
df['GUS'] = pd.to_numeric(df['GUS'], errors='coerce')
df['WUS'] = pd.to_numeric(df['WUS'], errors='coerce')
df['HUS'] = pd.to_numeric(df['HUS'], errors='coerce')

## 총 에너지 사용량 = 전기 + 가스 + 수도 + 지역난방
df['TOTAL_ENERGY_USE'] = df['EUS'] + df['GUS'] + df['WUS'] + df['HUS']


## 연도별로 그룹화하여 합계 계산
YEAR_TOTAL_ENERGY_USE = df.groupby('YEAR')['TOTAL_ENERGY_USE'].sum().reset_index()
## 컬럼값 변환
YEAR_TOTAL_ENERGY_USE['YEAR'] = YEAR_TOTAL_ENERGY_USE['YEAR'].astype(int)
YEAR_TOTAL_ENERGY_USE['TOTAL_ENERGY_USE'] = YEAR_TOTAL_ENERGY_USE['TOTAL_ENERGY_USE'] / 1_000_000
## 정렬
YEAR_TOTAL_ENERGY_USE = YEAR_TOTAL_ENERGY_USE.sort_values('YEAR')

print("\n====연도별 총 에너지 사용량====\n")
print(YEAR_TOTAL_ENERGY_USE)

plt.plot(YEAR_TOTAL_ENERGY_USE['YEAR'], YEAR_TOTAL_ENERGY_USE['TOTAL_ENERGY_USE'], linestyle='-', marker='o', color='b', label='총 에너지 사용량')
plt.title("연도별 에너지 사용 총액 변화 - 2685")   
plt.xlabel("연도")
plt.ylabel("에너지 사용량(단위: 백만)")
plt.grid(True)
plt.legend()
plt.xticks(YEAR_TOTAL_ENERGY_USE['YEAR'], rotation=45)
# plt.show()



# SEASON별 가스 사용량 평균을 막대 그래프로 시각화하고, 각 막대에 구체적인 수치를 표시
SEASON_GUS_MEAN = df.groupby('SEASON')['GUS'].mean().reset_index()
SEASON_GUS_MEAN['GUS'] = SEASON_GUS_MEAN['GUS'].astype(int)

# 계절 순서 지정
season_order = ['봄', '여름', '가을', '겨울']
SEASON_GUS_MEAN['SEASON'] = pd.Categorical(SEASON_GUS_MEAN['SEASON'], categories=season_order)
SEASON_GUS_MEAN = SEASON_GUS_MEAN.sort_values('SEASON').reset_index(drop=True)


print("\n====SEASON별 가스 사용량 평균====\n")
print(SEASON_GUS_MEAN)

plt.figure(figsize=(10, 6))
x_pos = range(len(SEASON_GUS_MEAN))  # 0, 1, 2, 3
plt.bar(x_pos, SEASON_GUS_MEAN['GUS'], color='skyblue')
# X축 설정
plt.xticks(x_pos, SEASON_GUS_MEAN['SEASON'])
plt.title("계절별 가스 사용량 평균 - 2685")
plt.xlabel("계절")
plt.ylabel("가스 사용량 평균")
plt.grid(True, alpha=0.3, axis='y')

for i, v in enumerate(SEASON_GUS_MEAN['GUS']):
    plt.text(i, v, f'{v:,}', ha='center', va='bottom', fontsize=10)
plt.tight_layout()
plt.show()
