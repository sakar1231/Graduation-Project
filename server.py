import os
import sys
from functools import lru_cache
from pathlib import Path
from flask import Flask, jsonify, render_template, request
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from password_risk import PasswordRiskPredictor, PwnedPasswordCheckError, check_password_exposure
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 2048
@lru_cache(maxsize=1)
def predictor():
    return PasswordRiskPredictor(ROOT / 'artifacts/password_risk_model.joblib')
@app.after_request
def headers(response):
    response.headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Frame-Options':'DENY','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"})
    return response
@app.get('/')
def index():
    return render_template('index.html')
@app.get('/health')
def health():
    predictor()
    return jsonify(status='ok')
@app.post('/api/analyze')
def analyze():
    if not request.is_json:
        return jsonify(error='Submit a JSON request.'),415
    data=request.get_json(silent=True)
    if not isinstance(data,dict) or not isinstance(data.get('password'),str):
        return jsonify(error='Enter a test password.'),400
    password=data['password']
    if not 4 <= len(password) <= 64:
        return jsonify(error='Use between 4 and 64 characters.'),400
    if not isinstance(data.get('breach_check',False),bool):
        return jsonify(error='Invalid breach-check option.'),400
    result=predictor().evaluate(password)
    result['breach']={'status':'not_requested'}
    if data.get('breach_check',False):
        try:
            count=check_password_exposure(password)
            result['breach']={'status':'found' if count else 'not_found','count':count}
        except PwnedPasswordCheckError:
            result['breach']={'status':'unavailable'}
    return jsonify(result)
@app.errorhandler(413)
def large(error):
    return jsonify(error='Request too large. Use at most 64 characters.'),413
@app.errorhandler(500)
def failure(error):
    return jsonify(error='Analysis is temporarily unavailable.'),500
if __name__=='__main__':
    from waitress import serve
    serve(app,host=os.getenv('HOST','127.0.0.1'),port=int(os.getenv('PORT','8080')),threads=4)
