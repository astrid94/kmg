# -*- coding: utf-8 -*-
from flask import Flask
from flask_restx import Api 

from src.board.board import board
from src.board.boardList import boardList
from src.user.join import join
from src.user.login import login

app= Flask(__name__)
api= Api(
    app,
    version='0,1',
    title="homepage",
    description="homepage API Server",
    terms_url="/",
)

api.add_namespace(board, '/board')
api.add_namespace(boardList, '/boardList')
api.add_namespace(join, '/join')
api.add_namespace(login, '/login')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)






