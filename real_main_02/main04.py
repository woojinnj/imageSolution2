# main04.py
import sys
import os
import logging
import threading
import zlib
import base64
import signal
import fastapi
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QAction, QMenu
from PyQt5.QtGui import QIcon
from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.orm import declarative_base, sessionmaker
import db_info04
import platform
from ui_basic04 import LogViewer, QTextEditLogger
from ui_dbinfo_mod04 import Mainwindow
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from fastapi.responses import RedirectResponse
import webbrowser
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
from fastapi import FastAPI
from real_main_02.auth import router as auth_router
from db_info04 import update_auth_engine
from real_main_02.admin import router as admin_router
from real_main_02.dbconnection import router as dbconnection_router

fastapi_app = FastAPI()
update_auth_engine()

fastapi_app.include_router(auth_router)
fastapi_app.include_router(admin_router)  # ← 등록
fastapi_app.include_router(dbconnection_router)


def graceful_exit(*args):
    if db_info04.engine:
        db_info04.engine.dispose()
        logging.info("CORE DB 엔진 종료")
    if db_info04.portal_engine:
        db_info04.portal_engine.dispose()
        logging.info("PORTAL DB 엔진 종료")
    sys.exit(0)


# 종료 시그널 핸들링 등록
signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)


class DataItem(BaseModel):
    stationCode: str
    id: str
    name: Optional[str]
    nfc: Optional[str]
    data: Dict[str, Optional[Any]]


class DataListPayload(BaseModel):
    dataList: List[DataItem]  # 여기에 저장


from fastapi.middleware.cors import CORSMiddleware

# ← 이 블록을 fastapi_app 생성 직후에 넣어 줍니다.
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js 개발 서버 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base = declarative_base()

metadata = None
enddevice = None
content = None


# db 연결 정보 수정시 호출 되는 함수
def init_db_tables():
    """
    DB 연결 정보가 설정된 후에 호출되어, 데이터베이스 스키마를 불러오고
    enddevice와 content 테이블 객체를 생성합니다.
    """
    global metadata, enddevice, content
    from db_info04 import engine
    if engine is None:
        raise HTTPException(status_code=500, detail="CORE DB 엔진이 초기화되지 않았습니다.")
    metadata = MetaData(schema="public")
    metadata.reflect(bind=engine)
    enddevice = Table("enddevice", metadata, autoload_with=engine)
    content = Table("content", metadata, autoload_with=engine)
    logging.info("DB 테이블 초기화 완료")


def get_db():
    if db_info04.Session is None:
        raise HTTPException(status_code=500, detail="DB 연결 정보가 설정되지 않았습니다. 먼저 서버 설정을 진행하세요.")
    db = db_info04.Session()
    try:
        yield db
    finally:
        db.close()
        logging.info("AIMS_CORE_DB 세션 종료")


class ServerInfo(BaseModel):
    host: str
    port: str


@fastapi_app.post("/disconnect_db", response_class=JSONResponse)
def disconnect_db():
    db_info04.engine = None
    db_info04.Session = None
    db_info04.portal_engine = None
    db_info04.SessionPortal = None
    logging.info("DB 연결이 해제되었습니다.")

    return JSONResponse(content={"status": "disconnected", "message": "DB 연결이 정상적으로 해제되었습니다."})


# set_server 엔드포인트 (DB 정보를 업데이트하고 DB 테이블을 초기화)
from sqlalchemy.exc import OperationalError


