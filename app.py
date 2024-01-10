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
   if pw == pw_chk and nickname != '' and pw != '' and id != '':
       pwhash = hashlib.sha256(pw.encode('utf-8')).hexdigest()
       db.user.insert_one({'id': id, 'pw': pwhash, 'nickname': nickname, 'point': 100})
       payload = {
            'id': id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
        }
       token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
       return jsonify({'result': 'success', 'token': token , 'msg': '회원가입이 완료되었습니다.'})
   
   token_receive = request.cookies.get('mytoken')
   try:
       payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
       user_info = db.user.find_one({"id": payload['id']})
       return render_template('main.html', nickname=user_info['nickname'], point = user_info['point'])
   except jwt.ExpiredSignatureError:   
       return redirect(url_for("login", msg = "로그인 시간이 만료되었습니다."))
   except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg = "로그인 정보가 존재하지 않습니다."))
   
@app.route('/api/notuser', methods=['POST'])
def api_notuser():
    db.user.delete_many({'point': 0})
    return jsonify({'result': 'success', 'msg': "포인트가 없는 회원은 탈퇴한 회원입니다. 데이터가 말소됩니다."})

@app.route('/api/login', methods=['POST'])
def api_login():
    id = request.form['id']
    pw = request.form['pw']
    pw_hash = hashlib.sha256(pw.encode('utf-8')).hexdigest()
    result = db.user.find_one({'id': id, 'pw': pw_hash })
    if result is not None:
        payload = {
            'id': id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return jsonify({'result': 'success', 'token': token , 'msg': '로그인을 완료하였습니다.'})
    
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"id": payload['id']})
        return render_template('main.html', nickname=user_info['nickname'], point = user_info['point'])
    except result is None:
        return redirect(url_for("login", msg = "아이디/비밀번호가 일치하지 않습니다."))
    except jwt.ExpiredSignatureError:   
        return redirect(url_for("login", msg = "로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
         return redirect(url_for("login", msg = "로그인 정보가 존재하지 않습니다."))

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
       return render_template('main.html', nickname = user_info['nickname'] , point = user_info['point'])
   except jwt.ExpiredSignatureError:   
       return redirect(url_for("login", msg = "로그인 시간이 만료되었습니다."))
   except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg = "로그인 정보가 존재하지 않습니다."))
   
@app.route('/vote/<mooncheol>')
def vote(mooncheol):
   token_receive = request.cookies.get('mytoken')
   try:
       payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
       user_info = db.user.find_one({"id": payload['id']})
       return render_template('vote.html', nickname = user_info['nickname'], point = user_info['point'], title = mooncheol)
   except jwt.ExpiredSignatureError:   
       return redirect(url_for("login", msg = "로그인 시간이 만료되었습니다."))
   except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg = "로그인 정보가 존재하지 않습니다."))

@app.route('/api/nickname', methods=['GET'])
def api_valid():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        print(payload)
        userinfo = db.user.find_one({"id": payload['id']}, {'_id': False})
        return jsonify({'result': 'success', 'nickname': userinfo['nickname'] , 'point': userinfo['point']})
    except jwt.ExpiredSignatureError:
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})
    
@app.route('/api/vote_A', methods=['POST'])
def api_voteA():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"id": payload['id']})
        point = int(user_info['point'])
        usedpoint = int(request.form['usedpoint'])
        title = request.args.get("title")
        Bpoint = 0
        user_vote = db.user.find_one({'id': payload['id']}, {'title' : title})
        if db.user.find_one({'id': payload['id']}) is None:
            return jsonify({'result': 'fail', 'msg': '이미 동일한 이름의 투표에 투표하셨습니다.'})
        elif point - usedpoint < 0:
            return jsonify({'result': 'fail', 'msg': '포인트가 부족합니다.'})
        else:
            db.user.update_one({"id": payload['id']}, {"$set": {"point": point - usedpoint}})
            db.user.update_one({"id": payload['id']}, {"$push": {"title": title}})
            if db.mooncheolA.find_one({"title": title}) is None:
                db.mooncheolA.insert_one({"title": title, "Bpoint": 0})
            else:
                db.mooncheolA.update_one({"title": title}, {"$set": {"Bpoint": Bpoint + usedpoint}}) 
            return jsonify({'result': 'success', 'msg': '정상적으로 결과가 반영되었으며 포인트가 차감되었습니다.' ,
                            'Bpoint' : Bpoint})
    except jwt.ExpiredSignatureError:
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})

@app.route('/api/vote_B', methods=['POST'])
def api_voteB():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"id": payload['id']})
        point = int(user_info['point'])
        usedpoint = int(request.form['usedpoint'])
        Bpoint = 0
        title = request.args.get("title")
        if db.user.find_one({'id': payload['id']}, {'title' : title}) is not None:
            return jsonify({'result': 'fail', 'msg': '이미 동일한 이름의 투표에 투표하셨습니다.'})
        elif point - usedpoint < 0:
            return jsonify({'result': 'fail', 'msg': '포인트가 부족합니다.'})
        else:
            db.user.update_one({"id": payload['id']}, {"$set": {"point": point - usedpoint}})
            db.user.update_one({"id": payload['id']}, {"$push": {"title": title}})
            if db.mooncheolB.find_one({"title": title}) is None:
                db.mooncheolB.insert_one({"title": title, "Bpoint": 0})
            else:
                db.mooncheolB.update_one({"title": title}, {"$set": {"Bpoint": Bpoint + usedpoint}}) 
            return jsonify({'result': 'success', 'msg': '정상적으로 결과가 반영되었으며 포인트가 차감되었습니다.' ,
                            'Bpoint' : Bpoint})
    except jwt.ExpiredSignatureError:
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})
    
@app.route('/api/vote_compare', methods=['POST'])
def api_compare():
    title = request.args.get("title")
    Bpoint = 0
    A = int(Bpoint + db.mooncheolA.find_one({'title': title},{'Bpoint': Bpoint}))
    B = int(Bpoint + db.mooncheolB.find_one({'title': title},{'Bpoint': Bpoint}))
    Apercent = float((A/(A+B))*100)
    Bpercent = float((B/(A+B))*100)
    return jsonify({'result': 'success', 'Apercent': Apercent, 'Bpercent': Bpercent})

if __name__ == '__main__':
   app.run('0.0.0.0', port=5000, debug=True)