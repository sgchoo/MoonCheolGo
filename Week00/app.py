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
    db.moonchuls.insert_one({'subject1': subject_1_receive,'subject2': subject_2_receive, 'argument': argument_receive, 'position1': position_1_receive, 'position2': position_2_receive, 'isProceeding': 'True', 'vote1': 0, 'vote2': 0})
    return jsonify({'result': 'success'})


@app.route("/show/proceeding", methods=['GET'])
def show_proceeding_moonchuls():
    result = list(db.moonchuls.find({'isProceeding': 'True'},{'_id':0}))
    return jsonify({'result': 'success', 'moonchuls': result})


@app.route("/show/result", methods=['GET'])
def show_result_moonchuls():
    result = list(db.moonchuls.find({'isProceeding': False},{'_id':0}))
    return jsonify({'result': 'success', 'moonchuls': result})

@app.route("/vote/update", methods=['POST'])
def updateVoteCount():
    idElement = ''
    voteElement = ''
    plusCount = 0
    
    findData = request.form['id']
    
    voteCount = db.moonchuls.find_one({'position1': findData})
    
    
    if voteCount is None:
        voteCount = db.moonchuls.find_one({'position2': findData})
        idElement = 'position2'
    else:
        idElement = 'position1'
    
    if idElement is 'position1':
        plusCount = voteCount['vote1'] + 1
        voteElement = 'vote1'
        
    elif idElement is 'position2':
        plusCount = voteCount['vote2'] + 1
        voteElement = 'vote2'
        
    db.moonchuls.update_one({idElement: findData}, {'$set': {voteElement: plusCount}})
    
    
    return jsonify({'result': 'success'})



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
    