# server_config 에서 받은 host, port를 실제로 설정하는 부분
@fastapi_app.post("/set_server", response_class=JSONResponse)
def set_server(info: ServerInfo):
    if not info.port.isdigit():
        raise HTTPException(status_code=400, detail="포트 값은 숫자로 입력해 주세요.")

    # 잠시 별도로 값을 저장
    test_db_info_core = {
        "username": "aims",
        "password": "aims",
        "host": info.host,
        "port": info.port,
        "database": "AIMS_CORE_DB"
    }
    test_db_info_portal = {
        "username": "aims",
        "password": "aims",
        "host": info.host,
        "port": info.port,
        "database": "AIMS_PORTAL_DB"
    }

    #  테스트
    test_url_core = f'postgresql://{test_db_info_core["username"]}:{test_db_info_core["password"]}@{test_db_info_core["host"]}:{test_db_info_core["port"]}/{test_db_info_core["database"]}'
    test_url_portal = f'postgresql://{test_db_info_portal["username"]}:{test_db_info_portal["password"]}@{test_db_info_portal["host"]}:{test_db_info_portal["port"]}/{test_db_info_portal["database"]}'

    try:
        test_engine_core = create_engine(test_url_core)
        with test_engine_core.connect() as conn:
            conn.execute(text("SELECT 1"))

        test_engine_portal = create_engine(test_url_portal)
        with test_engine_portal.connect() as conn:
            conn.execute(text("SELECT 1"))

    except OperationalError as e:
        logging.error(f"DB 접속 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "DB 접속 실패. 서버 주소나 포트를 확인해 주세요."}
        )

    # 실제 연결
    db_info04.db_info_core["host"] = info.host
    db_info04.db_info_core["port"] = info.port
    db_info04.db_info_portal["host"] = info.host
    db_info04.db_info_portal["port"] = info.port

    db_info04.update_engine()
    db_info04.update_portal_engine()
    init_db_tables()

    logging.info(f"DB 연결 성공 및 설정 완료: {info.host}:{info.port}")
    return JSONResponse(content={"status": "success", "message": "DB 연결 성공"})


class EditableArticle(BaseModel):
    article_id: str
    article_data: Dict[str, Optional[Any]]


@fastapi_app.post("/articles", response_class=JSONResponse)
async def proxy_save_articles(payload: DataListPayload):
    # 외부 15988
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.post(
            "http://1.220.2.154:15988/articles",
            json=payload.model_dump()  # 또는 payload.dict()
        )
    return JSONResponse(
        status_code=res.status_code,
        content=res.text
    )


from fastapi.responses import JSONResponse


@fastapi_app.get("/api/image/by-code/{code}", response_class=JSONResponse)
def get_image_by_code(code: str, db: db_info04.Session = Depends(get_db)):
    sql = text("""
        SELECT DISTINCT ON (SPLIT_PART(code,'-',1)) content
        FROM public.content
        WHERE type = 'IMAGE' AND SPLIT_PART(code,'-',1)=:code
        ORDER BY SPLIT_PART(code,'-',1), id DESC
        LIMIT 1
    """)
    result = db.execute(sql, {"code": code}).fetchone()

    if not result or not result[0]:
        return {"image_base64": ""}

    try:
        decoded = base64.b64decode(result[0])
        decompressed = zlib.decompress(decoded)
        image_base64 = base64.b64encode(decompressed).decode("utf-8")
        return {"image_base64": image_base64}
    except Exception as e:
        logging.error(f"이미지 디코딩 실패 ({code}): {e}")
        return {"image_base64": ""}


