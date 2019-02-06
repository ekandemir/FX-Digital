import logging
import os
from flask import Flask, request, jsonify
from flask_ask import Ask, statement, question, session, delegate
import time
import pymysql

app = Flask(__name__)
ask = Ask(app,"/")
logging.getLogger("flask_ask").setLevel(logging.DEBUG)

connection = pymysql.connect(host='localhost',user='root',password='123456789', db='pythonDB')

@ask.launch
def start():
	welcomeMsg="Tell me when you go to shower"
	return question(welcomeMsg)

@ask.intent("startShower")
def startShower():
	startTime = time.time()
	req = request.get_json()
	id = req['session']['user']['userId']

	with connection.cursor() as cursor:
		sql = "SELECT * FROM timeAlexa WHERE id = %s"
		cursor.execute(sql,id)
		result = cursor.fetchall()
		if not result:
			sql = "INSERT INTO timeAlexa (id, sTime, eTime) VALUES (%s, %s, %s);"
			cursor.execute(sql, (id, int(startTime), int(0)))
			print("Task added successfully")
			connection.commit()
		else:
			sql = "UPDATE timeAlexa set sTime = %s WHERE id = %s;"
			cursor.execute(sql, (int(startTime),id))
			connection.commit()
		return question("Counter has started")

@ask.intent("finishShower")
def finishShower():
	endTime = time.time()
	req = request.get_json()
	id = req['session']['user']['userId']
	
	with connection.cursor() as cursor:
		sql = "SELECT * FROM timeAlexa WHERE id = %s"
		cursor.execute(sql,id)
		result = cursor.fetchall()
		if not result:
			return question("start first")
		else:
			sql = "UPDATE timeAlexa set eTime = %s WHERE id = %s;"
			cursor.execute(sql, (int(endTime),id))
			connection.commit()
			sql = "SELECT * FROM timeAlexa WHERE id = %s"
			cursor.execute(sql,id)
			result = cursor.fetchall()
			diff = result[0][2] - result[0][1]
			pointMsg =  str(diff)+" seconds"
			return statement(pointMsg)
	
	

if __name__ == '__main__':
	if 'ASK_VERIFY_REQUESTS' in os.environ:
		verify = str(os.environ.get('ASK_VERIFY_REQUESTS', '')).lower()
		if verify == 'false':
			app.config['ASK_VERIFY_REQUESTS'] = False
	app.run(debug=True)
