
'''import logging 
import os
from flask import Flask, request, jsonify
from flask_ask import Ask, statement, question, session, delegate
import random
import pymysql
import datetime
import requests
import smtplib'''

app = Flask(__name__)
ask = Ask(app,"/")
logging.getLogger("flask_ask").setLevel(logging.DEBUG)

connection = pymysql.connect(host='localhost',user='root',password='123456789', db='pythonDB')


def getEmail(token, host):
	head = {'Authorization':('Bearer '+ token),
			'Accept':'application/json',
			'Host' : host[8:]#avoid https://
			}
	return requests.get(url = (host + "/v2/accounts/~current/settings/Profile.email"),headers=head).json()

def isPermitted(token,host):
	head = {'Authorization':'Bearer '+ token,
		'Accept':'application/json',
		'Host' : host[8:]#avoid https://
		}
	message = requests.get(url = (host + "/v2/accounts/~current/settings/Profile.email"),headers=head)
	if message.status_code == 200:
		return True
	else:
		return False

def sendMail(mailadress,level):
	print ("send a mail to: ",str(mailadress)," about level: ",level)

@ask.launch
def start():
	req = request.get_json(force=True)
	userId = req['session']['user']['userId']
	apiToken = str(req['context']['System']['apiAccessToken'])
	apiEndpoint = str(req['context']['System']['apiEndpoint'])
	if isPermitted(apiToken,apiEndpoint):
		with connection.cursor() as cursor:
			sql = "SELECT * FROM ecochallenge WHERE id = %s"
			cursor.execute(sql,str(userId))
			result = cursor.fetchall()
		if not result:
			#first time
			welcome_msg = "Welcome to the echo challenge. Tell me when you want to take your daily mission."
		elif result[0][3] != datetime.datetime.now().strftime("%Y-%m-%d"):
			#date check
			welcome_msg = "Welcome to the echo challenge. Tell me when you want to take your daily mission."
		else:
			if int(result[0][4]) == 0:
				with connection.cursor() as cursor:
					sql = "SELECT * FROM challenges WHERE id = %s"
					cursor.execute(sql,int(result[0][2]))
					mission = cursor.fetchall()
				welcome_msg = "Hello " + mission[0][2]
			else:
				print (result)
				welcome_msg = "Hi, thank you to complete daily mission."
		result = None
		mission = None
		return question(welcome_msg)
	else:

		card = {
	  			"version": "1.0",
	  			"response": {
	  				"outputSpeech": {"type":"PlainText","text":"Welcome to the echo challenge. Tell me when you want to take your daily mission. Also I can see that you haven't permit me to access your mail adress. To let me sen your badgets to your mail adress, please use the card in your Alexa app."},
	    			"shouldEndSession": 'false',
	    			"card": {
	      				"type": "AskForPermissionsConsent",
	      				"permissions": [
	        				"alexa::profile:name:read",
	        				"alexa::profile:mobile_number:read",
	        				"alexa::profile:email:read"

	      				]
	   				}
	  			}
			}

	result = None
	mission = None
	return jsonify(card)
	

@ask.intent("dailyMission")
def dailyMission():
	req = request.get_json(force=True)
	userId = req['session']['user']['userId']
	with connection.cursor() as cursor:
		sql = "SELECT * FROM ecochallenge WHERE id = %s"
		cursor.execute(sql,userId)
		result = cursor.fetchall()
		missionID = random.randint(0, 2)
		sql = "SELECT * FROM challenges WHERE id = %s"
		cursor.execute(sql,int(missionID))
		mission = cursor.fetchall() 
				#choosing mission
		if not result:
			#new user
			sql = "INSERT INTO ecochallenge (id, totalPoint, todayMission, missionDate,isDone) VALUES (%s, %s, %s, %s,%s);"
			cursor.execute(sql, (str(userId), int(0), int(missionID), str(datetime.datetime.now().strftime("%Y-%m-%d")),int(0)))
			connection.commit()
			ret_msg = mission[0][1]
			result = None
			mission = None
			return statement(ret_msg)
		else:
			#old user
			if result[0][3] != str(datetime.datetime.now().strftime("%Y-%m-%d")):
				sql = "UPDATE ecochallenge set todayMission = %s, missionDate = %s, isDone = %s WHERE id = %s;"
				cursor.execute(sql, (int(missionID), datetime.datetime.now().strftime("%Y-%m-%d"),int(0), userId))
				connection.commit()
				ret_msg = mission[0][1]
			else:
				missionID = int(result[0][2])
				sql = "SELECT * FROM challenges WHERE id = %s"
				cursor.execute(sql,int(missionID))
				mission = cursor.fetchall()
				if int(result[0][4])==0:
					ret_msg = "It looks you've already got you mission for today and it is " + mission[0][1]
				else:
					ret_msg = "You already done todays mission. Come back tomorrow"
			result = None
			mission = None
			return statement(ret_msg)
