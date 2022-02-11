# -*- coding: utf-8 -*-
import logging
import traceback
logging.basicConfig(level=logging.ERROR)

from flask import request
from flask_restx import Resource, Namespace, reqparse
from werkzeug.datastructures import FileStorage
#from werkzeug import secure_filename
import datetime, uuid, pathlib, os
from src.common.util import *

board = Namespace('board')

# 메소드별 모델 생성 #
boardGetModel = board.schema_model('',{

  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "timestamp": {
      "type": "string"
    },
    "boardNo": {
      "type": "string"
    },
    "title": {
      "type": "string"
    },
    "content": {
      "type": "string"
    },
    "userName": {
      "type": "string"
    },
    "createdDate": {
      "type": "string"
    }
  },
  "required": [
    "timestamp",
    "boardNo",
    "title",
    "content",
    "userName",
    "createdDate"
  ]
})

boardPostModel = board.schema_model('',{

  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "timestamp": {
      "type": "string"
    },
     "boardNo": {
        "type": "integer"
     }
  },
  "required": [
    "timestamp"
    "boardNo"
  ]
})

boardPutModel = board.schema_model('',{

  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "timestamp": {
      "type": "string"
    }
  },
  "required": [
    "timestamp"
  ]
})

boardDeleteModel = board.schema_model('',{

  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "timestamp": {
      "type": "string"
    }
  },
  "required": [
    "timestamp"
  ]
})



@board.route('', methods=['GET','POST','PUT','DELETE'])

class boardApi(Resource):
    
    parser = board.parser()
    parser.add_argument('boardNo', type=int, required=True, location='body', help= '게시판번호')
    @board.expect(parser)
    
    @board.doc(model=boardGetModel)


# GET #

