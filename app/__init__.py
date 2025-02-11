from flask import Flask,g,request, session
from flask_babel import Babel

app = Flask(__name__)




from app import routes



app.run(debug=True)