from flask import Flask,g,request, session
from flask_babel import Babel

app = Flask(__name__)


app.config['BABEL_DEFAULT_LOCALE']='en'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

app.secret_key = 'your_secret_key'
babel=Babel(app)

def get_locale():
    locale = session.get('lang', app.config['BABEL_DEFAULT_LOCALE'])
    app.logger.debug(f'get_locale() returning: {locale}')
    return session.get('lang', app.config['BABEL_DEFAULT_LOCALE'])
@app.before_request
def set_language():
    lang = request.args.get('lang', session.get('lang', app.config['BABEL_DEFAULT_LOCALE']))
    session['lang'] = lang
    g.lang = lang
    app.logger.debug(f'setting language to {lang}')

from app import routes



app.run(debug=True)