import sys
import os
import logging
import zlib
import base64
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QSystemTrayIcon, QAction, QMenu
from PyQt5.QtGui import QIcon
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import Column, Integer, String, LargeBinary
from sqlalchemy.orm import declarative_base
from real_main.pyqt03_ui_basic import LogViewer  # 새로 만든 UI 파일 임포트
from real_main.pyqt03_dbinfo import Session
from real_main.pyqt03_ui_dbinfo_mod import Mainwindow

# SQLAlchemy 및 데이터베이스 설정
Base = declarative_base()


class CompressedImage(Base):
    __tablename__ = 'compressed_images'
    id = Column(Integer, primary_key=True, autoincrement=True)
    image_name = Column(String, nullable=False)
    compressed_data = Column(LargeBinary, nullable=False)


session = Session()

# FastAPI 애플리케이션 생성
fastapi_app = FastAPI()

def get_db():
    """SQLAlchemy 세션을 최신 엔진과 연결된 상태로 제공"""
    db = Session()  # 최신 세션 객체 사용
    try:
        yield db
    finally:
        db.close()

@fastapi_app.get("/")
def read_root():
    logging.info("메인 화면에 접속했습니다.")
    return {"message": "메인 화면 입니다!"}


@fastapi_app.get("/image/name/{image_name}")
def get_image_by_name_with_message(image_name: str):

    retrieved_image = session.query(CompressedImage).filter_by(image_name=image_name).first()
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


@fastapi_app.get("/image/all2")
def get_all_images2():
    """
    데이터베이스의 모든 이미지를 HTML 형식으로 반환
    """
    # 데이터베이스에서 모든 이미지 검색
    all_images = session.query(CompressedImage).all()

    if not all_images:
        raise HTTPException(status_code=404, detail="이미지가 없습니다.")

    # HTML 응답 생성
    html_content = """
      <html>
        <head>
            <title>바둑판 모든 이미지</title>
            <style>
                /* 이미지 컨테이너를 가로로 정렬하고 넘치면 줄바꿈 */
                .image-gallery {
                    display: flex;
                    flex-wrap: wrap; /* 줄바꿈 활성화 */
                    gap: 10px; /* 각 이미지 간 간격 */
                    padding: 30px; /* 좌우 여백 설정 */
                justify-content: center; /* 가로 방향 중앙 정렬 */


                }
                .image-container {
                    width: 384px; /* 최대 너비 제한 */
                    text-align: center; /* 텍스트 중앙 정렬 */
                }
                h2 {
                margin-bottom: 10px; /* 제목과 이미지 사이의 간격 설정 */
            }
                img {
                width: 384px; /* 고정 너비 */
                height: 192px; /* 고정 높이 */
            }

            </style>
        </head>
        <body>
            <h1>바둑판 모든 이미지</h1>
            <div class="image-gallery">
    """

    for image in all_images:
        # 압축 풀기 및 디코딩
        inflated_data = zlib.decompress(image.compressed_data)
        original_data = base64.b64decode(inflated_data)

        # 이미지를 Base64로 인코딩
        encoded_image = base64.b64encode(original_data).decode('utf-8')

        html_content += f"""
                <div class="image-container">
                    <h2>{image.image_name}</h2>
                    <img src="data:image/jpeg;base64,{encoded_image}" alt="{image.image_name}">
                </div>
            """

    html_content += """
                </div>
            </body>
        </html>
        """
    logging.info("전체 이미지 띄우기2(바둑판형식)")
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
    db_window=Mainwindow()


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
    tray_menu.addAction(quit_action)
    tray_menu.addAction(db_mod_open_action)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()

    viewer.show()
    sys.exit(qt_app.exec_())

