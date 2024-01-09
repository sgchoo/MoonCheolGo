from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient

app = Flask(__name__)

import requests

from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client.dbmoonchul

db.moonchuls.insert_one({'subject': "짜장면vs짬뽕", 'argument': "짬뽕짜장면",
              'position1': "짬뽕", 'position2': "짜장면"})

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
    print(moonchuls)

    return jsonify({'result': 'success'})

@app.route('/post', methods=['GET'])
def read_moonchuls():
        result = list(db.moonchuls.find_one({'subject'}))
        return jsonify({'result':'success','subjects':result})

if __name__ == '__main__':
     app.run('0,0,0,0', port = 5000, debug = True)