# -*- coding: utf-8 -*-
import logging
import traceback
logging.basicConfig(level=logging.ERROR)

from flask import request
from flask_restx import Resource, Namespace, reqparse
import datetime
from src.common.util import *

boardList = Namespace('boardList')

boardListGet = boardList.schema_model('boardListGet',{

  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "timestamp": {
      "type": "string"
    },
    "page": {
      "type": "integer"
    },
    "pageSize": {
      "type": "integer"
    },
    "nextPage": {
      "type": "boolean"
    },
    "boardList": {
      "type": "array",
      "items": [
        {
          "type": "object",
          "properties": {
            "boardNo": {
              "type": "integer"
            },
            "title": {
              "type": "string"
            },
            "content": {
              "type": "string"
            },
            "writer": {
              "type": "string"
            }
          },
          "required": [
            "boardNo",
            "title",
            "content",
            "writer"
          ]
        }
      ]
    }
  },
  "required": [
    "timestamp",
    "page",
    "pageSize",
    "nextPage",
    "boardList"
  ]
})

@boardList.route('', methods=['GET'])

class boardListApi(Resource):

    # GET # 
    # 로그인 완료된 회원이 작성한 게시글만 보여주기
    
    # swagger 파라미터 #
    parser = boardList.parser()
    parser.add_argument('Authorization', type = str, required=False, location='headers', help='로그인 token',)
    parser.add_argument('searchType', type = str, required=False, location='body', help='검색유형 (title,writer)')
    parser.add_argument('searchText', type = str, required=False, location='body', help='검색어')
    parser.add_argument('page', type = int, required=False, location='body', help='현재 페이지')
    parser.add_argument('pageSize', type = int, required=False, location='body', help='페이지당 데이터 수')
    @boardList.expect(parser)

    @boardList.doc(model=boardListGet)

    def get(self):
        """
        게시판 리스트
        searchType : title, writer
        일반: searchType, searchText, page, pageSize
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
        parser.add_argument('searchType', type =str, required = False)
        parser.add_argument('searchText', type =str, required = False)
        parser.add_argument('page', type = int, required = False)
        parser.add_argument('pageSize', type = int, required = False)
        parameter = parser.parse_args()

        # DB 시작 #
        cursor = mysql_cursor(mysql_conn(serverType))

        try:
            hasParam = True

            if hasParam:

                userId = None
                if payload is not None : 
                    userId = payload['userId']

                searchType = None
                if parameter['searchType'] is not None :
                    searchType = parameter['searchType']

                searchText = None
                if parameter['searchText'] is not None :
                    searchText = parameter['searchText']
                    
                page = 0
                if parameter['page'] is not None:
                    page = parameter['page']

                pageSize = 20
                if parameter['pageSize'] is not None:
                    pageSize = parameter['pageSize']

                sql = """SELECT COUNT(*) AS cnt
                FROM board
                WHERE disabled = 0 """
######### 다시보기
                if userId is not None : 

                  sql = """SELECT COUNT(*) cnt 
                  FROM user 
                  WHERE disabled = 0
                  AND userId = %s """
                  cursor.execute(query= sql, args=userId)
                  result = cursor.fetchone()

                if searchType is not None and searchText is not None :
                    if searchType == 'title' :
                            par_sql = sql+ " AND title LIKE '%%%s%%' " %searchText
                    elif searchType == 'writer' :
                        par_sql = sql+ " AND writer LIKE '%%%s%%' " %searchText    
                    elif searchType == 'content' :
                        par_sql = sql+ " AND content LIKE '%%%s%%' " %searchText
                    else :
                        par_sql = sql + ""
                cursor.execute(query= par_sql)
                result = cursor.fetchone()

                if result['cnt'] > 0 : 

                    sql = """SELECT boardNo, title, writer
                    FROM board
                    WHERE disabled = 0 """


                if searchType is not None and searchText is not None:
                    if searchType == 'title':
                        sql = sql + "AND title LIKE '%%%s%%' " %searchText
                    elif searchType == 'writer':
                        sql = sql + "AND writer LIKE '%%%s%%' " %searchText
                    elif searchType == 'content':    
                        sql = sql + "AND content LIKE '%%%s%%' " %searchText
                    else :
                        sql = sql + ""

                sql = sql + " ORDER BY boardNo DESC "
                
                sql = sql + " LIMIT %d, %d " % (pageSize * page, pageSize + 1)

                # query #
                cursor.execute(query=sql)              

                itemList = []
                for row in cursor.fetchall():
                    item = {}
                    item['boardNo'] = row['boardNo']
                    item['title'] = row['title']
                    item['content'] = row['content']
                    item['writer'] = row['writer']
                    itemList.append(item)

                data['totalCount'] = result['cnt']
                data['page'] = page
                data['pageSize'] = pageSize

                nextPage = False
                if len(itemList) > pageSize : 
                    del itemList[-1]
                    nextPage = True

                data['nextPage'] = nextPage
                data['boardList'] = itemList
                

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






                








