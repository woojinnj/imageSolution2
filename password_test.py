import bcrypt
from real_main.pyqt03_dbinfo import db_info
# 비밀번호를 바이트 문자열로 변환
password = "my_password".encode('utf-8')

# salt 생성
salt = bcrypt.gensalt()

# 비밀번호를 암호화
hashed_password = bcrypt.hashpw(password, salt)

print("암호화된 비밀번호:", hashed_password)

# 비밀번호 확인
check_password = "my_password".encode('utf-8')
if bcrypt.checkpw(check_password, hashed_password):
    print("비밀번호가 일치합니다.")
else:
    print("비밀번호가 일치하지 않습니다.")


print(db_info["password"])