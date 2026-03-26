# imageSolution2

AIMS(Asset & Image Management System) 환경에서 PostgreSQL DB에 저장된 디바이스 이미지를 조회하고 아티클 데이터를 관리하는 풀스택 웹 애플리케이션입니다.

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | FastAPI (Python 3.11), SQLAlchemy 2.0, Uvicorn |
| Frontend | Next.js 15 (React 19), TypeScript, Tailwind CSS 4 |
| 인증 | JWT (PyJWT), bcrypt |
| 이미지 처리 | base64 + zlib 압축 해제 |
| 데이터베이스 | PostgreSQL × 3 (CORE, PORTAL, AUTH) |
| 배포 | Render.com (`imagesolution2.onrender.com`) |

---

## 프로젝트 구조

```
imageSolution2/
├── real_main_02/             # FastAPI 백엔드
│   ├── api_main.py           # FastAPI 앱 진입점 (이미지 API, DB 설정 엔드포인트)
│   ├── auth.py               # 로그인 / 회원가입 / 비밀번호 변경
│   ├── admin.py              # 사용자 관리 (목록, 초기화, 삭제)
│   ├── dbconnection.py       # DB 연결 정보 CRUD + 일괄 업로드
│   ├── db_info04.py          # SQLAlchemy 엔진 관리 (CORE / PORTAL / AUTH)
│   ├── main04.py             # PyQt5 GUI + FastAPI 동시 실행 모드
│   └── ui_basic04.py         # PyQt5 로그 뷰어
│
├── frontend/                 # Next.js 프론트엔드
│   └── app/
│       ├── login/            # 로그인
│       ├── signup/           # 회원가입
│       ├── reset-password/   # 비밀번호 재설정
│       ├── server_config/    # DB 서버 연결 선택 화면
│       ├── image/all2_b/     # 메인 이미지 갤러리 뷰어
│       └── admin/
│           ├── user/         # 사용자 관리
│           └── dbconnection/ # DB 연결 관리
│
├── Dockerfile
├── requirements.txt
└── Makefile
```

---

## 핵심 동작 흐름

### 1. DB 서버 설정 (`/server_config`)

로그인 후 첫 번째로 거치는 화면입니다.

- AUTH DB(`dbconnection` 테이블)에 저장된 연결 목록을 드롭다운으로 보여줌
- DB명 / 호스트 / 메모로 필터링 가능
- 연결 선택 → `POST /set_server` 호출 → 백엔드가 AIMS_CORE_DB + AIMS_PORTAL_DB 접속 테스트 후 SQLAlchemy 엔진 초기화
- 연결 성공 시 `/image/all2_b` 로 이동
- 관리자는 "관리자 페이지로 이동" 버튼도 표시됨

### 2. 이미지 갤러리 (`/image/all2_b`)

메인 화면으로, 좌우 분할 레이아웃입니다.

**왼쪽 패널 (태그 목록)**
- `GET /api/image/list` 로 페이지네이션된 데이터 조회
- AIMS_CORE_DB(`enddevice`, `content`)와 AIMS_PORTAL_DB(`end_device_articles`, `article`)를 조인해 반환
- Code / State / Article ID / 수정일시 / 이미지 유무 컬럼
- 검색 필터:
  - Code 검색 (`q`)
  - Article ID 검색 (`aq`)
  - State 필터 (`SUCCESS` / `TIMEOUT` / `UNASSIGNED`)
- 하단 고정 페이지네이션 (10 / 20 / 50 / 전체)

**오른쪽 패널 (상세 정보)**
- 행 클릭 시 `GET /api/image/by-code/{code}` 호출 → 이미지 로드 (클라이언트 캐시 적용)
- 이미지: DB에 zlib 압축 + base64 인코딩된 데이터를 백엔드에서 복원해 반환
- article_data를 JSON 에디터로 표시
- **관리자 전용**: JSON 수정 후 저장 버튼 → `POST /articles` (외부 API 프록시) 로 전송

**드래그**: 가운데 경계선을 드래그해 좌우 패널 너비 조절 가능

### 3. DB 연결 관리 (`/admin/dbconnection`)

관리자만 접근 가능합니다.

- **DB 추가 폼**: username / password / database / host / port / memo 입력 → 백엔드에서 실제 접속 테스트 후 저장
- **목록 + 삭제**: 저장된 연결 정보 테이블, 검색 필터, 삭제 버튼
- **Excel/CSV 일괄 업로드**: 아래 컬럼 형식의 파일 업로드로 대량 등록 가능

  ```
  username | password | database | host | port | memo
  ```

---

## 데이터베이스 구성

| DB | 연결 방식 | 용도 | 주요 테이블 |
|----|-----------|------|------------|
| AIMS_CORE_DB | 런타임에 `/set_server`로 동적 설정 | 디바이스 상태 + 이미지 원본 | `enddevice`, `content` |
| AIMS_PORTAL_DB | CORE와 동일 호스트/포트 | 아티클 연결 정보 | `end_device_articles`, `article` |
| AUTH_DB | 환경변수 `AUTH_DATABASE_URL` (Render.com 고정) | 사용자 계정, DB 연결 목록 저장 | `users`, `dbconnection` |

---

## API 엔드포인트

### 서버 설정
| Method | Path | 설명 |
|--------|------|------|
| `POST` | `/set_server` | `{ host, port }` 로 CORE/PORTAL DB 연결 초기화 |
| `POST` | `/disconnect_db` | 현재 DB 연결 해제 |

### 이미지
| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/api/image/list` | 이미지 목록 (`page`, `per_page`, `q`, `aq`, `status`) |
| `GET` | `/api/image/by-code/{code}` | 특정 코드의 이미지 (base64 반환) |
| `POST` | `/articles` | 외부 API(`1.220.2.154:15988`) 프록시 |

### 인증 (`/auth`)
| Method | Path | 설명 |
|--------|------|------|
| `POST` | `/auth/signup` | 회원가입 |
| `POST` | `/auth/login` | 로그인 → JWT 토큰 반환 |
| `POST` | `/auth/reset-password` | 비밀번호 변경 |

### 관리자 (`/admin`)
| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/admin/user` | 사용자 목록 |
| `POST` | `/admin/reset-password` | 비밀번호 `0000` 으로 초기화 |
| `DELETE` | `/admin/delete-user` | 사용자 삭제 |
| `GET` | `/admin/dbconnections` | 저장된 DB 연결 목록 |
| `POST` | `/admin/add-dbconnection` | DB 연결 추가 (접속 테스트 포함) |
| `DELETE` | `/admin/delete-dbconnection/{id}` | DB 연결 삭제 |
| `POST` | `/admin/bulk-upload-dbconnections` | Excel/CSV 일괄 업로드 |

---

## 실행 방법

### 백엔드

```bash
# 서버 전용
uvicorn real_main_02.api_main:fastapi_app --host 0.0.0.0 --port 8000

# Makefile
make run

# PyQt5 데스크탑 앱 + 서버 동시 실행
python real_main_02/main04.py
```

### 프론트엔드

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

### Docker

```bash
docker build -t imagesolution2 .
docker run -p 8000:8000 imagesolution2
```

---

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `JWT_SECRET` | JWT 서명 키 | `supersecret` |
| `AUTH_DATABASE_URL` | 인증/연결정보 저장 DB URL | Render.com 고정 URL |

---

## 기본 계정

| 구분 | ID | PW |
|------|----|----|
| 관리자 (하드코딩) | `root` | `root` |
| 비밀번호 초기화 기본값 | - | `0000` |