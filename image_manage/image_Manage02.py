import base64
import zlib
import os
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLAlchemy ORM 기본 설정
Base = declarative_base()

# PostgreSQL 연결 정보
username = "postgres"
password = "0000"
database = "postgres"
host = "localhost"
port = "5432"

db_url = f"postgresql+psycopg://{username}:{password}@{host}:{port}/{database}"
engine = create_engine(db_url, echo=True)  # PostgreSQL 엔진 생성
Session = sessionmaker(bind=engine)

# DB 테이블 정의
class CompressedImage(Base):
    __tablename__ = 'compressed_images'
    id = Column(Integer, primary_key=True, autoincrement=True)
    image_name = Column(String, nullable=False)
    compressed_data = Column(LargeBinary, nullable=False)

# 테이블 생성
Base.metadata.create_all(engine)

def reorder_ids(session):
    """ID를 1부터 다시 정렬하는 함수"""
    images = session.query(CompressedImage).order_by(CompressedImage.id).all()
    for index, image in enumerate(images, start=1):
        image.id = index
    session.commit()

# 특정 디렉토리에서 이미지 파일을 읽어오는 함수
def process_images_in_directory(directory):
    try:
        # 디렉토리 내의 모든 파일 목록 가져오기
        image_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

        # 이미지 파일들을 처리할 리스트
        compressed_images = []

        for img_file in image_files:
            # 확장자가 이미지 파일인지 확인 (예: .jpg, .png)
            if img_file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                img_path = os.path.join(directory, img_file)
                with open(img_path, 'rb') as img_in:
                    base64_str = base64.b64encode(img_in.read())
                    deflated_data = zlib.compress(base64_str)

                # 이미지 파일명을 DB 이름으로 사용
                compressed_image = CompressedImage(image_name=img_file, compressed_data=deflated_data)
                compressed_images.append(compressed_image)

        # 세션 생성 및 데이터 삽입
        session = Session()
        session.add_all(compressed_images)  # 여러 이미지를 한 번에 추가
        session.commit()
        print(f"{len(compressed_images)}개의 이미지가 PostgreSQL 데이터베이스에 성공적으로 저장되었습니다!")

    except Exception as e:
        print(f"오류 발생: {e}")

# 디렉토리 경로 수정
directory = "/Users/woojin/Desktop/test/imageSolution/test_images_100/test_images"
process_images_in_directory(directory)

# ID 재정렬 호출
session = Session()
try:
    reorder_ids(session)
    print("ID가 성공적으로 재정렬되었습니다!")
except Exception as e:
    print(f"ID 재정렬 중 오류 발생: {e}")
finally:
    session.close()
