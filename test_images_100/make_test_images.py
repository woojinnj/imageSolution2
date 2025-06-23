from PIL import Image, ImageDraw
import os

# 테스트용 이미지 생성 함수
def create_test_images(directory, num_images=100):
    if not os.path.exists(directory):
        os.makedirs(directory)

    for i in range(num_images):
        # 이미지 크기 및 색상 설정
        img = Image.new('RGB', (100, 100), color=(i * 2 % 255, i * 3 % 255, i * 5 % 255))
        d = ImageDraw.Draw(img)
        d.text((10, 40), f"Image {i+1}", fill=(255, 255, 255))

        # 이미지 파일 저장
        img.save(os.path.join(directory, f"image_{i+1}.png"))

    print(f"{num_images}개의 테스트 이미지가 '{directory}'에 저장되었습니다.")

# 사용할 디렉토리 경로 설정
output_directory = "test_images"
create_test_images(output_directory)
