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
    subject_1_receive = request.form['subject_1_give']
    subject_2_receive = request.form['subject_2_give']
    argument_receive = request.form['argument_give']
    position_1_receive = request.form['position_1_give']
    position_2_receive = request.form['position_2_give']
    db.moonchuls.insert_one({'subject1': subject_1_receive,'subject2': subject_2_receive, 'argument': argument_receive, 'position1': position_1_receive, 'position2': position_2_receive, 'isProceeding': 'True'})
    return jsonify({'result': 'success'})


@app.route("/show/proceeding", methods=['GET'])
def show_proceeding_moonchuls():
    result = list(db.moonchuls.find({'isProceeding': 'True'},{'_id':0}))
    return jsonify({'result': 'success', 'moonchuls': result})


@app.route("/show/result", methods=['GET'])
def show_result_moonchuls():
    result = list(db.moonchuls.find({'isProceeding': 'False'},{'_id':0}))
    return jsonify({'result': 'success', 'moonchuls': result})

@app.route('/tog', methods=['POST'])
def toggle_moonchul():
    subject1 = request.form['subject1']

    # 해당 문서의 'isProceeding' 값을 False로 업데이트
    db.moonchuls.update_one({'subject1': subject1}, {'$set': {'isProceeding': 'False'}})

    return jsonify({'result': 'success', 'message': 'Toggle successful'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)