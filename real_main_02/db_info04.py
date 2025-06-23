#db_info04.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.pool import NullPool


# PostgreSQL 연결 정보
db_info_core = {
    "username": "aims",
    "password": "aims",
    "database": "AIMS_CORE_DB",
    "host": "",
    "port": "",

}

def get_core_db_url():
    if not db_info_core["host"] or not db_info_core["port"]:
        raise HTTPException(status_code=500, detail="CORE DB 정보가 설정되지 않았습니다. 먼저 서버 설정을 진행하세요.")
    return f"postgresql+psycopg://{db_info_core['username']}:{db_info_core['password']}@{db_info_core['host']}:{db_info_core['port']}/{db_info_core['database']}"


engine = None
Session = None
# 1.220.2.154
# 15987

def update_engine():

    global engine, Session
    try:
        url = get_core_db_url()

        # 이전 엔진이 살아 있다면 커넥션 풀부터 정리
        if engine is not None:
            engine.dispose()


        engine = create_engine(
            url,
            echo=True,
            connect_args={"application_name": "py_tray_core"},
            pool_pre_ping=True,                         # 죽은 커넥션 감지
            pool_recycle=300,                           # 5 분마다 재연결

        )


        Session = sessionmaker(bind=engine)
        print("AIMS_CORE_DB 정보 업데이트 완료")

    except Exception as e:
        engine = None
        Session = None
        print("CORE DB 업데이트 실패:", e)

db_info_portal = {
    "username": "aims",
    "password": "aims",
    "database": "AIMS_PORTAL_DB",
    "host": "",
    "port": "",
}

def get_portal_db_url():
    if not db_info_portal["host"] or not db_info_portal["port"]:
        raise HTTPException(status_code=500, detail="PORTAL DB 정보가 설정되지 않았습니다. 먼저 서버 설정을 진행하세요.")
    return f"postgresql+psycopg://{db_info_portal['username']}:{db_info_portal['password']}@{db_info_portal['host']}:{db_info_portal['port']}/{db_info_portal['database']}"



engine_portal = None
SessionPortal = None

def update_portal_engine():
    global engine_portal, SessionPortal
    try:
        url = get_portal_db_url()

        #  이미 살아있는 엔진이 있으면 먼저 정리
        if engine_portal is not None:
            engine_portal.dispose()

        engine_portal = create_engine(
            url,
            echo=True,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={"application_name": "py_tray_portal"},

        )

        SessionPortal = sessionmaker(bind=engine_portal)
        print("AIMS_PORTAL_DB 정보 업데이트 완료")

    except Exception as e:
        engine_portal = None
        SessionPortal = None
        print("PORTAL DB 업데이트 실패:", e)

#--------------------------------------------------------------------------------------
db_info_auth = {
    "username": "postgres",      # ← 실제 로그인 계정
    "password": "0000",          # ← 비밀번호
    "database": "testdb01",      # ← 방금 만든 DB 이름
    "host": "localhost",
    "port": "5432",
}

def get_auth_db_url():
    info = db_info_auth
    return f"postgresql+psycopg://{info['username']}:{info['password']}@" \
           f"{info['host']}:{info['port']}/{info['database']}"

engine_auth = None
SessionAuth = None

def update_auth_engine():
    global engine_auth, SessionAuth
    url = get_auth_db_url()

    if engine_auth is not None:
        engine_auth.dispose()

    engine_auth = create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"application_name": "py_tray_auth"},
    )
    SessionAuth = sessionmaker(bind=engine_auth)
    print("AUTH_DB(testdb01) 엔진 업데이트 완료")

#-------------------------------------------------------------------------------------------

