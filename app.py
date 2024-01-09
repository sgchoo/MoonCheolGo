from flask import Flask, render_template, request, url_for, jsonify, make_response
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
import json
from flask.json.provider import JSONProvider
from bson import ObjectId
import sys

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisissecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)
login_Manager = LoginManager()
login_Manager.init_app(app)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=CustomJSONEncoder)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)


# 위에 정의되 custom encoder 를 사용하게끔 설정한다.
app.json = CustomJSONProvider(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(50))
    email = db.Column(db.String(50))
    role = db.Column(db.String(30))

    def get_id(self):
        return self.id
    def __repr__(self):
        return f"USER: {self.id} = {self.name}"
    
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
           token = request.headers['x-access-token']
        if not token:
           return jsonify({'message': 'Token is missing!'}), 401
        try:
           data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
           current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
           return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@login_Manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/user', methods=['GET'])
@token_required
def get_all_users(current_user):
    if current_user.role != 'user':
        return jsonify({'message': 'Permission denied!'})

    users = User.query.all()
    output = []
    for user in users:
        user_data = {}
        user_data['public_id'] = user.public_id
        user_data['name'] = user.name
        user_data['password'] = user.password
        user_data['email'] = user.email
        user_data['role'] = user.role
        output.append(user_data)
    return jsonify({'users': output})

@app.route('/user/<public_id>', methods=['GET'])
@token_required
def get_one_user(current_user, public_id):
    user = User.query.filter_by(public_id=public_id).first()
    if not user:
        return jsonify({'message': 'No user found!'})
    user_data = {}
    user_data['public_id'] = user.public_id
    user_data['name'] = user.name
    user_data['password'] = user.password
    user_data['email'] = user.email
    user_data['role'] = user.role
    return jsonify({'user': user_data})

@app.route('/user', methods=['POST'])
def create_user(current_user):
    data = request.get_json
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(public_id=str(uuid.uuid4()), name=data['name'], password=hashed_password, email=data['email'], role='user')
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'New user created!'})

# role을 바꿔주는 함수
@app.route('/user/<public_id>', methods=['PUT'])
@token_required
def promote_student(current_user, public_id):
    #student = Student.query.filter_by(public_id=public_id).first() 
    #db.session.commit()
    return '<h1>promote_student - superuser, admin, user</h1>'

@app.route('/user/<public_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, public_id):
    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message': 'No user Found!'})

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'The user has been deleted'})

@app.route('/login')
def login():
    auth = request.authorization
    
    if not auth or not auth.username or not auth.password: #인증되지 않은 사용자일 때
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    user = User.query.filter_by(name=auth.username).first()
    
    if not user: #인증은 됬지만 사용자가 존재하지 않을 경우
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})
    
    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'public_id' : user.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(seconds=100)}, app.config['SECRET_KEY'], algorithm='HS256')
        #seconds ms 100ms -> 1초
        #minutes
        return jsonify({'token': jwt.decode(token, app.config['SECRET_KEY'], algorithms='HS256')}) #DB에 token column만들어서 추가하기 -> DB에 저장된 token조회해서 유효성 검사 효율적으로 해보자


    return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'}) #인증됬고, 사용자가 존재하지만, password가 틀렷을 경우


if __name__ == '__main__':
   app.run('0.0.0.0', port=5000, debug=True)