# swager 파라미터 #
    def get(self):
        """
        게시판 번호 조회
        필수: boardNo
        """

        statusCode = 200
        data = {'timestamp': datetime.datetime.now().isoformat()}

        # host 정보 #
        serverType, host, userIp = get_server_type(request)

        # 파라미터 정리 #
        parser = reqparse.RequestParser()
        parser.add_argument('boardNo', type=int, required=True)
        parameter = parser.parse_args()

        # DB 시작 # 
        cursor = mysql_cursor(mysql_conn(serverType))

        try:
            hasParam = True 

            if 'boardNo' not in parameter or parameter['boardNo'] =='':
                    hasParam = False

            if hasParam: 
                boardNo = parameter['boardNo']

                # 입력값 등록 확인 #
                sql = """SELECT COUNT(*) AS cnt 
                FROM board 
                WHERE disabled = 0 
                AND boardNo = %s"""
                cursor.execute(query=sql, args=boardNo)
                result = cursor.fetchone()

                
                if result['cnt'] == 1:
                    
                    sql ="""UPDATE board
                    SET count= count+1 
                    WHERE boardNo = %s """
                    cursor.execute(query=sql, args=boardNo)

                    # 상세 조회 
                    sql = """SELECT U.userName, B.title, B.content, B.createdDate
                    FROM board B 
                    LEFT JOIN user U ON B.userNo=U.userNo
                    WHERE B.disabled = 0 
                    AND B.boardNo = %s """    
                    cursor.execute(query=sql, args=boardNo)

                    result = cursor.fetchone()
                    data['userName'] = result['userName']
                    data['title'] = result['title']
                    data['content'] = result['content']
                    data['createdDate'] = result['createdDate'].strftime('%Y-%m-%d %H:%M')

                else:
                    statusCode= 400
                    data['error'] = '데이터 불일치'
            else:
                statusCode= 404
                data['error'] = 'No Parameter'

        except Exception as e:
            logging.error(traceback.format_exc())
            data['error'] = 'exception error' + str(e)
            statusCode = 505  
        
        finally : 
            cursor.close
            # DB 종료 #

        return data, statusCode

    # POST #

    # swager 파라미터 #
    parser = board.parser()
    parser.add_argument('Authorization', required=True, location='headers', help='로그인 token',) #로그인 한사람만 볼 수있음
    parser.add_argument('title', required=True, location='body', help='제목',)
    parser.add_argument('content', required=True, location='body', help='내용')
    parser.add_argument('file', type=FileStorage, required=False, location='files', help='파일')
    
    @board.expect(parser)

    @board.doc(model=boardPostModel)

    def post(self):
        """
        게시판 글 등록
        필수: Authorization, title, content, userName
        일반: file
        """

        statusCode = 200
        data = {'timestamp': datetime.datetime.now().isoformat()}

        # host 정보 #
        serverType, host, userIp = get_server_type(request)

        # 로그인 확인
        payload = decode_jwt(request.headers)
        if payload is None:
            data['error'] = '로그인 인증되지 않는 사용자입니다.'
            return data, 401
        
        # 파라미터 정리 #
        parser = reqparse.RequestParser()
        parser.add_argument('title', type=str, required=True)
        parser.add_argument('content', type=str, required=True)
               
        parameter = parser.parse_args()

        # DB 시작 #
        cursor = mysql_cursor(mysql_conn(serverType))

        try : 
            hasParam = True

            if 'userId' not in payload or payload['userId'] =='':
                hasParam = False

            if 'title' not in parameter or parameter['title'] == '':
                hasParam = False
            
            if 'content' not in parameter or parameter['content'] == '':
                hasParam = False

            if hasParam:
                userId = payload['userId']
                title = parameter['title']
                content = parameter['content']
            
                #파일 
                file = None
                if request.files['file'] is not None  : 
                    file = request.files['file'] 

                sql = """
                      SELECT COUNT(*) AS cnt
                      FROM user
                      WHERE disabled = 0
                      AND userId = %s 
                      """
                cursor.execute(query=sql, args=(userId))
                result = cursor.fetchone()
                
                if result ['cnt'] == 1 :

                    sql = """INSERT INTO board (userNo, title, content, fileNo)
                    CALUES (%s, %s, %s, %s)"""
                    cursor.execute(query=sql, args=(userId, title, content, fileNo))
                    data['boardNo'] = cursor.lastrowid
                    
                    
                    fileNameOrigin = file.filename

                    fileName = str(uuid.uuid4()) +  pathlib.Path(fileNameOrigin).suffix

                    contentType = file.content_type

                    filePath = 'files/board/'
                    
                    fileFullPath = filePath + fileName

                    file.save(fileFullPath)

                    fileSize = os.path.getsize(fileFullPath)

                    sql = """INSERT INTO files (fileName, fileNameOrigin, fileType, fileSize, fileUrl, boardNo) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(query=sql, args=(fileName, fileNameOrigin, contentType, fileSize, fileFullPath, data['boardNo']))
                    fileNo = cursor.lastrowid

            else:
                statusCode = 404
                data['error'] = 'No Parameter'
        
        except Exception as e:
            logging.error(traceback.format_exc())
            data['error'] = 'exception error' + str(e)
            statusCode = 505
            return data, statusCode

        finally:
            cursor.close()
            # DB 종료 #

        return data, statusCode

    # PUT #

    # swager 파라미터 #
    parser = board.parser()
    parser.add_argument('Authorization', required=True, location='headers', help='로그인 token',)
    parser.add_argument('boardNo',type=int,required=True, location='body', help='게시판 번호')
    parser.add_argument('title',type=str,required=True, location='body', help='제목')
    parser.add_argument('content',type=str,required=False, location='body', help='내용')
    parser.add_argument('file', type=FileStorage, required=False, location='files', help='파일')

    @board.expect(parser)

    @board.doc(model=boardPutModel)

    def put(self):
        """
        게시판수정
        필수: Authorization, boardNo, title, userName, content
        """

        statusCode = 200
        data = {'timestamp': datetime.datetime.now().isoformat()}

        # host 정보 #
        serverType, host, userIp = get_server_type(request)

        # 로그인 확인
        payload = decode_jwt(request.headers)
        if payload is None:
            data['error'] = '로그인 인증되지 않는 사용자입니다.'
            return data, 401

        # 파라미터 정리 #
        parser = reqparse.RequestParser()
        parser.add_argument('boardNo', type=int, required=True)
        parser.add_argument('title', type=str, required=True)
        parser.add_argument('content', type=str, required=True)
       
        parameter = parser.parse_args()

        # DB 시작 #       
        cursor = mysql_cursor(mysql_conn(serverType))       

        try:
            hasParam = True
            if 'userId' not in payload or payload['userId'] == '':
                hasParam = False

            if 'boardNo' not in parameter or parameter['boardNo'] == '':
                hasParam = False

            if 'title' not in parameter or parameter['title'] =='':
                hasParam = False

            if 'content' not in parameter or parameter['content'] =='':
               
                hasParam = False
            if hasParam:
                userId = payload['userId']
                boardNo = parameter['boardNo']
                title = parameter['title']
                content = parameter['content']
                
                file = None
                if 'file' in request.files :
                    file = request.files['file']

######           
                # 입력값 등록 확인 #
                sql = """SELECT COUNT(*) AS cnt, userName, title
                FROM board
                WHERE disabled = 0
                AND boardNo = %s 
                AND userName = %s
                AND title = %s"""
                cursor.execute(query=sql, args=(boardNo, userId, title))
                result = cursor.fetchone()

                if result['cnt'] == 1:
                    sql = """UPDATE board SET title = %s, content = %s
                    WHERE boardNo = %s AND userName = %s """ 
                    cursor.execute(query=sql, args=(title, content, boardNo, userId))

                    if file :
                        fileNameOrigin = file.filename

                        filename = str(uuid.uuid4()) +  pathlib.Path(fileNameOrigin).suffix

                        contentType = file.content_type

                        filePath = 'files/board/'
                        
                        fileFullPath = filePath + filename

                        file.save(fileFullPath)

                        sql = """INSERT INTO board(title, content, userName, fileNameOrigin) VALUES (%s, %s, %s, %s)
                        """
                        cursor.execute(query=sql, args=(title, content, userId, fileNameOrigin))


                else:
                    statusCode = 400
                    data['error'] = '수정 불가'

            else:
                statusCode = 404
                data['error'] = 'No Parameter'

        except Exception as e:
            logging.error(traceback.format_exc())
            data['error'] = 'exception error'
            statusCode = 505
            return data, statusCode

        finally:
            cursor.close()
            # DB 종료 #

        return data, statusCode

    # DELETE #

    # swager 파라미터 #
    parser = board.parser()
    parser.add_argument('Authorization', required=True, location='headers', help='로그인 token',)
    parser.add_argument('boardNo', type=int, required=True, location='body', help='게시판번호')
    @board.expect(parser)

    @board.doc(model=boardDeleteModel)

    def delete(self):
        """
        게시판삭제 
        필수:Authorization, boardNo
        """

        statusCode = 200
        data = {'timestamp': datetime.datetime.now().isoformat()}

        #host 정보
        serverType, host, userIp = get_server_type(request)

        # 로그인 확인
        payload = decode_jwt(request.headers)
        if payload is None:
            data['error'] = '로그인 인증되지 않는 사용자입니다.'
            return data, 401

        # 파라미터 정리 #
        parser = reqparse.RequestParser()
        parser.add_argument('boardNo', type=int, required=True)
        parameter = parser.parse_args()

        # DB 시작 #
        cursor = mysql_cursor(mysql_conn(serverType))

        try:
            hasParam = True
            if 'userId' not in payload or payload['userId'] == '' : 
                hasParam = False
            if 'boardNo' not in parameter or parameter['boardNo'] == '' :
                hasParam = False

            if hasParam:
                userId = payload['userId']
                boardNo = parameter['boardNo']

                # 입력값 등록 확인 #
                sql = """SELECT COUNT(*) AS cnt FROM board WHERE boardNo = %s
                AND userName = %s
                """
                cursor.execute(query=sql, args=(boardNo,userId))
                result = cursor.fetchone()
#####
                if result['cnt'] == 1:
                    
                    sql = """UPDATE board SET disabled = 1 WHERE boardNo = %s
                    AND wirter = %s"""
                    cursor.execute(query=sql, args=(boardNo, userId))

                else:
                    statusCode = 400
                    data['error'] = '삭제 오류'

            else:
                statusCode = 404
                data['error'] = 'No Parameter'

        except Exception as e:
            logging.error(traceback.format_exc())
            data['error'] = 'exception error'
            statusCode = 505
            return data, statusCode

        finally:
            cursor.close()
            # DB 종료 #

        return data, statusCode




