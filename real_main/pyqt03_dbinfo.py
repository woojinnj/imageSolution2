from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, HTTPException, Depends


# PostgreSQL 연결 정보
db_info = {
    "username": "postgres",
    "password": "0000",
    "database": "postgres",
    "host": "localhost",
    "port": "5432",
    # "username": "1",
    # "password": "1",
    # "database": "1",
    # "host": "1",
    # "port": "1",
}


def get_db_url():
    """현재 db_info를 바탕으로 DB URL 생성"""
    return f"postgresql+psycopg://{db_info['username']}:{db_info['password']}@{db_info['host']}:{db_info['port']}/{db_info['database']}"


# SQLAlchemy 엔진 및 세션 생성
engine = create_engine(get_db_url(), echo=True)
Session = sessionmaker(bind=engine)




def update_engine():
    """DB 연결 정보 변경 시 엔진과 세션 갱신"""
    global engine, Session
    engine.dispose()
    engine = create_engine(get_db_url(), echo=True)
    Session = sessionmaker(bind=engine)
    print("db 정보 수정됨")
