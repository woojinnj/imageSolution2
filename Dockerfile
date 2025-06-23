# 1. Python 베이스 이미지 선택
FROM python:3.11-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. requirements.txt 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 소스 코드 복사
COPY real_main_02 ./real_main_02

# 5. 포트 노출
EXPOSE 8000

# 6. FastAPI 앱 실행
CMD ["uvicorn", "real_main_02.main04:fastapi_app", "--host", "0.0.0.0", "--port", "8000"]
