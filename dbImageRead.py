import base64
import zlib
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary
from sqlalchemy.orm import declarative_base, sessionmaker

# PostgreSQL 연결 정보
username = "postgres"
password = "0000"
database = "postgres"
host = "localhost"
port = "5432"

# psycopg를 사용하는 연결 URL
db_url = f"postgresql+psycopg://{username}:{password}@{host}:{port}/{database}"
engine = create_engine(db_url, echo=True)

# SQLAlchemy ORM 기본 설정
Base = declarative_base()

class CompressedImage(Base):
    __tablename__ = 'compressed_images'
    id = Column(Integer, primary_key=True, autoincrement=True)
    image_name = Column(String, nullable=False)
    compressed_data = Column(LargeBinary, nullable=False)

# 세션 생성
Session = sessionmaker(bind=engine)
session = Session()

try:
    # 데이터베이스에서 이미지 검색
    image_name = "misosoup.jpg"
    retrieved_image = session.query(CompressedImage).filter_by(image_name=image_name).first()

    if retrieved_image:
        print(f"이미지 '{retrieved_image.image_name}'을(를) 데이터베이스에서 읽어왔습니다!")

        # 압축 해제
        inflated_data = zlib.decompress(retrieved_image.compressed_data)

        # Base64 디코딩
        original_data = base64.b64decode(inflated_data)

        # 이미지 파일로 저장
        output_path = '/Users/woojin/Desktop/test/imageSolution/restored_misosoup.jpg'
        with open(output_path, 'wb') as out_file:
            out_file.write(original_data)

        print(f"이미지를 '{output_path}' 경로에 복원했습니다!")
    else:
        print(f"이미지 '{image_name}'을(를) 데이터베이스에서 찾을 수 없습니다.")
except Exception as e:
    print(f"오류 발생: {e}")
finally:
    session.close()
