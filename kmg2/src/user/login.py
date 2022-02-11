# -*- coding: utf-8 -*-
import logging
import traceback
logging.basicConfig(level=logging.ERROR)

from flask import request
from flask_restx import Resource, Namespace, reqparse
import datetime
from src.common.util import *

login = Namespace('login')

# 메소드별 모델 생성 #
loginPost = login.schema_model('loginPostModel',{

  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "timestamp": {
      "type": "string"
    },
    "userName": {
      "type": "string"
    },
    "token": {
      "type": "string"
    },
    "refresh_token": {
      "type": "string"
    }
  },
  "required": [
    "timestamp",
    "userName",
    "token",
    "refresh_token"
  ]
})

@login.route('', methods=['POST'])
class loginApi(Resource):

    # swagger 파라미터 #
    parser = login.parser()
    parser.add_argument('userId', required=True, location='body', help = '회원 아이디')
    parser.add_argument('userPassword', required=True, location='body', help = '회원 비밀번호')
    @login.expect(parser)

    @login.doc(model=loginPost)

    def post(self):
        """
        로그인
        필수: userId, userPassword
        """

        statusCode = 200
        data = {'timestamp': datetime.datetime.now().isoformat()}

        # host 정보 # 
        serverType, host, userIp = get_server_type(request)

        # 파라미터 정리 # 
        parser = reqparse.RequestParser()
        parser.add_argument('userId', type=str, required=True)
        parser.add_argument('userPassword', type=str, required=True)
        parameter = parser.parse_args()

        # DB 시작 #
        cursor = mysql_cursor(mysql_conn(serverType))

        try:

            hasParam = True

            if 'userId' not in parameter or parameter['userId'] is None :
                hasParam = False

            if 'userPassword' not in parameter or parameter['userPassword'] is None :
                hasParam = False

            if hasParam:
                userId = parameter['userId']
                userPassword = parameter['userPassword']
                #DB에서 userId와 userPassword조건으로 검색. 

                sql = """SELECT COUNT(*) AS cnt, userNo, userId, userName
                FROM user
                WHERE disabled = 0 
                AND userId= %s 
                AND userPassword= PASSWORD(%s) """

                cursor.execute(query=sql, args=(userId, userPassword))
                result = cursor.fetchone()

                if result is not None : 
                    userId = result['userId']
                    userNo = result['userNo']
                    userName = result['userName']

                    # 토큰 생성 #           #JSON Web Tokens#
                    token = jwt_token_generator(userNo, userName, userId)

                    # 리프레시 토큰 #
                    refresh_token = jwt_refresh_token_generator(userNo)

                    # 토큰 업데이트 #
                    sql = """UPDATE user SET refreshToken = %s WHERE userNo = %s """
                    cursor.execute(query=sql, args=(refresh_token, userNo))

                    data['userNo'] = userNo
                    data['userName'] = userName
                    data['token'] = token
                    data['refresh_token'] = refresh_token
                    #data['tokenGenerator'] = get_rand_base64_token() # 토큰생성용

                else:
                    statusCode = 404
                    data['error'] = '아이디 비밀번호 오류'
                    print(data)

            else:
                statusCode = 404
                data['error'] = 'No Parameter'

        except Exception as e:
            print('Exception')
            logging.error(traceback.format_exc())
            data['error'] = 'exception error'
            statusCode = 505
            return data, statusCode

        finally:
            cursor.close() 
            # DB 종료 # 

        print('data ==>', data)

        return data,statusCode


