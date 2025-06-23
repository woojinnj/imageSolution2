import base64
import zlib
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary
from sqlalchemy.orm import declarative_base, sessionmaker
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.responses import HTMLResponse

Base = declarative_base()


class CompressedImage(Base):
    __tablename__ = 'compressed_images'
    id = Column(Integer, primary_key=True, autoincrement=True)
    image_name = Column(String, nullable=False)
    compressed_data = Column(LargeBinary, nullable=False)


# PostgreSQL 연결 정보
username = "postgres"
password = "0000"
database = "postgres"
host = "localhost"
port = "5432"
db_url = f"postgresql+psycopg://{username}:{password}@{host}:{port}/{database}"
engine = create_engine(db_url, echo=True)

# 세션 생성
Session = sessionmaker(bind=engine)
session = Session()

# FastAPI 애플리케이션 생성
app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "메인 화면 입니다!"}


@app.get("/image/name/{image_name}")
def get_image_by_name_with_message(image_name: str):
    """
    데이터베이스에서 이미지 이름으로 검색 및 HTML 형식으로 메시지와 함께 반환
    """
    # 데이터베이스에서 이미지 검색
    retrieved_image = session.query(CompressedImage).filter_by(image_name=image_name).first()

    if not retrieved_image:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")
    image_id = retrieved_image.id

    # 압축 풀기
    inflated_data = zlib.decompress(retrieved_image.compressed_data)
    # 디코딩
    original_data = base64.b64decode(inflated_data)

    # 이미지를 Base64로 인코딩
    encoded_image = base64.b64encode(original_data).decode('utf-8')

    # HTML 응답 생성
    html_content = f"""
        <html>
            <head>
                <title>이미지 표시</title>
            </head>
            <body>
                <h1>{image_name} 이미지</h1>
                <p>이미지 ID: {image_id}</p>
                <img src="data:image/jpeg;base64,{encoded_image}" alt="{image_name}">
            </body>
        </html>
        """
    return HTMLResponse(content=html_content)


@app.get("/image/id/{image_id}")
def get_image_by_id(image_id: int):
    """
    데이터베이스에서 ID로 이미지 검색 및 반환
    """
    # 데이터베이스에서 이미지 검색
    retrieved_image = session.query(CompressedImage).filter_by(id=image_id).first()
    image_name = retrieved_image.image_name
    if not retrieved_image:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")

    # 압축 풀기
    inflated_data = zlib.decompress(retrieved_image.compressed_data)
    # 디코딩
    original_data = base64.b64decode(inflated_data)
    # 이미지를 Base64로 인코딩
    encoded_image = base64.b64encode(original_data).decode('utf-8')

    # HTML 응답 생성
    html_content = f"""
            <html>
                <head>
                    <title>이미지 표시</title>
                </h
                <body>
                    <h1>{image_name} 이미지</h1>
                    <p>이미지 ID: {image_id}</p>
                    <img src="data:image/jpeg;base64,{encoded_image}" alt="{image_name}">
                </body>
            </html>
            """
    return HTMLResponse(content=html_content)


@app.get("/image/all1")
def get_all_images1():
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
            <title>모든 이미지</title>
        </head>
        <body>
            <h1>모든 이미지</h1>
    """

    for image in all_images:
        # 압축 풀기 및 디코딩
        inflated_data = zlib.decompress(image.compressed_data)
        original_data = base64.b64decode(inflated_data)

        # 이미지를 Base64로 인코딩
        encoded_image = base64.b64encode(original_data).decode('utf-8')

        html_content += f"""
            <div style="margin-bottom: 50px;">
                <h2>이미지 이름: {image.image_name}</h2>
                <p>이미지 ID: {image.id}</p>
                <img src="data:image/jpeg;base64,{encoded_image}" alt="{image.image_name}" style="max-width: 350px; max-height: 350px;">
            </div>
        """

    html_content += """
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/image/all2")
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
    return HTMLResponse(content=html_content)