@ask.intent("AMAZON.YesIntent")
def missionComplete():
	req = request.get_json(force=True)
	userId = req['session']['user']['userId']
	apiToken = str(req['context']['System']['apiAccessToken'])
	apiEndpoint = str(req['context']['System']['apiEndpoint'])



	with connection.cursor() as cursor:
		sql = "SELECT * FROM ecochallenge WHERE id = %s"
		cursor.execute(sql,userId)
		result = cursor.fetchall()
	if int(result[0][4]) == 0:
		if not result:
			return_msg = "You haven't been assigned for any mission yet. Please ask for mission first"
			result = None
			mission = None
			return question(return_msg)
		elif result[0][3] != datetime.datetime.now().strftime("%Y-%m-%d"):
			return_msg = "Missions are daily! You haven't been assigned for any mission today. Please ask for your new mission first"
			result = None
			mission = None
			return question(return_msg)
		else:
			newTotal = str(int(result[0][1])+1)
			with connection.cursor() as cursor:
				sql = "UPDATE ecochallenge set totalPoint = %s ,isDone = %s WHERE id = %s;"
				cursor.execute(sql, (int(newTotal),int(1), str(userId)))
				return_msg = "Well done! You get 1 more point. Your new total point is " +str(newTotal)
				connection.commit()

			if newTotal == "5":
				# level 2
				if isPermitted(apiToken,apiEndpoint):
					sendMail(getEmail(apiToken,apiEndpoint),2)

				else:
					return_msg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + " Congrulations! You are now at level 2!"
					
				return statement(return_msg).standard_card(title='LEVEL 2',
					text='Congrulations! You are now at Level 2!',
					large_image_url='https://i.imgur.com/9TJOi0y.png')
			elif newTotal == "12":
				# level 3
				if isPermitted(apiToken,apiEndpoint):
					sendMail(getEmail(apiToken,apiEndpoint),3)
					return_msg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "Congrulations! You are now at level 3! Check your inbox and share your badget!"
				
				else:
					return_msg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "Congrulations! You are now at level 3!"
				
				return statement(return_msg).standard_card(title='LEVEL 3',
                       text='Congrulations! You are now at Level 3!',
                       large_image_url='https://a8097910.ngrok.io/Alexa-EcoChallenge/level3.png')
			elif newTotal == "20":
				# level 4
				if isPermitted(apiToken,apiEndpoint):
					sendMail(getEmail(apiToken,apiEndpoint),4)
					return_msg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "Congrulations! You are now at level 4! Check your inbox and share your badget!"
				
				else:
					return_msg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "Congrulations! You are now at level 4!"
				
				return statement(return_msg).standard_card(title='LEVEL 4',
                       text='Congrulations! You are now at Level 4!',
                       large_image_url='https://a8097910.ngrok.io/Alexa-EcoChallenge/level4.png')
			elif newTotal == "30":
				# level 5
				if isPermitted(apiToken,apiEndpoint):
					sendMail(getEmail(apiToken,apiEndpoint),5)
					return_msg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "Congrulations! You are now at level 5! Check your inbox and share your badget!"
				
				else:
					return_msg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "Congrulations! You are now at level 5!"
				
				return statement(return_msg).standard_card(title='LEVEL 5',
                       text='Congrulations! You are now at Level 5!',
                       large_image_url='https://a8097910.ngrok.io/Alexa-EcoChallenge/level5.png')
			elif newTotal == "45":
				# level 6
				if isPermitted(apiToken,apiEndpoint):
					sendMail(getEmail(apiToken,apiEndpoint),6)
					return_msg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "Congrulations! You are now at level 6! Check your inbox and share your badget!"
				
				else:
					return_msg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "Congrulations! You are now at level 6!"
				
				return statement(return_msg).standard_card(title='LEVEL 6',
                       text='Congrulations! You are now at Level 6!',
                       large_image_url='https://a8097910.ngrok.io/Alexa-EcoChallenge/level6.png')
			elif newTotal == "65":
				# level 7
				if isPermitted(apiToken,apiEndpoint):
					sendMail(getEmail(apiToken,apiEndpoint),7)
					return_msg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "Congrulations! You are now at level 7! Check your inbox and share your badget!"
				
				else:
					return_msg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "Congrulations! You are now at level 7!"
				
				return statement(return_msg).standard_card(title='LEVEL 7',
                       text='Congrulations! You are now at Level 7!',
                       large_image_url='https://a8097910.ngrok.io/Alexa-EcoChallenge/level7.png')
			elif newTotal == "90":
				# level 8
				if isPermitted(apiToken,apiEndpoint):
					sendMail(getEmail(apiToken,apiEndpoint),8)
					return_msg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "Congrulations! You are now at level 8! Check your inbox and share your badget!"
				
				else:
					return_msg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "Congrulations! You are now at level 8!"
				
				return statement(return_msg).standard_card(title='LEVEL 8',
                       text='Congrulations! You are now at Level 8!',
                       large_image_url='https://a8097910.ngrok.io/Alexa-EcoChallenge/level8.png')

			result = None
			mission = None
			return statement(return_msg)
	else:
		return_msg = "You already done today's mission anyway. Your total point is " +str(result[0][1])
		return statement(return_msg)




if __name__ == '__main__':
	if 'ASK_VERIFY_REQUESTS' in os.environ:
		verify = str(os.environ.get('ASK_VERIFY_REQUESTS', '')).lower()
		if verify == 'false':
			app.config['ASK_VERIFY_REQUESTS'] = False
	app.run(debug=True)
