from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from passlib.hash import bcrypt
from real_main_02.db_info04 import update_auth_engine
from fastapi import Query

router = APIRouter(prefix="/admin", tags=["admin"])
update_auth_engine()

# 기본 비밀번호
DEFAULT_PASSWORD = "0000"

def get_db():
    from real_main_02.db_info04 import SessionAuth
    if SessionAuth is None:
        raise HTTPException(500, "AUTH DB 세션이 초기화되지 않았습니다.")
    db = SessionAuth()
    try:
        yield db
    finally:
        db.close()

# 🔁 사용자 목록 조회
@router.get("/user")
def get_users(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT username, password FROM users"))
    rows = result.fetchall()
    return {
        "users": [{"id": row[0], "password": row[1]} for row in rows]
    }

# 🔁 비밀번호 초기화: 0000으로 변경
@router.post("/reset-password")
def reset_to_default_password(username: str, db: Session = Depends(get_db)):
    user = db.execute(text("SELECT id FROM users WHERE username = :u").bindparams(u=username)).first()
    if not user:
        raise HTTPException(404, detail="존재하지 않는 사용자입니다.")

    hashed = bcrypt.hash(DEFAULT_PASSWORD)
    db.execute(
        text("UPDATE users SET password = :p WHERE username = :u")
        .bindparams(p=hashed, u=username)
    )
    db.commit()
    return {"msg": f"{username}의 비밀번호가 기본값(0000)으로 초기화되었습니다."}
@router.delete("/delete-user")
def delete_user(username: str = Query(...), db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT id FROM users WHERE username = :u").bindparams(u=username)
    ).first()

    if not row:
        raise HTTPException(404, detail="사용자가 존재하지 않습니다.")

    db.execute(
        text("DELETE FROM users WHERE username = :u").bindparams(u=username)
    )
    db.commit()

    return {"msg": f"{username} 계정이 삭제되었습니다."}