from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from passlib.hash import bcrypt
from real_main_02.db_info04 import update_auth_engine
from fastapi import Query
from pydantic import BaseModel
from fastapi import Path
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from fastapi import UploadFile, File, APIRouter, Depends, HTTPException
import pandas as pd
router = APIRouter(prefix="/admin", tags=["관리자"])
update_auth_engine()


class DBConnectionCreateRequest(BaseModel):
    username: str
    password: str
    database: str
    host: str
    port: int
    memo: str = ""  # 기본값 지정 (선택사항일 경우) ""하면 선택사항임

def get_db():
    from real_main_02.db_info04 import SessionAuth
    if SessionAuth is None:
        raise HTTPException(500, "AUTH DB 세션이 초기화되지 않았습니다.")
    db = SessionAuth()
    try:
        yield db
    finally:
        db.close()


@router.get("/dbconnections")
def get_dbconnections(db: Session = Depends(get_db)):
    query = text("""
        SELECT id, username, "password", "database", host, port, memo
        FROM dbconnection
    """)
    result = db.execute(query)
    rows = result.fetchall()
    return {
        "dbconnections": [
            {
                "id": row[0],
                "username": row[1],
                "password": row[2],
                "database": row[3],
                "host": row[4],
                "port": row[5],
                "memo": row[6]
            }
            for row in rows
        ]
    }


@router.post("/add-dbconnection")
def add_dbconnection(req: DBConnectionCreateRequest, db: Session = Depends(get_db)):
    # 실제 연결 가능한지 테스트
    test_url = f'postgresql+psycopg://{req.username}:{req.password}@{req.host}:{req.port}/{req.database}'
    try:
        test_engine = create_engine(test_url)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))  # 간단한 테스트 쿼리
    except OperationalError as e:
        raise HTTPException(status_code=400, detail=f"DB 연결 실패: {str(e)}")

    # 중복 검사
    exists = db.execute(
        text("""
            SELECT id FROM dbconnection 
            WHERE host = :host AND port = :port AND database = :database
        """).bindparams(
            host=req.host,
            port=req.port,
            database=req.database
        )
    ).first() #첫번째 열만 가져오기

    if exists:
        raise HTTPException(400, detail="해당 DB 연결 정보가 이미 존재합니다.")

    # 실제 INSERT
    db.execute(
        text("""
            INSERT INTO dbconnection (username, "password", "database", host, port, memo)
            VALUES (:username, :password, :database, :host, :port, :memo)
        """).bindparams( #sql injection 방지 + 안전하게 값을 넣기 위해 사용
            username=req.username,
            password=req.password,
            database=req.database,
            host=req.host,
            port=req.port,
            memo=req.memo
        )
    )
    db.commit() #commit 에서 실제로 적용한, executet에서 담아놓은 것들...
    return {"msg": "DB 연결 성공 및 정보가 저장되었습니다."}

@router.delete("/delete-dbconnection/{id}")
def delete_dbconnection(
        id:int = Path(...,description="삭제할 dbconnection 의 db"),
        db:Session = Depends(get_db)
):
    result = db.execute(
        text("DELETE FROM dbconnection WHERE id = :id")
        .bindparams(id=id)
    )
    db.commit()
    if result.rowcount==0:
        raise HTTPException (404,detail="햬당 id의 DB연결 정보가 없음")
    return {"msg":"삭제 성공"}


@router.post("/bulk-upload-dbconnections")
async def bulk_upload_dbconnections(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.csv')):
        raise HTTPException(400, detail="xlsx 또는 csv 파일만 업로드 가능")

    if file.filename.endswith('.xlsx'):
        df = pd.read_excel(file.file)
    else:
        df = pd.read_csv(file.file)

    required_cols = {'username', 'password', 'database', 'host', 'port'}
    allowed_cols = required_cols | {'memo'}
    extra_cols = set(df.columns) - allowed_cols
    missing = required_cols - set(df.columns)

    if missing:
        raise HTTPException(
            400,
            detail=f"엑셀 파일에 다음 필수 컬럼이 없습니다: {', '.join(missing)}"
        )

    if extra_cols:
        raise HTTPException(
            400,
            detail=f"다음과 같은 불필요한 컬럼이 있습니다: {', '.join(extra_cols)}"
        )

    count = 0
    errors = []
    for idx, row in df.iterrows():
        try:
            port_val = int(str(row['port']).replace(",", ""))  # 콤마도 허용
            exists = db.execute(
                text("""
                    SELECT id FROM dbconnection
                    WHERE host = :host AND port = :port AND database = :database
                """).bindparams(
                    host=row['host'],
                    port=port_val,
                    database=row['database']
                )
            ).first()
            if exists:
                errors.append(f"{idx+2}행: 이미 존재해서 건너뜀")
                continue
            db.execute(
                text("""
                    INSERT INTO dbconnection (username, "password", "database", host, port, memo)
                    VALUES (:username, :password, :database, :host, :port, :memo)
                """).bindparams(
                    username=row['username'],
                    password=row['password'],
                    database=row['database'],
                    host=row['host'],
                    port=port_val,
                    memo=row.get('memo', '')
                )
            )
            count += 1
        except Exception as e:
            errors.append(f"{idx+2}행: 오류 - {str(e)} (port={row['port']})")
    db.commit()
    return {"msg": f"{count}개 연결정보 추가 완료", "errors": errors}
