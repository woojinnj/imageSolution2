import base64
import zlib
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


while True:
    img = input("이미지 파일명을 입력하세요(exit 입력시 종료): ")
    if img.lower() == "exit":
        print("종료합니다...")
        break

    try:
        # Base64 인코딩 및 압축
        with open(img, 'rb') as img_in:
            base64_str = base64.b64encode(img_in.read())
            deflated_data = zlib.compress(base64_str)

        # 세션 생성 및 데이터 삽입
        session = Session()
        img_db_name = input("DB에 어떤 이름으로 넣을까요: ")
        compressed_image = CompressedImage(image_name=img_db_name, compressed_data=deflated_data)
        session.add(compressed_image)
        session.commit()
        print(f"이미지 '{img_db_name}'의 압축 데이터를 PostgreSQL 데이터베이스에 성공적으로 저장했습니다!")
    except Exception as e:
        print(f"오류 발생: {e}")
        session.rollback()
    finally:
        session.close()

    # ID 재정렬 호출
    session = Session()
    try:
        reorder_ids(session)
        print("ID가 성공적으로 재정렬되었습니다!")
    except Exception as e:
        print(f"ID 재정렬 중 오류 발생: {e}")
    finally:
        session.close()

# 삭제 예시
def delete_image_by_id(image_id):
    session = Session()
    try:
        image = session.query(CompressedImage).filter_by(id=image_id).first()
        if image:
            session.delete(image)
            session.commit()
            print(f"ID {image_id} 데이터가 삭제되었습니다.")
            reorder_ids(session)
        else:
            print(f"ID {image_id} 데이터가 없습니다.")
    except Exception as e:
        print(f"삭제 중 오류 발생: {e}")
        session.rollback()
    finally:
        session.close()
