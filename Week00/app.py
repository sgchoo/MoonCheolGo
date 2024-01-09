from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.dbmoonchul

@app.route('/')
def home():
    return render_template('main.html')

@app.route('/main', methods=['POST'])
def apply_moonchul():
    subject_receive = request.form['subject_give']
    argument_receive = request.form['argument_give']
    position_1_receive = request.form['position_1_give']
    position_2_receive = request.form['position_2_give']

    moonchuls = {'subject': subject_receive, 'argument': argument_receive,
                 'position1': position_1_receive, 'position2': position_2_receive}
    db.moonchuls.insert_one(moonchuls)
    #print(moonchuls)

    return jsonify({'result': 'success'})

@app.route('/main', methods=['GET'])
def read_moonchuls():
    # find_one 대신 find를 사용하여 모든 문서를 가져오도록 수정
    result = list(db.moonchuls.find())
    
    # 모든 문서의 'subject' 필드를 가져오도록 수정
    subjects = [item['subject'] for item in result]

    return jsonify({'result': 'success', 'subjects': subjects})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)