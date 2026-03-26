# imageSolution2

PostgreSQL 데이터베이스에 저장된 이미지를 조회하고 관리하는 풀스택 웹 애플리케이션입니다.
IoT/디바이스 모니터링 플랫폼(AIMS - Asset & Image Management System)의 이미지 뷰어 및 관리 시스템으로 동작합니다.

---

## 주요 기능

- **이미지 조회**: DB에 저장된 압축/인코딩된 이미지를 페이지네이션 방식으로 열람
- **검색 및 필터링**: 디바이스 코드 및 아티클 ID 기반 검색
- **사용자 인증**: JWT 기반 로그인/회원가입, 비밀번호 초기화
- **역할 기반 접근 제어**: `admin` / `user` 두 가지 권한
- **DB 연결 관리**: 다수의 PostgreSQL 연결을 동적으로 설정 및 저장 (Excel/CSV 일괄 업로드 지원)
- **관리자 패널**: 사용자 계정 관리, DB 연결 CRUD
- **데스크탑 앱 모드**: PyQt5 GUI + FastAPI 동시 실행 지원

---

## 기술 스택

### Backend
| 항목 | 사용 기술 |
|------|-----------|
| 프레임워크 | FastAPI 0.115.6 |
| 언어 | Python 3.11 |
| 데이터베이스 | PostgreSQL (SQLAlchemy 2.0) |
| 인증 | JWT (PyJWT), bcrypt |
| 이미지 처리 | OpenCV, Pillow, numpy |
| 데이터 처리 | pandas, openpyxl |
| 서버 | Uvicorn (ASGI) |

### Frontend
| 항목 | 사용 기술 |
|------|-----------|
| 프레임워크 | Next.js 15.3.1 (React 19) |
| 언어 | TypeScript 5 |
| 스타일링 | Tailwind CSS 4 |
| 빌드 도구 | Turbopack |

### 인프라
- **컨테이너**: Docker (Python 3.11-slim)
- **배포**: Render.com (`https://imagesolution2.onrender.com`)

---

## 프로젝트 구조

```
imageSolution2/
├── frontend/                    # Next.js 프론트엔드
│   └── app/
│       ├── login/               # 로그인 페이지
│       ├── signup/              # 회원가입 페이지
│       ├── reset-password/      # 비밀번호 재설정
│       ├── server_config/       # DB 서버 설정
│       ├── admin/               # 관리자 패널
│       │   ├── user/            # 사용자 관리
│       │   └── dbconnection/    # DB 연결 관리
│       └── image/all2_b/        # 메인 이미지 갤러리 뷰어
│
├── real_main_02/                # FastAPI 백엔드 (현재 사용)
│   ├── main04.py                # FastAPI + PyQt5 앱 진입점
│   ├── api_main.py              # FastAPI 앱 (서버 전용)
│   ├── auth.py                  # 인증 라우터
│   ├── admin.py                 # 관리자 라우터
│   ├── dbconnection.py          # DB 연결 관리 라우터
│   └── db_info04.py             # DB 연결 설정
│
├── Dockerfile                   # Docker 컨테이너 설정
├── requirements.txt             # Python 의존성
└── Makefile                     # 실행 명령어
```

---

## 실행 방법

### 백엔드 (개발)

```bash
# Makefile 사용
make run

# 직접 실행 (서버 전용)
uvicorn real_main_02.api_main:fastapi_app --host 0.0.0.0 --port 8000

# PyQt5 데스크탑 앱 + 서버 동시 실행
python real_main_02/main04.py
```

### 프론트엔드 (개발)

```bash
cd frontend
npm install
npm run dev
# http://localhost:3000 에서 실행
```

### Docker

```bash
docker build -t imagesolution2 .
docker run -p 8000:8000 imagesolution2
```

---

## API 엔드포인트

### 인증 (`/auth`)
| Method | Path | 설명 |
|--------|------|------|
| POST | `/auth/signup` | 회원가입 |
| POST | `/auth/login` | 로그인 (JWT 토큰 반환) |
| POST | `/auth/reset-password` | 비밀번호 변경 |

### 이미지 (`/api/image`)
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/image/by-code/{code}` | 디바이스 코드로 이미지 조회 |
| GET | `/api/image/list` | 이미지 목록 (페이지네이션, 검색) |

### 관리자 (`/admin`)
| Method | Path | 설명 |
|--------|------|------|
| GET | `/admin/user` | 사용자 목록 조회 |
| POST | `/admin/reset-password` | 사용자 비밀번호 초기화 |
| DELETE | `/admin/delete-user` | 사용자 삭제 |
| GET | `/admin/dbconnections` | DB 연결 목록 |
| POST | `/admin/add-dbconnection` | DB 연결 추가 |
| DELETE | `/admin/delete-dbconnection/{id}` | DB 연결 삭제 |
| POST | `/admin/bulk-upload-dbconnections` | Excel/CSV 일괄 업로드 |

### 서버 설정
| Method | Path | 설명 |
|--------|------|------|
| POST | `/set_server` | CORE/PORTAL DB 연결 설정 |
| POST | `/disconnect_db` | DB 연결 해제 |

---

## 데이터베이스 구성

| DB | 용도 | 주요 테이블 |
|----|------|------------|
| AIMS_CORE_DB | 디바이스 엔드포인트 및 이미지 데이터 | `enddevice`, `content` |
| AIMS_PORTAL_DB | 아티클 및 디바이스 연결 데이터 | `end_device_articles`, `article` |
| AUTH_DB (Render) | 사용자 인증 및 DB 연결 정보 저장 | `users`, `dbconnection` |

---

## 환경 변수

| 변수 | 설명 |
|------|------|
| `JWT_SECRET` | JWT 서명 시크릿 키 |
| `AUTH_DATABASE_URL` | 인증 DB PostgreSQL 연결 URL |

---

## 기본 계정

| 항목 | 값 |
|------|----|
| 관리자 ID | `root` |
| 관리자 PW | `root` |
| 비밀번호 초기화 값 | `0000` |