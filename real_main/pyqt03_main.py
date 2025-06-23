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
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary
from sqlalchemy.orm import declarative_base, sessionmaker
from pyqt03_ui_basic import LogViewer  # 새로 만든 UI 파일 임포트
from pyqt03_ui_basic import QTextEditLogger
from pyqt03_dbinfo import engine, Session
import platform
from pyqt03_ui_dbinfo_mod import Mainwindow
from pyqt03_dbinfo import update_engine
import enum
from sqlalchemy.types import Enum

# SQLAlchemy 및 데이터베이스 설정
Base = declarative_base()

class StatusEnum(enum.Enum):
    processing = "processing"
    success = "success"
    failed = "failed"

class CompressedImage(Base):
    __tablename__ = 'compressed_images'
    id = Column(Integer, primary_key=True, autoincrement=True)
    image_name = Column(String, nullable=False)
    compressed_data = Column(LargeBinary, nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.processing)


# FastAPI 애플리케이션 생성
fastapi_app = FastAPI()


def get_db():
    """SQLAlchemy 세션을 최신 엔진과 연결된 상태로 제공"""
    db = Session()  # 최신 세션 객체 사용
    try:
        yield db
    finally:
        db.close()
        print("close 성공")


@fastapi_app.get("/")
def read_root():
    logging.info("메인 화면에 접속했습니다.")
    return {"message": "메인 화면 입니다!"}


@fastapi_app.get("/image/name/{image_name}")
def get_image_by_name_with_message(image_name: str, db: Session = Depends(get_db)):
    retrieved_image = db.query(CompressedImage).filter_by(image_name=image_name).first()
    if not retrieved_image:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")
    inflated_data = zlib.decompress(retrieved_image.compressed_data)
    original_data = base64.b64decode(inflated_data)
    encoded_image = base64.b64encode(original_data).decode('utf-8')

    html_content = f"""
    <html>
        <head><title>이미지 표시</title></head>
        <body>
            <h1>{image_name} 이미지</h1>
            <img src="data:image/jpeg;base64,{encoded_image}" alt="{image_name}">
        </body>
    </html>
    """
    logging.info("이름으로 이미지 검색하기.")
    return HTMLResponse(content=html_content)


