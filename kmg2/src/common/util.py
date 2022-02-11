import pymysql
import platform
import datetime
import re
import copy
import jwt
import uuid, pathlib
from secrets import token_bytes
from base64 import b64encode
from src.common.config import *

def mysql_conn(server_type=''):
    
    db_name = MysqlConfig.DATABASE
    host = MysqlConfig.HOST
    port = MysqlConfig.PORT

    conn = pymysql.connect(host=host, port=port, user=MysqlConfig.USER, passwd=MysqlConfig.PASSWORD, db=db_name, charset='utf8mb4', autocommit=True)
    return conn

def mysql_cursor(conn):
    curs = conn.cursor(pymysql.cursors.DictCursor)
    return curs

def get_server_type(request):
    host = request.headers.get('Host')
    host_split = host.split('.')
    server_type = host_split[0]
    ip = request.remote_addr

    return server_type, host, ip

# openssl rand -base64 32 생성
def get_rand_base64_token():
    return b64encode(token_bytes(32)).decode()

# 인증 토근 생성 #
def jwt_token_generator(user_no, user_name, user_id):
    issuer = 'root'
    subject = '127.0.0.1'
    date_time_obj = datetime.datetime
    exp_time = date_time_obj.timestamp(date_time_obj.now() + datetime.timedelta(hours=10))

    payload = {
        'userNo': user_no,
        'userId': user_id,
        'userName': user_name,
        'exp': int(exp_time),
        #'scope': scope_text
    }

    return jwt.encode(payload, JWTConfig.SECRET, algorithm='HS256') #HMAC(Hash-based Message Authentication Code)SHA256

# 리플래쉬 토큰 생성 #  보안대책으로 리플래시 토큰 사용 # 
def jwt_refresh_token_generator(user_no):
    date_time_obj = datetime.datetime
    refresh_payload = {
        'user_no' : user_no,
        'exp': date_time_obj.timestamp(date_time_obj.now() + datetime.timedelta(days=15)) ## 
    }
    return jwt.encode(refresh_payload, JWTConfig.SECRET, algorithm='HS256')

def decode_jwt(headers):
    try:
        if 'Authorization' in headers:
            access_token = headers['Authorization'].replace('Bearer', '')

            if access_token:
                try:
                    payload = jwt.decode(access_token, JWTConfig.SECRET, algorithms='HS256')

                except jwt.InvalidTokenError:
                    payload = None

                if payload is not None:
                    exp = int(payload['exp'])
                    date_time_obj = datetime.datetime
                    now_time = int(date_time_obj.timestamp(date_time_obj.now()))

                    if exp > now_time:
                        return payload

        return None
    except BaseException:
        return None 

def chk_input_match(in_type, in_value):
    # 정규식으로 입력값 체크
    
    if in_type == 'password':
       
        chk = re.compile('^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[$@$!%*?&])[A-Za-z\d$@$!%*?&]{8,10}')

    elif in_type == 'email':
        chk = re.compile('^[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

    else:
        pass

    val = chk.match(in_value)

    # 결과 리턴
    if val is not None:
        return True
    else:
        return False

# 파일업로드

def fileUpload(upFile, filePath, serverType):
    #DB 시작 
    cursor = mysql_cursor(mysql_conn(serverType))
    
    try : 

        #원본 파일명 
        fileNameOrigin = upFile.filename

        #저장될 파일 이름 변경 
        fileName = str(uuid.uuid4()) + pathlib.Path(fileNameOrigin).suffix

        #파일 타입
        contentType = upFile.content_type
        fileTypeArr = contentType.split('/')
        fileType = fileTypeArr[0]       

        #파일 전체 경로
        fileFullPath = filePath + fileName

    except Exception as e :
        print('sql', str(e))
    finally :
        cursor.close()    

    return None