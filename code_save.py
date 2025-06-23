import sys
import os
import logging
import threading
import zlib
import base64
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QAction, QMenu
from PyQt5.QtGui import QIcon
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.orm import declarative_base, sessionmaker
from db_info04 import engine, Session  # AIMS_CORE_DB 연결
from db_info04 import engine_portal, SessionPortal  # AIMS_PORTAL_DB 연결
import platform
from ui_basic04 import LogViewer, QTextEditLogger
from ui_dbinfo_mod04 import Mainwindow

# SQLAlchemy 및 데이터베이스 설정
Base = declarative_base()
metadata = MetaData(schema="public")
metadata.reflect(bind=engine)

enddevice = Table("enddevice", metadata, autoload_with=engine)
content = Table("content", metadata, autoload_with=engine)
# 필요에 따라 enddevice, content 테이블의 컬럼을 확인 가능:
# print(enddevice.columns.keys())
# print(content.columns.keys())

# FastAPI 애플리케이션 생성
fastapi_app = FastAPI()

def get_db():
    """SQLAlchemy 세션을 최신 엔진과 연결된 상태로 제공 (AIMS_CORE_DB)"""
    db = Session()
    try:
        yield db
    finally:
        db.close()
        print("AIMS_CORE_DB close 성공")

@fastapi_app.get("/")
def read_root():
    logging.info("메인 화면에 접속했습니다.")
    return {"message": "메인 화면 입니다!"}


