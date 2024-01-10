from flask import Flask, render_template, request, url_for, jsonify, redirect
import jwt
import datetime
import certifi
from pymongo import MongoClient  
import hashlib 
from bson.objectid import ObjectId

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
       db.user.insert_one({'id': id, 'pw': pwhash, 'nickname': nickname, 'point': 100 , 'post_id': []})
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
       _id = request.values.get("_id")
       A_origin = db.mooncheolA.find_one({'Post_log': _id })
       B_origin = db.mooncheolB.find_one({'Post_log': _id })
       if A_origin is None and B_origin is None:
              Apercent = 0
              Bpercent = 0
       elif A_origin is None and B_origin is not None:
                Apercent = 0
                Bpercent = 100
       elif A_origin is not None and B_origin is None:     
                    Apercent = 100
                    Bpercent = 0
       else:
                    A = A_origin['Bpoint']
                    B = B_origin['Bpoint']
                    Apercent = float((A/(A+B))*100)
                    Bpercent = 100 - Apercent
       return render_template('main.html', nickname = user_info['nickname'] , point = user_info['point'],
                              Apercent = Apercent, Bpercent = Bpercent)
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
    
@app.route('/main', methods=['POST'])
def apply_moonchul():
    subject_1_receive = request.form['subject_1_give']
    subject_2_receive = request.form['subject_2_give']
    argument_receive = request.form['argument_give']
    position_1_receive = request.form['position_1_give']
    position_2_receive = request.form['position_2_give']

    db.moonchuls.insert_one({'subject1': subject_1_receive,'subject2': subject_2_receive, 
                             'argument': argument_receive, 'position1': position_1_receive, 
                             'position2': position_2_receive, 'isProceeding': 'True' ,
                             'vote1': 0, 'vote2': 0, 'Post_log': [], 'Apoint': 0 , 'Bpoint': 0})
    return jsonify({'result': 'success' , 'subject1': subject_1_receive,
                    'subject2': subject_2_receive, 'argument': argument_receive, 
                    'position1': position_1_receive, 'position2': position_2_receive, 'isProceeding': 'True',
                     'msg': '정상적으로 등록되었습니다.'})


@app.route("/show/proceeding", methods=['GET'])
def show_proceeding_moonchuls():
    result = list(db.moonchuls.find({'isProceeding': 'True'},{'_id':0}))
    return jsonify({'result': 'success', 'moonchuls': result})

@app.route("/show/result", methods=['GET'])
def show_result_moonchuls():
    result = list(db.moonchuls.find({'isProceeding': 'False'},{'_id':0}))
    return jsonify({'result': 'success', 'moonchuls': result})

@app.route("/vote/update", methods=['POST'])
def updateVoteCount():
    findData = request.form['id']
    idElement = ''
    voteElement = ''
    plusCount = 0
    
    
    voteCount = db.moonchuls.find_one({'subject1': findData})
    if voteCount is None:
        voteCount = db.moonchuls.find_one({'subject2': findData})
        idElement = 'subject2'
    else:
        idElement = 'subject1'
    
    if idElement is 'subject1':
        plusCount = voteCount['vote1'] + 1
        voteElement = 'vote1'
        
    elif idElement is 'subject2':
        plusCount = voteCount['vote2'] + 1
        voteElement = 'vote2'
        
    
    db.moonchuls.update_one({idElement: findData}, {'$set': {voteElement: plusCount}})
    return jsonify({'result': 'success', 'msg': '투표 집계가 완료되었습니다.'})

@app.route('/api/vote_A', methods=['POST'])
def api_voteA():
    token_receive = request.cookies.get('mytoken')
    _id = request.values.get("_id")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"id": payload['id']})
        point = int(user_info['point'])
        usedpoint = int(request.form['usedpoint'])
        Bpoint = 0
        if user_info:
            post_ids = user_info.get('post_id', [])
            if _id in post_ids:  # '특정 값'이 post_ids 리스트 안에 있는지 확인
                return jsonify({'result': 'fail', 'msg': '이미 동일한 이름의 투표에 투표하셨습니다. 중복 투표는 불가합니다.'})
            else:
                db.user.update_one({"id": payload['id']}, {"$set": {"point": point - usedpoint}})
                db.user.update_one({"id": payload['id']}, {"$push": {"post_id": _id}})
            if db.moonchuls.find_one({"Post_log": _id}) is None:
                db.moonchuls.insert_one({"Post_log": _id, "Bpoint": usedpoint})
            else:
                db.moonchuls.update_one({"Post_log": _id}, {"$set": {"Bpoint": Bpoint + usedpoint}}) 
            return jsonify({'result': 'success', 'msg': '정상적으로 결과가 반영되었으며 포인트가 차감되었습니다.'})
        elif user_info is None:
            return jsonify({'result': 'fail', 'msg': '사용자가 존재하지 않습니다. 다시 로그인해주세요.'})
        elif point - usedpoint < 0:
            return jsonify({'result': 'fail', 'msg': '포인트가 부족합니다.'})
        else:
            return jsonify({'result': 'fail', 'msg': '투표 처리에 실패했습니다. 잠시 후 다시 시도해주세요.'})
    except jwt.ExpiredSignatureError:
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})

@app.route('/api/vote_B', methods=['POST'])
def api_voteB():
    token_receive = request.cookies.get('mytoken')
    _id = request.values.get("_id")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"id": payload['id']})
        point = int(user_info['point'])
        usedpoint = int(request.form['usedpoint'])
        Bpoint = 0
        if user_info:
            post_ids = user_info.get('post_id', [])
            if _id in post_ids:  # '특정 값'이 post_ids 리스트 안에 있는지 확인
                return jsonify({'result': 'fail', 'msg': '이미 동일한 이름의 투표에 투표하셨습니다. 중복 투표는 불가합니다.'})
            else:
                db.user.update_one({"id": payload['id']}, {"$set": {"point": point - usedpoint}})
                db.user.update_one({"id": payload['id']}, {"$push": {"post_id": _id}})
            if db.moonchuls.find_one({"Post_log": _id}) is None:
                db.moonchuls.insert_one({"Post_log": _id, "Bpoint": 0})
            else:
                db.moonchuls.update_one({"Post_log": _id}, {"$set": {"Bpoint": Bpoint + usedpoint}}) 

            return jsonify({'result': 'success', 'msg': '정상적으로 결과가 반영되었으며 포인트가 차감되었습니다.'})
        elif user_info is None:
            return jsonify({'result': 'fail', 'msg': '사용자가 존재하지 않습니다. 다시 로그인해주세요.'})
        elif point - usedpoint < 0:
            return jsonify({'result': 'fail', 'msg': '포인트가 부족합니다.'})
        else:
            return jsonify({'result': 'fail', 'msg': '투표 처리에 실패했습니다. 잠시 후 다시 시도해주세요.'})
    except jwt.ExpiredSignatureError:
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})

if __name__ == '__main__':
   app.run('0.0.0.0', port=5000, debug=True)