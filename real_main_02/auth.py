# real_main_02/auth.py
import datetime, os
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel # pydantic은 데이터 검증과 설정관리를 쉽게 해주는 라이브러리임. 핵심: type을 검사하고 보장해줌. 왜 필요?파이썬은 타입 검사가 느슨해서.근데 api는 같은데서는 정확한 타입이 중요함
from passlib.hash import bcrypt
import jwt
from sqlalchemy import text
from sqlalchemy.orm import Session
from db_info04 import SessionAuth
from db_info04 import get_auth_db_url

SECRET = os.getenv("JWT_SECRET", "supersecret") #보안 위해 환경변수 사용,없으면 supersecret사용
router = APIRouter(prefix="/auth", tags=["auth"]) # 인증 관련 api만 따로 쓰는 라우터 객체를 만드는 코드. prefix="/auth" 자동으로 붙는거임. tags는 자동 생성되는 swagger 문서에서 이 그룹을 auth 탭으로 묶어 보여줌
bearer_scheme = HTTPBearer() # 토큰을 자동으로 꺼내주는 fastapi 보안도구 (토큰: 로그인 성공후 발급하는 권한 증명서)

# 입력 스키마
class UserIn(BaseModel): # 타입검사 도구. username, password가 문자열인지 체크,
    username: str # 데이터 검증용
    password: str

class PasswordResetIn(BaseModel):
    username: str
    new_Password: str

# DB 세션 획득
def get_db() -> Session: #get_db() 함수가 Session 타입을 반환한다는 뜻.
    from db_info04 import SessionAuth  # <- 이 줄을 함수 안에 넣자! ★★★
    if SessionAuth is None: #SessionAuth는 DB연결을 해주는 객체
        raise HTTPException(500, "AUTH DB 세션이 초기화되지 않았습니다.")
    db = SessionAuth()
    try:
        yield db
    finally:
        db.close()

# ─ 회원가입 ─────────────────────────────────────
@router.post("/signup", status_code=201) #201은 성공시 이 코드를 보내주겠다는 말임
def signup(user: UserIn, db: Session = Depends(get_db)):
    # 중복 체크
    exists = db.execute(
        text("SELECT 1 FROM users WHERE username = :u").bindparams(u=user.username) #보안상 위험 때문에 =:u.bindparms... 이거 쓴다고함
    ).first()
    if exists:
        raise HTTPException(409, "이미 존재하는 아이디")

    # 비밀번호 해시 저장
    hashed = bcrypt.hash(user.password)
    db.execute(
        text("INSERT INTO users (username, password) VALUES (:u, :p)")
        .bindparams(u=user.username, p=hashed)
    )
    db.commit()
    return {"msg": "가입 완료"}

# ─ 로그인 ───────────────────────────────────────
@router.post("/login")
def login(user: UserIn, db: Session = Depends(get_db)):
    if user.username=="root" and user.password=="root":
        payload={
            "sub": "admin",
            "role": "admin",  # 추가: 관리자 여부
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, SECRET, algorithm="HS256")
        return {"access_token": token, "token_type": "bearer"}
    row = db.execute(
        text("SELECT id, password FROM users WHERE username = :u")
        .bindparams(u=user.username)
    ).first()

    if not row or not bcrypt.verify(user.password, row.password):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호 오류")

    payload = {
        "sub": row.id,
        "role":"user",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}

# ─ 현재 사용자 확인 ────────────────────────────
def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    try:
        data = jwt.decode(cred.credentials, SECRET, algorithms=["HS256"])
        return data["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰 만료")

#────────────────────────────────────────────────────────
#새 비밀번호 설정하기, 아이디만 알면 됨
@router.post("/reset-password")
def reset_password(data: PasswordResetIn, db: Session = Depends(get_db)):
    # 유저 존재 여부 확인
    row = db.execute(
        text("SELECT id FROM users WHERE username = :u")
        .bindparams(u=data.username)
    ).first()

    if not row:
        raise HTTPException(status_code=404, detail="존재하지 않는 사용자입니다.")

    # 새 비밀번호 해시
    new_hashed = bcrypt.hash(data.new_Password)

    # DB 업데이트
    db.execute(
        text("UPDATE users SET password = :p WHERE username = :u")
        .bindparams(p=new_hashed, u=data.username)
    )
    db.commit()

    return {"msg": "비밀번호가 성공적으로 변경되었습니다."}
