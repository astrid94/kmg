# -*- coding: utf-8 -*-
import logging
import traceback
logging.basicConfig(level=logging.ERROR)

from flask import request 
from flask_restx import Resource, Namespace, reqparse
import datetime
from src.common.util import * 

join = Namespace('join')

# 메소드별 모델 생성
joinPostModel = join.schema_model('joinPostModel', {

    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "timestamp": {
            "type": "string"
        },
        "userNo": {
            "type": "integer"
        }
    },
    "required": [
        "timestamp",
        "userNo"
    ]
})   

@join.route('', methods=['POST'])

class JoinApi(Resource):

# POST

#swager 파라미터

    parser = join.parser()
    
    parser.add_argument('userId', type=str, required=True, location='body', help='회원ID')
    parser.add_argument('password', type=str, required=True, location='body', help='비밀번호')
    parser.add_argument('rePassword', type=str, required=True, location='body', help='비밀번호확인')
    parser.add_argument('userName', type=str, required=True, location='body', help='회원이름')
    parser.add_argument('email', type=str, required=True, location='body', help='이메일')

    @join.expect(parser)

    @join.doc(model=joinPostModel)

    def post(self):
        """
        회원가입
        필수 : userId, password, repassword, userName, email
        """

        statusCode = 200
        data = {'timestamp': datetime.datetime.now().isoformat()}

        serverType, host, userIp = get_server_type(request)

        parser = reqparse.RequestParser()
        parser.add_argument('userId', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        parser.add_argument('rePassword', type=str, required=True)
        parser.add_argument('userName', type=str, required=True)
        parser.add_argument('email', type=str, required=True)
     
        parameter = parser.parse_args()

        # DB 시작
        cursor = mysql_cursor(mysql_conn(serverType))

        try:
            hasParam = True

            if 'userId' not in parameter or parameter['userId'] =='' :
                hasParam = False

            if 'password' not in parameter or parameter['password'] =='' :
                hasParam = False               

            if 'rePassword' not in parameter or parameter['rePassword'] =='' :
                hasParam = False

            if 'userName' not in parameter or parameter['userName'] =='' :
                hasParam = False

            if 'email' not in parameter or parameter['email'] =='' :
                hasParam = False

            if hasParam:
                userId = parameter['userId']
                password = parameter['password']
                rePassword = parameter['rePassword']
                userName = parameter['userName']
                email = parameter['email']


                # 입력값 확인
                hasProcess = True

                # 비밀번호 일치 확인 
                if password != rePassword:
                    statusCode = 404
                    data['error'] = '비밀번호가 일치하지 않습니다.'
                    hasProcess = False

                if password is not None :
                    # 비밀번호 체크
                    password_chk = chk_input_match('password', password)
                    if not password_chk : 
                        statusCode = 404
                        data['error'] = '비밀번호를 다시 생성하세요.'
                        hasProcess = False

                if email is not None:
                    # 이메일 체크
                    email_chk =  chk_input_match('email', email)
                    if not email_chk:
                        statusCode = 404
                        data['error'] = ' 이메일 주소가 유효하지 않습니다.'
                        hasProcess = False

                if hasProcess:

                    # ID 중복체크
                    sql = """SELECT COUNT(*) AS cnt 
                    FROM user 
                    WHERE userId = %s """
                    cursor.execute(query=sql, args=userId)
                    result = cursor.fetchone()

                    if result['cnt'] == 0 :

                        sql = """INSERT INTO user (userId, password, userName, email)
                        VALUES (%s, PASSWORD(%s), %s, %s)
                        """
                        cursor.execute(query=sql, args=(userId, password, userName, email))
                        userNo = cursor.lastrowid

                        data['userNo'] = userNo

                    else:
                        statusCode = 404
                        data['error'] = '동일한 회원 아이디가 존재합니다. 아이디를 변경해주세요'

            else:
                statusCode = 404
                data['error'] = 'No Parameter'

        except Exception as e:
            logging.error(traceback.format_exc())
            data['error'] = 'exception error'
            statusCode = 505
            return data, statusCode

        finally:
            # DB 종료
            cursor.close()

        return data, statusCode