@fastapi_app.get("/image/all2", response_class=HTMLResponse)
def get_all_images2(
        page: int = 1,
        per_page: int = 10,
        q: str = "",  # 검색어
        status: str = "",  # 상태 필터 (예: SUCCESS, TIMEOUT, UNASSIGNED)
        aq:str="", #article 검색어
        db: Session = Depends(get_db)
):
    offset = (page - 1) * per_page

    # AIMS_CORE_DB에서 enddevice와 content 데이터를 조인하는 SQL
    sql = text("""
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
        SELECT 
            e.state, 
            e.code,
            c.id,
            c.code,
            c."content"
        FROM latest_enddevice e
        LEFT JOIN latest_content c
            ON e.code = SPLIT_PART(c.code, '-', 1)
        WHERE (:q = '' OR e.code ILIKE '%' || :q || '%')
          AND (:status = '' OR e.state = :status)
        ORDER BY e.id
        LIMIT :limit OFFSET :offset
    """)
    params = {"q": q, "status": status, "offset": offset, "limit": per_page}
    core_results = db.execute(sql, params).fetchall()

    # 전체 행 수 조회 (페이징 처리를 위해)
    count_sql = text("""
        SELECT COUNT(*)
        FROM public.enddevice e
        WHERE (:q = '' OR e.code ILIKE '%' || :q || '%')
          AND (:status = '' OR e.state = :status)
    """)
    total_rows = db.execute(count_sql, {"q": q, "status": status}).scalar()
    total_pages = (total_rows // per_page) + (1 if total_rows % per_page > 0 else 0)

    # AIMS_CORE_DB 결과에서 코드 목록 추출
    codes = [row[1] for row in core_results]

    # AIMS_PORTAL_DB에서 해당 코드에 대한 article_id 조회
    portal_session = SessionPortal()
    sql_portal = text("""
            SELECT eda.label_code, eda.article_id, art.last_modified, art.data
            FROM public.end_device_articles eda
            JOIN public.article art ON eda.article_id = art.article_id
            WHERE eda.label_code = ANY(:codes)
        """)
    portal_results = portal_session.execute(sql_portal, {"codes": codes}).fetchall()
    portal_session.close()

    article_map = {
        row[0]: {"article_id": row[1], "last_modified": row[2], "data": row[3]}
        for row in portal_results
    }

    if core_results:
        html = "<div class='image-gallery'>"
        for state, ed_code, _, _, content in core_results:
            article_info = article_map.get(ed_code, None)
            if article_info:
                article_id = article_info.get("article_id", "N/A")
                last_modified = article_info.get("last_modified", "N/A")
                article_data = article_info.get("data", "N/A")
            else:
                article_id = "N/A"
                last_modified = "N/A"
                article_data = "N/A"

            encoded_image = ""
            if content is not None and content != "string":
                try:
                    decoded = base64.b64decode(content)
                    decompressed = zlib.decompress(decoded)
                    encoded_image = base64.b64encode(decompressed).decode('utf-8')
                except Exception as e:
                    logging.error(f"이미지 처리 에러(code={ed_code}): {e}")
                    encoded_image = ""
            html += f"""
                <div class="image-container" style="margin-bottom:20px;">
                    <h2 onclick="toggleBoth(this)">
                        Code: {ed_code} (State: {state}) Article: {article_id} LastModified: {last_modified}
                    </h2>
                    <div class="article-data" style="display:none; font-size:10px; margin-top:5px;">
                        Data: {article_data}
                    </div>
                    <img data-src="data:image/jpeg;base64,{encoded_image}" alt="Image-{ed_code}" style="max-width:300px; display:none;">
                </div>
            """
        html += "</div>"
    else:
        html = "<div class='image-gallery'><h2>검색 결과가 없습니다.</h2></div>"

    # 페이징 및 검색 관련 HTML (자바스크립트 포함)
    pagination_html = f"""
    <div class="pagination">
        {"<button onclick='goToPage(1)'>«</button>" if page > 1 else ""}
        {"<button onclick='goToPage({page - 1})'>‹</button>" if page > 1 else ""}
        <span>페이지 {page} / {total_pages}</span>
        <select id="per-page" class="per-page-select" onchange="changePerPage()">
            <option value="10" {"selected" if per_page == 10 else ""}>10개씩 보기</option>
            <option value="20" {"selected" if per_page == 20 else ""}>20개씩 보기</option>
            <option value="50" {"selected" if per_page == 50 else ""}>50개씩 보기</option>
            <option value="{total_rows}" {"selected" if per_page == total_rows else ""}>전체 보기</option>
        </select>
        {"<button onclick='goToPage({page + 1})'>›</button>" if page < total_pages else ""}
        {"<button onclick='goToPage({total_pages})'>»</button>" if page < total_pages else ""}
    </div>
    """

    full_html = f"""
    <html>
        <head>
            <title>갤러리 (페이지 {page})</title>
            <style>
                .image-gallery {{
                    display: flex;
                    flex-direction: column;
                    gap: 0px;
                    padding: 5px;
                    justify-content: flex-start;
                }}
                .image-container {{
                    width: 100%;
                    text-align: left;
                    font-size: 12px;
                    margin: 0;
                }}
                .pagination {{
                    position: fixed;
                    bottom: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                    display: flex;
                    gap: 10px;
                    background: rgba(255, 255, 255, 0.9);
                    padding: 5px 10px;
                    border-radius: 5px;
                    box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
                }}
                .per-page-select {{
                    font-size: 14px;
                    padding: 2px;
                    border-radius: 3px;
                    border: 1px solid #ccc;
                }}
                .search-container {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 10px;
                    margin: 20px auto;
                    width: fit-content;
                }}
            </style>
            <script>
                function goToPage(page) {{
                    let query = document.getElementById("search-box").value;
                    let status = document.getElementById("status-select").value;
                    window.location.href = `/image/all2?q=${{query}}&status=${{status}}&page=${{page}}&per_page={per_page}`;
                }}
                function changePerPage() {{
                    let selectedPerPage = document.getElementById("per-page").value;
                    let query = document.getElementById("search-box").value;
                    let status = document.getElementById("status-select").value;
                    window.location.href = `/image/all2?q=${{query}}&status=${{status}}&page=1&per_page=${{selectedPerPage}}`;
                }}
                function searchImages() {{
                    let query = document.getElementById("search-box").value;
                    let status = document.getElementById("status-select").value;
                    window.location.href = `/image/all2?q=${{query}}&status=${{status}}&page=1&per_page={per_page}`;
                }}
                function toggleBoth(element) {{
                    var container = element.parentElement;
                    var dataDiv = container.querySelector(".article-data");
                    if (dataDiv) {{
                        dataDiv.style.display = (dataDiv.style.display === "none" || dataDiv.style.display === "") ? "block" : "none";
                    }}
                    var img = container.querySelector("img");
                    if (img) {{
                        if (!img.getAttribute('src')) {{
                            img.src = img.getAttribute('data-src');
                            console.log("Image loaded " + img.src);
                        }}
                        img.style.display = (img.style.display === "none" || img.style.display === "") ? "block" : "none";
                    }}
                }}
            </script>
        </head>
        <body>
            <h1 style="text-align:center;">갤러리</h1>
            <div class="search-container">
                <input type="text" id="search-box" placeholder="Code 검색..." value="{q}" onkeyup="if(event.keyCode === 13) searchImages()">
                <select id="status-select" onchange="searchImages()">
                    <option value="" {"selected" if status == "" else ""}>전체</option>
                    <option value="SUCCESS" {"selected" if status == "SUCCESS" else ""}>SUCCESS</option>
                    <option value="TIMEOUT" {"selected" if status == "TIMEOUT" else ""}>TIMEOUT</option>
                    <option value="UNASSIGNED" {"selected" if status == "UNASSIGNED" else ""}>UNASSIGNED</option>
                </select>
                <button onclick="searchImages()">검색</button>
            </div>
            {html}
            {pagination_html}
        </body>
    </html>
    """

    logging.info(f"검색어 '{q}', 상태 '{status}' 적용 - 페이지 {page}")
    return HTMLResponse(content=full_html)


@fastapi_app.get("/image/all3_notusenow", response_class=HTMLResponse)
def get_all_images2(
        page: int = 1,
        per_page: int = 10,
        q: str = "",  # 검색어
        status: str = "",  # 상태 필터 (예: SUCCESS, TIMEOUT, UNASSIGNED)
        db: Session = Depends(get_db)
):
    offset = (page - 1) * per_page

    # AIMS_CORE_DB에서 enddevice와 content 데이터를 조인하는 SQL
    sql = text("""
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
        SELECT 
            e.state, 
            e.code,
            c.id,
            c.code,
            c."content"
        FROM latest_enddevice e
        LEFT JOIN latest_content c
            ON e.code = SPLIT_PART(c.code, '-', 1)
        WHERE (:q = '' OR e.code ILIKE '%' || :q || '%')
          AND (:status = '' OR e.state = :status)
        ORDER BY e.id
        LIMIT :limit OFFSET :offset
    """)
    params = {"q": q, "status": status, "offset": offset, "limit": per_page}
    core_results = db.execute(sql, params).fetchall()

    # 전체 행 수 조회 (페이징 처리를 위해)
    count_sql = text("""
        SELECT COUNT(*)
        FROM public.enddevice e
        WHERE (:q = '' OR e.code ILIKE '%' || :q || '%')
          AND (:status = '' OR e.state = :status)
    """)
    total_rows = db.execute(count_sql, {"q": q, "status": status}).scalar()
    total_pages = (total_rows // per_page) + (1 if total_rows % per_page > 0 else 0)

    # AIMS_CORE_DB 결과에서 코드 목록 추출
    codes = [row[1] for row in core_results]
    # print("Codes:", codes)

    # AIMS_PORTAL_DB에서 해당 코드에 대한 article_id 조회
    portal_session = SessionPortal()
    sql_portal = text("""
            SELECT eda.label_code, eda.article_id, art.last_modified, art.data
            FROM public.end_device_articles eda
            JOIN public.article art ON eda.article_id = art.article_id
            WHERE eda.label_code = ANY(:codes)
        """)
    portal_results = portal_session.execute(sql_portal, {"codes": codes}).fetchall()
    portal_session.close()
    # print("Portal results:", portal_results)  # portal_results 전체 출력

    article_map = {
        row[0]: {"article_id": row[1], "last_modified": row[2], "data": row[3]}
        for row in portal_results
    }  # print("Article map:", article_map)  # article_map 출력

    if core_results:
        html = "<div class='image-gallery'>"
        for state, ed_code, _, _, content in core_results:
            article_id = article_map.get(ed_code, None)
            encoded_image = ""
            if content is not None and content != "string":
                try:
                    decoded = base64.b64decode(content)
                    decompressed = zlib.decompress(decoded)
                    encoded_image = base64.b64encode(decompressed).decode('utf-8')
                except Exception as e:
                    logging.error(f"이미지 처리 에러(code={ed_code}): {e}")
                    encoded_image = ""
            html += f"""
                <div class="image-container" style="margin-bottom:20px;">
                    <h2 onclick="toggleImage(this)">
                        Code: {ed_code} (State: {state}) Article: {article_id or 'N/A'}
                    </h2>
                    <img data-src="data:image/jpeg;base64,{encoded_image}" alt="Image-{ed_code}" style="max-width:300px; display:none;">
                </div>
            """

        html += "</div>"
    else:
        html = "<div class='image-gallery'><h2>검색 결과가 없습니다.</h2></div>"

    # 페이징 및 검색 관련 HTML (자바스크립트 포함)
    # (여기서는 간단히 pagination_html 예시를 작성)
    pagination_html = f"""
    <div class="pagination">
        {"<button onclick='goToPage(1)'>&laquo;</button>" if page > 1 else ""}
        {"<button onclick='goToPage(" + str(page - 1) + ")'>&lt;</button>" if page > 1 else ""}
        <span>페이지 {page} / {total_pages}</span>
        <select id="per-page" class="per-page-select" onchange="changePerPage()">
            <option value="10" {"selected" if per_page == 10 else ""}>10개씩 보기</option>
            <option value="20" {"selected" if per_page == 20 else ""}>20개씩 보기</option>
            <option value="50" {"selected" if per_page == 50 else ""}>50개씩 보기</option>
            <option value="{total_rows}" {"selected" if per_page == total_rows else ""}>전체 보기</option>
        </select>
        {"<button onclick='goToPage(" + str(page + 1) + ")'>&gt;</button>" if page < total_pages else ""}
        {"<button onclick='goToPage(" + str(total_pages) + ")'>&raquo;</button>" if page < total_pages else ""}
    </div>
    """

    full_html = f"""
    <html>
        <head>
            <title>갤러리 (페이지 {page})</title>
            <style>

                .image-gallery {{
                    display: flex;
                    flex-direction: column;
                    gap: 0px;
                    padding: 5px;
                    justify-content: flex-start;
                }}
                .image-container {{
                    width: 100%;
                    text-align: left;
                    font-size: 12px; 
                    margin: 0; 

                }}
                .pagination {{
                    position: fixed;
                    bottom: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                    display: flex;
                    gap: 10px;
                    background: rgba(255, 255, 255, 0.9);
                    padding: 5px 10px;
                    border-radius: 5px;
                    box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
                }}
                .per-page-select {{
                    font-size: 14px;
                    padding: 2px;
                    border-radius: 3px;
                    border: 1px solid #ccc;
                }}
                .search-container {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 10px;
                    margin: 20px auto;
                    width: fit-content;
                }}
            </style>
            <script>
                function goToPage(page) {{
                    let query = document.getElementById("search-box").value;
                    let status = document.getElementById("status-select").value;
                    window.location.href = `/image/all2?q=${{query}}&status=${{status}}&page=${{page}}&per_page={per_page}`;
                }}
                function changePerPage() {{
                    let selectedPerPage = document.getElementById("per-page").value;
                    let query = document.getElementById("search-box").value;
                    let status = document.getElementById("status-select").value;
                    window.location.href = `/image/all2?q=${{query}}&status=${{status}}&page=1&per_page=${{selectedPerPage}}`;
                }}
                function searchImages() {{
                    let query = document.getElementById("search-box").value;
                    let status = document.getElementById("status-select").value;
                    window.location.href = `/image/all2?q=${{query}}&status=${{status}}&page=1&per_page={per_page}`;
                }}
                function toggleImage(element) {{
                    var container = element.parentElement;
                    var img = container.querySelector("img");
                    if (!img.getAttribute('src')) {{
                        img.src = img.getAttribute('data-src');
                        console.log("Image loaded " + img.src);
                    }}
                    img.style.display = (img.style.display === "none") ? "block" : "none";
                }}
            </script>
        </head>
        <body>
            <h1 style="text-align:center;">갤러리</h1>
            <div class="search-container">
                <input type="text" id="search-box" placeholder="Code 검색..." value="{q}" onkeyup="if(event.keyCode === 13) searchImages()">
                <select id="status-select" onchange="searchImages()">
                    <option value="" {"selected" if status == "" else ""}>전체</option>
                    <option value="SUCCESS" {"selected" if status == "SUCCESS" else ""}>SUCCESS</option>
                    <option value="TIMEOUT" {"selected" if status == "TIMEOUT" else ""}>TIMEOUT</option>
                    <option value="UNASSIGNED" {"selected" if status == "UNASSIGNED" else ""}>UNASSIGNED</option>
                </select>
                <button onclick="searchImages()">검색</button>
            </div>
            {html}
            {pagination_html}
        </body>
    </html>
    """

    logging.info(f"검색어 '{q}', 상태 '{status}' 적용 - 페이지 {page}")
    return HTMLResponse(content=full_html)

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
    quit_action.triggered.connect(qt_app.quit)

    db_mod_open_action = QAction("db연결 수정", viewer)
    db_mod_open_action.triggered.connect(db_window.show)

    tray_menu.addAction(restore_action)
    tray_menu.addAction(db_mod_open_action)
    tray_menu.addAction(quit_action)
    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()

    viewer.show()
    sys.exit(qt_app.exec_())