@fastapi_app.get("/image/all2", response_class=HTMLResponse)
def get_all_images2(
        page: int = 1,
        per_page: int = 10,
        q: str = "",
        status: str = "",  # status 파라미터 추가
        db: Session = Depends(get_db)
):

    """
    검색, 페이지네이션, 상태 필터링이 적용된 이미지 갤러리 엔드포인트
    - q: 이미지 이름 검색어
    - status: 이미지 상태 필터 ('', 'processing', 'success', 'failed')
    """
    # 검색어 필터
    query = db.query(CompressedImage)
    if q:
        query = query.filter(CompressedImage.image_name.ilike(f"%{q}%"))
    # 상태 필터 (status 값이 전달된 경우)
    if status:
        query = query.filter(CompressedImage.status == status)

    total_images = query.count()
    total_pages = (total_images // per_page) + (1 if total_images % per_page > 0 else 0)
    all_images = query.offset((page - 1) * per_page).limit(per_page).all()

    if not all_images:
        return HTMLResponse(content=f"<h1>'{q}'와 상태 '{status}'에 해당하는 이미지가 없습니다.</h1>", status_code=404)

    all_image_names = [img.image_name for img in db.query(CompressedImage).all()]
    options_html = "".join(f'<option value="{name}">' for name in all_image_names)

    html_content = f"""
      <html>
        <head>
            <title>갤러리 (페이지 {page})</title>
            <style>
                .image-gallery {{
                    display: flex; flex-wrap: wrap; gap: 10px; padding: 30px; justify-content: center;
                }}
                .image-container {{
                    width: calc(12.5% - 10px); text-align: center;
                }}
                h2 {{
                    margin-bottom: 10px;
                }}
                img {{
                    width: 100%; height: auto;
                }}
                #search-box {{
                    width: 300px; padding: 10px; margin: 20px auto; display: block; font-size: 16px; 
                    border: 1px solid #ccc; border-radius: 5px;
                }}
                .pagination {{
                    position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
                    display: flex; gap: 10px; background: rgba(255, 255, 255, 0.9);
                    padding: 10px 20px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
                }}
                .pagination button {{
                    font-size: 16px; padding: 5px 10px; cursor: pointer; border: none;
                    background: #93a0ad; color: white; border-radius: 5px;
                }}
                .pagination button:hover {{
                    background: #7c8a99;
                }}
                .per-page-select {{
                    font-size: 14px; padding: 5px; border-radius: 5px; border: 1px solid #ccc;
                }}
                .search-container {{
                    display: flex; justify-content: center; align-items: center; gap: 10px;
                    margin: 20px auto; width: fit-content;
                }}
            </style>
            <script>
                function searchImages() {{
                    let query = document.getElementById("search-box").value;
                    let status = document.getElementById("status-select").value;
                    window.location.href = `/image/all2?q=${{query}}&status=${{status}}&page=1&per_page={per_page}`;
                }}
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
            </script>
        </head>
        <body>
        <h1>갤러리</h1>
        <div class="search-container">
            <input type="text" id="search-box" placeholder="이미지 검색..." list="image-list" value="{q}" onkeyup="if(event.keyCode === 13) searchImages()">
            <datalist id="image-list">
                {options_html}
            </datalist>
            <select id="status-select" onchange="searchImages()">
                <option value="" {"selected" if status == "" else ""}>전체</option>
                <option value="processing" {"selected" if status == "processing" else ""}>processing</option>
                <option value="success" {"selected" if status == "success" else ""}>success</option>
                <option value="failed" {"selected" if status == "failed" else ""}>failed</option>
            </select>
            <button onclick="searchImages()">검색</button>
        </div>
        <div class="image-gallery">
    """

    for image in all_images:
        inflated_data = zlib.decompress(image.compressed_data)
        original_data = base64.b64decode(inflated_data)
        encoded_image = base64.b64encode(original_data).decode('utf-8')
        html_content += f"""
                <div class="image-container">
                    <h2>{image.image_name}</h2>
                    <p>현재 상태: {image.status.value}</p>
                    <img src="data:image/jpeg;base64,{encoded_image}" alt="{image.image_name}">
                </div>
            """

    html_content += "<div class='pagination'>"
    if page > 1:
        html_content += f'<button onclick="goToPage(1)">&laquo;</button>'
        html_content += f'<button onclick="goToPage({page - 1})">&lt;</button>'
    html_content += f'<span>페이지 {page} / {total_pages}</span>'
    html_content += f"""
        <select id="per-page" class="per-page-select" onchange="changePerPage()">
            <option value="10" {'selected' if per_page == 10 else ''}>10개씩 보기</option>
            <option value="20" {'selected' if per_page == 20 else ''}>20개씩 보기</option>
            <option value="50" {'selected' if per_page == 50 else ''}>50개씩 보기</option>
            <option value="{total_images}" {'selected' if per_page == total_images else ''}>전체 보기</option>
        </select>
    """
    if page < total_pages:
        html_content += f'<button onclick="goToPage({page + 1})">&gt;</button>'
        html_content += f'<button onclick="goToPage({total_pages})">&raquo;</button>'
    html_content += "</div></body></html>"

    logging.info(f"검색어 '{q}', 상태 '{status}' 적용 - 페이지 {page}")
    return HTMLResponse(content=html_content)


# PyQt 메인 함수
if __name__ == "__main__":
    qt_app = QtWidgets.QApplication(sys.argv)


    # Dock 아이콘 클릭 시 동작 설정
    def on_focus_changed(old_widget, new_widget):
        if not viewer.isVisible():
            viewer.show()


    qt_app.focusChanged.connect(on_focus_changed)

    # Dock 아이콘 설정
    path = os.path.join(
        os.path.dirname(sys.modules[__name__].__file__),
        '/Users/woojin/Desktop/test/imageSolution/images/moonicon.png',
    )
    qt_app.setWindowIcon(QIcon(path))

    viewer = LogViewer(app=fastapi_app)
    db_window = Mainwindow()

    viewer.setWindowTitle("로그뷰어")
    db_window.setWindowTitle("DB CONNECTION SETTINGS")

    # 시스템 트레이 설정
    tray_icon = QSystemTrayIcon(QIcon(path), qt_app)
    tray_menu = QMenu()

    restore_action = QAction("창 열기", viewer)
    restore_action.triggered.connect(viewer.show)  # 트레이에서 창 열기

    quit_action = QAction("종료", viewer)
    quit_action.triggered.connect(qt_app.quit)  # 앱 종료

    db_mod_open_action = QAction("db연결 수정", viewer)
    db_mod_open_action.triggered.connect(db_window.show)  # db연결 정보 수정하기

    tray_menu.addAction(restore_action)
    tray_menu.addAction(db_mod_open_action)
    tray_menu.addAction(quit_action)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()

    viewer.show()
    sys.exit(qt_app.exec_())
