from flask import Flask, render_template, request, url_for, jsonify, redirect
import jwt
import datetime
import certifi
from pymongo import MongoClient  
import hashlib 

app = Flask(__name__)
SECRET_KEY = 'THIS IS SECRET KEY'
client = MongoClient('localhost', 27017)  # mongoDB는 27017 포트로 돌아갑니다.
db = client.dbjungle   

@app.route('/api/register', methods=['POST'])
def api_register():
   id = request.form['id']
   pw = request.form['pw']
   pw_chk = request.form['pw_chk']
   nickname = request.form['nickname']
   if pw != pw_chk:
       return jsonify({'result': 'fail', 'msg': '비밀번호가 일치하지 않습니다.'})
   if (pw == '' or id == '') and nickname != '':
       return jsonify({'result': 'fail', 'msg': '아이디/비밀번호를 입력해주세요.'})
   if nickname == '' and (pw != '' and id != ''):
       return jsonify({'result': 'fail', 'msg': '이름(성명)을 입력해주세요.'})
   if nickname == '' or pw == '' or id == '':
       return jsonify({'result': 'fail', 'msg': '아무것도 입력하지 않으셨습니다.'})
   if db.user.find_one({'id': id}) is not None:
        return jsonify({'result': 'fail', 'msg': '이미 존재하는 아이디입니다.'})
   if pw == pw_chk:
       pwhash = hashlib.sha256(pw.encode('utf-8')).hexdigest()
       db.user.insert_one({'id': id, 'pw': pwhash, 'nickname': nickname})
       return jsonify({'result': 'success'})

@app.route('/api/login', methods=['POST'])
def api_login():
    id = request.form['id']
    pw = request.form['pw']
    pw_hash = hashlib.sha256(pw.encode('utf-8')).hexdigest()
    result = db.user.find_one({'id': id, 'pw': pw_hash})
    if result is not None:
        payload = {
            'id': id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=5)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return jsonify({'result': 'success', 'token': token})
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

@app.route('/')
def home():
   token_receive = request.cookies.get('mytoken')
   try:
       payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
       user_info = db.user.find_one({"id": payload['id']})
       return render_template('index.html', nickname=user_info['nickname'])
   except jwt.ExpiredSignatureError:   
       return redirect(url_for("api_login", msg = "로그인 시간이 만료되었습니다."))
   except jwt.exceptions.DecodeError:
        return redirect(url_for("api_login", msg = "로그인 정보가 존재하지 않습니다."))

@app.route('/api/nickname', methods=['GET'])
def api_valid():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        print(payload)
        userinfo = db.user.find_one({"id": payload['id']}, {'_id': False})
        return jsonify({'result': 'success', 'nickname': userinfo['nickname']})
    except jwt.ExpiredSignatureError:
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})

if __name__ == '__main__':
   app.run('0.0.0.0', port=5000, debug=True)