@fastapi_app.get("/api/image/list", response_class=JSONResponse)
def get_image_list(
        page: int = 1,
        per_page: int = 10,
        q: str = "",
        status: str = "",
        aq: str = "",
        db: db_info04.Session = Depends(get_db)
):
    if db_info04.SessionPortal is None:
        raise HTTPException(status_code=500, detail="PORTAL DB 세션이 초기화되지 않았습니다.")

    # AIMS_CORE_DB 쿼리
    offset = (page - 1) * per_page
    core_sql = text("""
        WITH latest_enddevice AS (
            SELECT DISTINCT ON (code) *
            FROM public.enddevice
            ORDER BY code, id DESC
        ),
        latest_content AS (
            SELECT DISTINCT ON (SPLIT_PART(code, '-', 1)) *
            FROM public.content
            WHERE "type" = 'IMAGE'
            ORDER BY SPLIT_PART(code, '-', 1), id DESC
        )
        SELECT e.state, e.code, c.content
        FROM latest_enddevice e
        LEFT JOIN latest_content c
            ON e.code = SPLIT_PART(c.code, '-', 1)
        WHERE (:q = '' OR e.code ILIKE '%' || :q || '%')
          AND (:status = '' OR e.state = :status)
        ORDER BY e.id
        LIMIT :limit OFFSET :offset
    """)
    core_params = {"q": q, "status": status, "limit": per_page, "offset": offset}
    core_results = db.execute(core_sql, core_params).fetchall()

    # 전체 수
    count_sql = text("""
        SELECT COUNT(*) FROM public.enddevice e
        WHERE (:q = '' OR e.code ILIKE '%' || :q || '%')
          AND (:status = '' OR e.state = :status)
    """)
    total_rows = db.execute(count_sql, {"q": q, "status": status}).scalar()

    # AIMS_PORTAL_DB 쿼리
    codes = [row[1] for row in core_results]
    portal_session = db_info04.SessionPortal()
    sql_portal = text("""
        SELECT eda.label_code, eda.article_id, art.last_modified, art.data
        FROM public.end_device_articles eda
        JOIN public.article art ON eda.article_id = art.article_id
        WHERE eda.label_code = ANY(:codes)
          AND (:aq = '' OR eda.article_id ILIKE '%' || :aq || '%')
    """)
    portal_params = {"codes": codes, "aq": aq}
    portal_results = portal_session.execute(sql_portal, portal_params).fetchall()
    portal_session.close()

    article_map = {
        row[0]: {
            "article_id": row[1],
            "last_modified": row[2].strftime('%Y-%m-%d %H:%M:%S') if row[2] else None,
            "data": json.loads(row[3]) if isinstance(row[3], str) else row[3]
        }
        for row in portal_results
    }

    result_list = []
    for state, ed_code, content in core_results:
        article = article_map.get(ed_code, {})

        if aq and not article:
            continue

        image_data = ""
        if content and content != "string":
            try:
                decoded = base64.b64decode(content)
                decompressed = zlib.decompress(decoded)
                image_data = base64.b64encode(decompressed).decode("utf-8")
            except Exception as e:
                logging.error(f"이미지 처리 실패 ({ed_code}): {e}")

        result_list.append({
            "code": ed_code,
            "state": state,
            "article_id": article.get("article_id", "N/A"),
            "last_modified": article.get("last_modified", "N/A"),
            "article_data": article.get("data", "N/A"),
            "has_image": bool(content and content.strip() and content != "string")
        })

    return {
        "page": page,
        "per_page": per_page,
        "total": total_rows,
        "results": result_list
    }


# PyQt 메인 함수 (단 한 번만 실행)
if __name__ == "__main__":

    if not QtWidgets.QApplication.instance():
        qt_app = QtWidgets.QApplication(sys.argv)


    def on_focus_changed(old_widget, new_widget):
        if not viewer.isVisible():
            viewer.show()


    qt_app.focusChanged.connect(on_focus_changed)

    path = os.path.join(os.path.dirname(sys.modules[__name__].__file__),
                        '/Users/woojin/Desktop/test/imageSolution/images/moonicon.png')
    qt_app.setWindowIcon(QIcon(path))

    viewer = LogViewer(app=fastapi_app)
    db_window = Mainwindow()

    viewer.setWindowTitle("로그뷰어")

    db_window.setWindowTitle("DB CONNECTION SETTINGS")

    tray_icon = QSystemTrayIcon(QIcon(path), qt_app)
    tray_menu = QMenu()

    restore_action = QAction("창 열기", viewer)
    restore_action.triggered.connect(viewer.show)

    quit_action = QAction("종료", viewer)
    quit_action.triggered.connect(lambda: graceful_exit())  # graceful_exit() 호출

    db_mod_open_action = QAction("db연결 수정", viewer)
    db_mod_open_action.triggered.connect(db_window.show)

    tray_menu.addAction(restore_action)
    tray_menu.addAction(db_mod_open_action)
    tray_menu.addAction(quit_action)
    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()

    viewer.show()
    sys.exit(qt_app.exec_())
