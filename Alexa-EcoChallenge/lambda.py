import boto3
from botocore.vendored import requests
import random
# Get the service resource.
dynamodb = boto3.resource('dynamodb')
userTable = dynamodb.Table('ecoChallenge_user')		#	{ [userID] , [dateMission] , [mission] , [isDone] , [totalPoint] }
missionTable = dynamodb.Table('ecoChallenge_mission')	#  { [missionID] , [mission] , [question] }
def lambda_handler(event, context):
	if event['request']['type'] == "LaunchRequest":
		return launch(event)
	elif event['request']['type']=="IntentRequest":
		if event['request']['intent']['name'] == "dailyMission":
			return dailyMission(event)
		elif event['request']['intent']['name'] == "AMAZON.YesIntent":
			return yesIntent(event)
		elif event['request']['intent']['name'] == "AMAZON.NoIntent":
			return noIntent()
		elif event['request']['intent']['name'] == "AMAZON.StopIntent":
			return stopIntent()
		elif event['request']['intent']['name'] == "AMAZON.CancelIntent":
			return stopIntent()
		elif event['request']['intent']['name'] == "AMAZON.HelpIntent":
			return helpIntent()
	return wrongIntent(event)


#<-------------------INTENT: L A U N C H ------------------>
def launch(event):
	user = userTable.get_item(Key = {'userID':event['session']['user']['userId']})
	
	if isPermitted(event['context']['System']['apiAccessToken'],event['context']['System']['apiEndpoint']):#did user permit mail adress usage.
		#with permission
		

		if not 'Item' in user:
			#first user
			welcome_msg = "Welcome to eco challenge. Tell me when you want to take your daily mission."
		elif user['Item']['dateMission'] != event['request']['timestamp'][:10]:
			#old mission
			welcome_msg = "Welcome to eco challenge. Tell me when you want to take your daily mission."
		else:
			if user['Item']['isDone'] == 0:
				#havent done todays mission
				mission = missionTable.get_item(Key = {'missionID':str(user['Item']['mission'])})
				welcome_msg = "Hello. " + mission['Item']['question']
			else:
				# done todays mission
				welcome_msg = "Hi, thank you for completing daily mission. Come again tomorrow to get another one."
				return buildResponse({},buildSpeechletResponse(welcome_msg,welcome_msg,'True',hasDisplay(event)))
		return buildResponse({},buildSpeechletResponse(welcome_msg,welcome_msg,'False',hasDisplay(event)))
	else:
		#without information
		if not 'Item' in user:
			#first user -SEND PERM CARD
			welcome_msg="Welcome to eco challenge. Tell me when you want to take your daily mission. Also I can see that you haven't given me permissions to access your email address. To let me send your badges to your email address, please use the card in your Alexa app."
			card = {
						"type": "AskForPermissionsConsent",
						"permissions": [
						"alexa::profile:email:read"

						]
						}
			return buildResponse({},buildCardResponse(welcome_msg,card,welcome_msg,'False',hasDisplay(event)))
		if user['Item']['dateMission'] != event['request']['timestamp'][:10]:
			#old mission -SEND PERM CARD
			welcome_msg="Welcome to eco challenge. Tell me when you want to take your daily mission. Also I can see that you haven't given me permissions to access your email address. To let me send your badges to your email address, please use the card in your Alexa app."
			card = {
						"type": "AskForPermissionsConsent",
						"permissions": [
						"alexa::profile:email:read"

						]
						}
			return buildResponse({},buildCardResponse(welcome_msg,card,welcome_msg,'False',hasDisplay(event)))
	
		else:
			if user['Item']['isDone'] == 0:
				#havent done todays mission
				mission = missionTable.get_item(Key = {'missionID':str(user['Item']['mission'])})
				welcome_msg = "Hello. " + mission['Item']['question']
			else:
				#done todays mission
				welcome_msg = "Hi, thank you for completing your daily mission. Come again tomorrow to get another one."
				return buildResponse({},buildSpeechletResponse(welcome_msg,welcome_msg,'True',hasDisplay(event)))
		return buildResponse({},buildSpeechletResponse(welcome_msg,welcome_msg,'False',hasDisplay(event)))
#<+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++>


#<---------------INTENT: D A I L Y	M I S S I O N --------------->
def dailyMission(event):
	user = userTable.get_item(Key = {'userID':event['session']['user']['userId']})
	if not 'Item' in user:
		#new user
		missionID = random.randint(0, 16)
		mission = missionTable.get_item(Key = {'missionID':str(missionID)})
		userTable.put_item( Item = {
			'userID' : event['session']['user']['userId'],
			'dateMission' : event['request']['timestamp'][:10],
			'mission' : missionID,
			'isDone' : 0,
			'totalPoint' :0
			} )#create item on db
		retMsg = mission['Item']['mission']

	elif user['Item']['dateMission'] != event['request']['timestamp'][:10]:
		#old mission
		missionID = random.randint(0, 16)
		mission = missionTable.get_item(Key = {'missionID':str(missionID)})
		userTable.update_item(Key = {'userID' : event['session']['user']['userId']},
			UpdateExpression='SET mission = :misID , isDone = :zero, dateMission = :daMi',
			ExpressionAttributeValues={
					':misID' : missionID,
					':daMi' : event['request']['timestamp'][:10],
					':zero' :0
			} )#update item
		retMsg = mission['Item']['mission'] + ". Come later again to answer."


	else:
		#mission is done
		if user['Item']['isDone'] != 0:
			retMsg = "You have already done today's mission. Come back tomorrow"
		else:
			mission = missionTable.get_item(Key = {'missionID':str(user['Item']['mission'])})
			retMsg = "It looks you've already got your mission for today and it is " + mission['Item']['mission']


	return buildResponse({},buildSpeechletResponse(retMsg,retMsg,'True',hasDisplay(event)))
#<++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++>


#<--------------------INTENT: Y E S  I N T E N T ----------------->
def yesIntent(event):
	user = userTable.get_item(Key = {'userID':event['session']['user']['userId']})
	returnMsg = ""
	if not 'Item' in user:
		#new user
		returnMsg = "You haven't been assigned for any mission yet. Please ask for the mission first"
	elif user['Item']['dateMission'] != event['request']['timestamp'][:10]:
		#old mission
		returnMsg = "Missions are daily! You haven't been assigned for any mission today. Please ask for your new mission first"
	else:
		if user['Item']['isDone'] == 0:
			print(user['Item']['isDone'])
			newTotal = int(user['Item']['totalPoint']) + 1

			userTable.update_item(Key = {'userID' : event['session']['user']['userId']},
				UpdateExpression='SET totalPoint = :totPo , isDone = :one',
				ExpressionAttributeValues={
					':totPo' : newTotal,
					':one' : 1
				} )#update item
			if newTotal == 5:
				# level 2
				if isPermitted(event['context']['System']['apiAccessToken'],event['context']['System']['apiEndpoint']):
					sendMail(getEmail(event['context']['System']['apiAccessToken'],event['context']['System']['apiEndpoint']),2)
					returnMsg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + ". Congratulations! You are now at level 2! Check your inbox and share your badge!"
				else:
					returnMsg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + ". Congratulations! You are now at level 2!"

				card = {
					"type": "Standard",
					"title": "LEVEL 2",
					"text": "Congratulations! You are now at level 2!",
					"image": {
						"smallImageUrl": "https://s3-eu-west-1.amazonaws.com/alexaecochallenge/level2.png",
						"largeImageUrl": "https://s3-eu-west-1.amazonaws.com/alexaecochallenge/level2.png"
					}
				}

				return buildResponse({},buildCardResponse(returnMsg, card, returnMsg, 'True',hasDisplay(event)))

			elif newTotal == 12:
				# level 3
				if isPermitted(event['context']['System']['apiAccessToken'],event['context']['System']['apiEndpoint']):
					sendMail(getEmail(event['context']['System']['apiAccessToken'],event['context']['System']['apiEndpoint']),3)
					returnMsg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "! Congratulations! You are now at level 3! Check your inbox and share your badge!"
				
				else:
					returnMsg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "! Congratulations! You are now at level 3!"
				card = {
					"type": "Standard",
					"title": "LEVEL 3",
					"text": "Congratulations! You are now at level 3!",
					"image": {
						"smallImageUrl": "https://s3-eu-west-1.amazonaws.com/alexaecochallenge/level3.png",
						"largeImageUrl": "https://s3-eu-west-1.amazonaws.com/alexaecochallenge/level3.png"
					}
				}

				return buildResponse({},buildCardResponse(returnMsg, card, returnMsg, 'True',hasDisplay(event)))
			elif newTotal == 20:
				# level 4
				if isPermitted(event['context']['System']['apiAccessToken'],event['context']['System']['apiEndpoint']):
					sendMail(getEmail(event['context']['System']['apiAccessToken'],event['context']['System']['apiEndpoint']),4)
					returnMsg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "! Congratulations! You are now at level 4! Check your inbox and share your badge!"
				
				else:
					returnMsg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "! Congratulations! You are now at level 4!"
				card = {
					"type": "Standard",
					"title": "LEVEL 4",
					"text": "Congratulations! You are now at level 4!",
					"image": {
						"smallImageUrl": "https://s3-eu-west-1.amazonaws.com/alexaecochallenge/level4.png",
						"largeImageUrl": "https://s3-eu-west-1.amazonaws.com/alexaecochallenge/level4.png"
					}
				}

				return buildResponse({},buildCardResponse(returnMsg, card, returnMsg, 'True',hasDisplay(event)))
			elif newTotal == 30:
				# level 5
				if isPermitted(event['context']['System']['apiAccessToken'],event['context']['System']['apiEndpoint']):
					sendMail(getEmail(event['context']['System']['apiAccessToken'],event['context']['System']['apiEndpoint']),5)
					returnMsg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "! Congratulations! You are now at level 5! Check your inbox and share your badge!"
				
				else:
					returnMsg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "! Congratulations! You are now at level 5!"
				card = {
					"type": "Standard",
					"title": "LEVEL 5",
					"text": "Congratulations! You are now at level 5!",
					"image": {
						"smallImageUrl": "https://s3-eu-west-1.amazonaws.com/alexaecochallenge/level5.png",
						"largeImageUrl": "https://s3-eu-west-1.amazonaws.com/alexaecochallenge/level5.png"
					}
				}

				return buildResponse({},buildCardResponse(returnMsg, card, returnMsg, 'True',hasDisplay(event)))
			elif newTotal == 45:
				# level 6
				if isPermitted(event['context']['System']['apiAccessToken'],event['context']['System']['apiEndpoint']):
					sendMail(getEmail(event['context']['System']['apiAccessToken'],event['context']['System']['apiEndpoint']),6)
					returnMsg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "! Congratulations! You are now at level 6! Check your inbox and share your badge!"
				
				else:
					returnMsg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "! Congratulations! You are now at level 6!"
				card = {
					"type": "Standard",
					"title": "LEVEL 6",
					"text": "Congratulations! You are now at level 6!",
					"image": {
						"smallImageUrl": "https://s3-eu-west-1.amazonaws.com/alexaecochallenge/level6.png",
						"largeImageUrl": "https://s3-eu-west-1.amazonaws.com/alexaecochallenge/level6.png"
					}
				}

				return buildResponse({},buildCardResponse(returnMsg, card, returnMsg, 'True',hasDisplay(event)))
			elif newTotal == 65:
				# level 7
				if isPermitted(event['context']['System']['apiAccessToken'],event['context']['System']['apiEndpoint']):
					sendMail(getEmail(event['context']['System']['apiAccessToken'],event['context']['System']['apiEndpoint']),7)
					returnMsg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "! Congratulations! You are now at level 7! Check your inbox and share your badge!"
				
				else:
					returnMsg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "! Congratulations! You are now at level 7!"
				card = {
					"type": "Standard",
					"title": "LEVEL 7",
					"text": "Congratulations! You are now at level 7!",
					"image": {
						"smallImageUrl": "https://s3-eu-west-1.amazonaws.com/alexaecochallenge/level7.png",
						"largeImageUrl": "https://s3-eu-west-1.amazonaws.com/alexaecochallenge/level7.png"
					}
				}

				return buildResponse({},buildCardResponse(returnMsg, card, returnMsg, 'True',hasDisplay(event)))
			elif newTotal == 90:
				# level 8
				if isPermitted(event['context']['System']['apiAccessToken'],event['context']['System']['apiEndpoint']):
					sendMail(getEmail(event['context']['System']['apiAccessToken'],event['context']['System']['apiEndpoint']),8)
					returnMsg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "! Congratulations! You are now at level 8! Check your inbox and share your badge!"
				
				else:
					returnMsg = "Well done! You get 1 more point. Your new total point is " +str(newTotal) + "! Congratulations! You are now at level 8!"
				card = {
					"type": "Standard",
					"title": "LEVEL 8",
					"text": "Congratulations! You are now at level 8!",
					"image": {
						"smallImageUrl": "https://s3-eu-west-1.amazonaws.com/alexaecochallenge/level8.png",
						"largeImageUrl": "https://s3-eu-west-1.amazonaws.com/alexaecochallenge/level8.png"
					}
				}

				return buildResponse({}, buildCardResponse(returnMsg, card, returnMsg, 'True',hasDisplay(event)))
			else:
				returnMsg = "Well done! You get 1 more point. Your new total point is " +str(newTotal)


		else:
			#mission completed earlier
			returnMsg = "You have already done today's mission anyway. Your total point is " +str(user['Item']['totalPoint'])
	return buildResponse({},buildSpeechletResponse(returnMsg,returnMsg,'True',hasDisplay(event)))
		
#<++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++>

#<--------------------INTENT: N O   I N T E N T ------------------>
def noIntent():
	returnMsg = "Come on champion!!! You can do this! Do not forget that small changes in our lives will bring us a great environment!"
	return buildResponse({},buildSpeechletResponse(returnMsg,returnMsg,'True',hasDisplay(event)))

#<++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++>



#<-------------------WRONG INTENTS ------------------------------->
def wrongIntent(event):
	user = userTable.get_item(Key = {'userID':event['session']['user']['userId']})
	if not 'Item' in user:
		#new user
		returnMsg = "I could not understand what you said exactly, but you can ask for a mission and you can start to be a eco challenger"
	elif user['Item']['dateMission'] != event['request']['timestamp'][:10]:
		#old mission
		returnMsg = "I could not understand what you said exactly, but you can ask for a new mission."
	else:
		if user['Item']['isDone'] != 0:
			#done todays mission
			returnMsg = "I could not understand what you said exactly, but looks like you already done today's mission. Come back tomorrow to get new mission"
		else:
			#havent done todays mission
			returnMsg = "I could not understand what you said exactly, but looks like you haven't done today's mission. Tell me when you have done. Do not forget that small changes in our lives will bring us a great environment!"

	return buildResponse({},buildSpeechletResponse(returnMsg,returnMsg,'False',hasDisplay(event)))

#<++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++>




#<---------------------INTENT: S T O P --------------------------->
def stopIntent():
	returnMsg = "Okay, see you later!"
	return buildResponse({},buildSpeechletResponse(returnMsg,returnMsg,'True',hasDisplay(event)))
#<++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++>



#<---------------------INTENT: H E L P --------------------------->
def helpIntent():
	returnMsg = "Missions are daily. You can not complete more than one mission in a day. You can ask for a mission by saying tell my mission. After you completed the mission you can confirm it by saying I did."
	return buildResponse({},buildSpeechletResponse(returnMsg,returnMsg,'False',hasDisplay(event)))
#<++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++>


#<--------- E-MAIL ACCESS FUNCS----------------->
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
	SENDER = "erdinc@fxdigital.uk"
	RECIPIENT = mailadress
	#CONFIGURATION_SET = "ConfigSet"
	AWS_REGION = "eu-west-1"
	SUBJECT = "[Eco Challenge]Congratulations! Level " + str(level)

	BODY_HTML = htmlify(level)
	CHARSET = "UTF-8"
	client = boto3.client('ses',region_name="eu-west-1")
	#Provide the contents of the email.
	response = client.send_email(
		Destination={
			'ToAddresses': [
				RECIPIENT,
			],
		},
		Message={
			'Body': {
				'Html': {
					'Charset': CHARSET,
					'Data': BODY_HTML,
				},
			},
			'Subject': {
				'Charset': CHARSET,
				'Data': SUBJECT,
			},
		},
		Source=SENDER,
		# If you are not using a configuration set, comment or delete the
		# following line
		#ConfigurationSetName=CONFIGURATION_SET,
	)

	return
def htmlify(level):
	htmled = """
	<!DOCTYPE HTML PUBLIC "-//W3C//DTD XHTML 1.0 Transitional //EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
	<!--[if gte mso 9]><xml>
	 <o:OfficeDocumentSettings>
	  <o:AllowPNG/>
	  <o:PixelsPerInch>96</o:PixelsPerInch>
	 </o:OfficeDocumentSettings>
	</xml><![endif]-->
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
	<meta name="viewport" content="width=device-width">
	<!--[if !mso]><!--><meta http-equiv="X-UA-Compatible" content="IE=edge"><!--<![endif]-->
	<title>eco challenge</title>
	<!--[if !mso]><!-- -->
	<link href="https://fonts.googleapis.com/css?family=Oswald" rel="stylesheet" type="text/css">
	<link href="https://fonts.googleapis.com/css?family=Open+Sans" rel="stylesheet" type="text/css">
	<!--<![endif]-->

	<style type="text/css" id="media-query">
		body {
			margin: 0;
			padding: 0;
		}

		table, tr, td {
			vertical-align: top;
			border-collapse: collapse;
		}

		.ie-browser table, .mso-container table {
			table-layout: fixed;
		}

		* {
			line-height: inherit;
		}

		a[x-apple-data-detectors=true] {
			color: inherit !important;
			text-decoration: none !important;
		}

		[owa] .img-container div, [owa] .img-container button {
			display: block !important;
		}

		[owa] .fullwidth button {
			width: 100% !important;
		}

		[owa] .block-grid .col {
			display: table-cell;
			float: none !important;
			vertical-align: top;
		}

		.ie-browser .num12, .ie-browser .block-grid, [owa] .num12, [owa] .block-grid {
			width: 675px !important;
		}

		.ExternalClass, .ExternalClass p, .ExternalClass span, .ExternalClass font, .ExternalClass td, .ExternalClass div {
			line-height: 100%;
		}

		.ie-browser .mixed-two-up .num4, [owa] .mixed-two-up .num4 {
			width: 224px !important;
		}

		.ie-browser .mixed-two-up .num8, [owa] .mixed-two-up .num8 {
			width: 448px !important;
		}

		.ie-browser .block-grid.two-up .col, [owa] .block-grid.two-up .col {
			width: 337px !important;
		}

		.ie-browser .block-grid.three-up .col, [owa] .block-grid.three-up .col {
			width: 225px !important;
		}

		.ie-browser .block-grid.four-up .col, [owa] .block-grid.four-up .col {
			width: 168px !important;
		}

		.ie-browser .block-grid.five-up .col, [owa] .block-grid.five-up .col {
			width: 135px !important;
		}

		.ie-browser .block-grid.six-up .col, [owa] .block-grid.six-up .col {
			width: 112px !important;
		}

		.ie-browser .block-grid.seven-up .col, [owa] .block-grid.seven-up .col {
			width: 96px !important;
		}

		.ie-browser .block-grid.eight-up .col, [owa] .block-grid.eight-up .col {
			width: 84px !important;
		}

		.ie-browser .block-grid.nine-up .col, [owa] .block-grid.nine-up .col {
			width: 75px !important;
		}

		.ie-browser .block-grid.ten-up .col, [owa] .block-grid.ten-up .col {
			width: 67px !important;
		}

		.ie-browser .block-grid.eleven-up .col, [owa] .block-grid.eleven-up .col {
			width: 61px !important;
		}

		.ie-browser .block-grid.twelve-up .col, [owa] .block-grid.twelve-up .col {
			width: 56px !important;
		}

		@media only screen and (min-width: 695px) {
		  .block-grid {
			width: 675px !important; }
		  .block-grid .col {
			vertical-align: top; }
			.block-grid .col.num12 {
			  width: 675px !important; }
		  .block-grid.mixed-two-up .col.num4 {
			width: 224px !important; }
		  .block-grid.mixed-two-up .col.num8 {
			width: 448px !important; }
		  .block-grid.two-up .col {
			width: 337px !important; }
		  .block-grid.three-up .col {
			width: 225px !important; }
		  .block-grid.four-up .col {
			width: 168px !important; }
		  .block-grid.five-up .col {
			width: 135px !important; }
		  .block-grid.six-up .col {
			width: 112px !important; }
		  .block-grid.seven-up .col {
			width: 96px !important; }
		  .block-grid.eight-up .col {
			width: 84px !important; }
		  .block-grid.nine-up .col {
			width: 75px !important; }
		  .block-grid.ten-up .col {
			width: 67px !important; }
		  .block-grid.eleven-up .col {
			width: 61px !important; }
		  .block-grid.twelve-up .col {
			width: 56px !important; } }

		@media (max-width: 695px) {
		  .block-grid, .col {
			min-width: 320px !important;
			max-width: 100% !important;
			display: block !important; }
		  .block-grid {
			width: calc(100% - 40px) !important; }
		  .col {
			width: 100% !important; }
			.col > div {
			  margin: 0 auto; }
		  img.fullwidth, img.fullwidthOnMobile {
			max-width: 100% !important; }
		  .no-stack .col {
			min-width: 0 !important;
			display: table-cell !important; }
		  .no-stack.two-up .col {
			width: 50% !important; }
		  .no-stack.mixed-two-up .col.num4 {
			width: 33% !important; }
		  .no-stack.mixed-two-up .col.num8 {
			width: 66% !important; }
		  .no-stack.three-up .col.num4 {
			width: 33% !important; }
		  .no-stack.four-up .col.num3 {
			width: 25% !important; }
		  .mobile_hide {
			min-height: 0px;
			max-height: 0px;
			max-width: 0px;
			display: none;
			overflow: hidden;
			font-size: 0px; }
		}
	</style>
</head>
<body class="clean-body" style="margin: 0;padding: 0;-webkit-text-size-adjust: 100%;background-color: #FFFFFF">
	<style type="text/css" id="media-query-bodytag">
		@media (max-width: 520px) {
		  .block-grid {
			min-width: 320px!important;
			max-width: 100%!important;
			width: 100%!important;
			display: block!important;
		  }

		  .col {
			min-width: 320px!important;
			max-width: 100%!important;
			width: 100%!important;
			display: block!important;
		  }

			.col > div {
			  margin: 0 auto;
			}

		  img.fullwidth {
			max-width: 100%!important;
		  }
				img.fullwidthOnMobile {
			max-width: 100%!important;
		  }
		  .no-stack .col {
					min-width: 0!important;
					display: table-cell!important;
				}
				.no-stack.two-up .col {
					width: 50%!important;
				}
				.no-stack.mixed-two-up .col.num4 {
					width: 33%!important;
				}
				.no-stack.mixed-two-up .col.num8 {
					width: 66%!important;
				}
				.no-stack.three-up .col.num4 {
					width: 33%!important;
				}
				.no-stack.four-up .col.num3 {
					width: 25%!important;
				}
		  .mobile_hide {
			min-height: 0px!important;
			max-height: 0px!important;
			max-width: 0px!important;
			display: none!important;
			overflow: hidden!important;
			font-size: 0px!important;
		  }
		}
	</style>
	<!--[if IE]><div class="ie-browser"><![endif]-->
	<!--[if mso]><div class="mso-container"><![endif]-->
	<table class="nl-container" style="border-collapse: collapse;table-layout: fixed;border-spacing: 0;mso-table-lspace: 0pt;mso-table-rspace: 0pt;vertical-align: top;min-width: 320px;Margin: 0 auto;background-color: #FFFFFF;width: 100%" cellpadding=0 cellspacing=0>
		<tbody>
			<tr style="vertical-align: top">
				<td style="word-break: break-word;border-collapse: collapse !important;vertical-align: top">
					<!--[if (mso)|(IE)]><table width="100%" cellpadding=0 cellspacing=0 border=0><tr><td align="center" style="background-color: #FFFFFF;"><![endif]-->

					<div style="background-color:#40e0d4;">
						<div style="Margin: 0 auto;min-width: 320px;max-width: 675px;overflow-wrap: break-word;word-wrap: break-word;word-break: break-word;background-color: transparent;" class="block-grid ">
							<div style="border-collapse: collapse;display: table;width: 100%;background-color:transparent;">
								<!--[if (mso)|(IE)]><table width="100%" cellpadding=0 cellspacing=0 border=0><tr><td style="background-color:#40e0d4;" align="center"><table cellpadding=0 cellspacing=0 border=0 style="width: 675px;"><tr class="layout-full-width" style="background-color:transparent;"><![endif]-->

								<!--[if (mso)|(IE)]><td align="center" width="675" style=" width:675px; padding-right: 0px; padding-left: 0px; padding-top:5px; padding-bottom:5px; border-top: 0px solid transparent; border-left: 0px solid transparent; border-bottom: 0px solid transparent; border-right: 0px solid transparent;" valign="top"><![endif]-->
								<div class="col num12" style="min-width: 320px;max-width: 675px;display: table-cell;vertical-align: top;">
									<div style="background-color: transparent; width: 100% !important;">
									<!--[if (!mso)&(!IE)]><!--><div style="border-top: 0px solid transparent; border-left: 0px solid transparent; border-bottom: 0px solid transparent; border-right: 0px solid transparent; padding-top:5px; padding-bottom:5px; padding-right: 0px; padding-left: 0px;"><!--<![endif]-->


									<div align="center" class="img-container center  autowidth  " style="padding-right: 0px;  padding-left: 0px;">
										<!--[if mso]><table width="100%" cellpadding=0 cellspacing=0 border=0><tr style="line-height:0px;line-height:0px;"><td style="padding-right: 0px; padding-left: 0px;" align="center"><![endif]-->
										<div style="line-height:60px;font-size:1px">&#160;</div>  <img class="center  autowidth " align="center" border=0 src="https://s3-eu-west-1.amazonaws.com/alexaecochallenge/mail-header.png" alt="" title="" style="outline: none;text-decoration: none;-ms-interpolation-mode: bicubic;clear: both;display: block !important;border: 0;height: auto;float: none;width: 100%;max-width: 577px" width="577">
										<div style="line-height:60px;font-size:1px">&#160;</div><!--[if mso]></td></tr></table><![endif]-->
									</div>


									<!--[if (!mso)&(!IE)]><!--></div><!--<![endif]-->
									</div>
								</div>
								<!--[if (mso)|(IE)]></td></tr></table></td></tr></table><![endif]-->
							</div>
						</div>
					</div>
					<div style="background-color:#d7f2e4;">
						<div style="Margin: 0 auto;min-width: 320px;max-width: 675px;overflow-wrap: break-word;word-wrap: break-word;word-break: break-word;background-color: transparent;" class="block-grid ">
							<div style="border-collapse: collapse;display: table;width: 100%;background-color:transparent;">
								<!--[if (mso)|(IE)]><table width="100%" cellpadding=0 cellspacing=0 border=0><tr><td style="background-color:#d7f2e4;" align="center"><table cellpadding=0 cellspacing=0 border=0 style="width: 675px;"><tr class="layout-full-width" style="background-color:transparent;"><![endif]-->

								<!--[if (mso)|(IE)]><td align="center" width="675" style=" width:675px; padding-right: 0px; padding-left: 0px; padding-top:5px; padding-bottom:60px; border-top: 0px solid transparent; border-left: 0px solid transparent; border-bottom: 0px solid transparent; border-right: 0px solid transparent;" valign="top"><![endif]-->
								<div class="col num12" style="min-width: 320px;max-width: 675px;display: table-cell;vertical-align: top;">
									<div style="background-color: transparent; width: 100% !important;">
										<!--[if (!mso)&(!IE)]><!--><div style="border-top: 0px solid transparent; border-left: 0px solid transparent; border-bottom: 0px solid transparent; border-right: 0px solid transparent; padding-top:5px; padding-bottom:60px; padding-right: 0px; padding-left: 0px;"><!--<![endif]-->


										<div class="">
											   <!--[if mso]><table width="100%" cellpadding=0 cellspacing=0 border=0><tr><td style="padding-right: 10px; padding-left: 10px; padding-top: 60px; padding-bottom: 0px;"><![endif]-->
												<div style="color:#01030f;font-family:'Oswald', Arial, 'Helvetica Neue', Helvetica, sans-serif;line-height:120%; padding-right: 10px; padding-left: 10px; padding-top: 60px; padding-bottom: 0px;">
													<div style="font-size:16px;line-height:19px;font-family:Oswald, Arial, 'Helvetica Neue', Helvetica, sans-serif;color:#01030f;text-align:left;">
														<p style="margin: 0;font-size: 16px;line-height: 19px;text-align: center">
															<span style="line-height: 40px; font-size: 34px;">Congratulations! You are now Level """+str(level)+"""</span>
														</p>
													</div>
												</div>
												<!--[if mso]></td></tr></table><![endif]-->
										</div>


										<div align="center" class="img-container center  autowidth  " style="padding-right: 0px;  padding-left: 0px;">
											<!--[if mso]><table width="100%" cellpadding=0 cellspacing=0 border=0><tr style="line-height:0px;line-height:0px;"><td style="padding-right: 0px; padding-left: 0px;" align="center"><![endif]-->
											<div style="line-height:50px;font-size:1px">&#160;</div>
											<img class="center  autowidth " align="center" border=0 src="https://s3-eu-west-1.amazonaws.com/alexaecochallenge/level"""+str(level)+""".png" alt="level image" title="level image" style="outline: none;text-decoration: none;-ms-interpolation-mode: bicubic;clear: both;display: block !important;border: 0;height: auto;float: none;width: 100%;max-width: 277px" width="277">
											<!--[if mso]></td></tr></table><![endif]-->
										</div>
										<!--[if (!mso)&(!IE)]><!--></div><!--<![endif]-->
									</div>
								</div>
								<!--[if (mso)|(IE)]></td></tr></table></td></tr></table><![endif]-->
							</div>
						</div>
					</div>
					<div style="background-color:#40e0d4;">
						<div style="Margin: 0 auto;min-width: 320px;max-width: 675px;overflow-wrap: break-word;word-wrap: break-word;word-break: break-word;background-color: transparent;" class="block-grid ">
							<div style="border-collapse: collapse;display: table;width: 100%;background-color:transparent;">
								<!--[if (mso)|(IE)]><table width="100%" cellpadding=0 cellspacing=0 border=0><tr><td style="background-color:#40e0d4;" align="center"><table cellpadding=0 cellspacing=0 border=0 style="width: 675px;"><tr class="layout-full-width" style="background-color:transparent;"><![endif]-->

								<!--[if (mso)|(IE)]><td align="center" width="675" style=" width:675px; padding-right: 0px; padding-left: 0px; padding-top:0px; padding-bottom:30px; border-top: 0px solid transparent; border-left: 0px solid transparent; border-bottom: 0px solid transparent; border-right: 0px solid transparent;" valign="top"><![endif]-->
								<div class="col num12" style="min-width: 320px;max-width: 675px;display: table-cell;vertical-align: top;">
									<div style="background-color: transparent; width: 100% !important;">
										<!--[if (!mso)&(!IE)]><!--><div style="border-top: 0px solid transparent; border-left: 0px solid transparent; border-bottom: 0px solid transparent; border-right: 0px solid transparent; padding-top:0px; padding-bottom:30px; padding-right: 0px; padding-left: 0px;"><!--<![endif]-->


										<div class="">
											<!--[if mso]><table width="100%" cellpadding=0 cellspacing=0 border=0><tr><td style="padding-right: 0px; padding-left: 0px; padding-top: 60px; padding-bottom: 0px;"><![endif]-->
											<div style="color:#FFFFFF;font-family:'Oswald', Arial, 'Helvetica Neue', Helvetica, sans-serif;line-height:120%; padding-right: 0px; padding-left: 0px; padding-top: 60px; padding-bottom: 0px;">
											  <div style="font-family:Oswald, Arial, 'Helvetica Neue', Helvetica, sans-serif;font-size:12px;line-height:14px;color:#FFFFFF;text-align:left;">
												  <p style="margin: 0;font-size: 18px;line-height: 22px;text-align: center">
													  <span style="line-height: 40px; font-size: 34px;">Thanks for your contributions for a great environment</span>
												  </p>
											  </div>
											</div>
											<!--[if mso]></td></tr></table><![endif]-->
										</div>


										<div class="">
										   <!--[if mso]><table width="100%" cellpadding=0 cellspacing=0 border=0><tr><td style="padding-right: 0px; padding-left: 0px; padding-top: 33px; padding-bottom: 0px;"><![endif]-->
										   <div style="color:#FFFFFF;font-family:'Open Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;line-height:120%; padding-right: 0px; padding-left: 0px; padding-top: 33px; padding-bottom: 0px;">
												<div style="font-size:12px;line-height:14px;font-family:'Open Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;color:#FFFFFF;text-align:left;">
													<p style="margin: 0;font-size: 14px;line-height: 17px;text-align: center">
														<span style="font-size: 24px; line-height: 28px;">You proved that you are a real Eco Challenger</span>
													</p>
												</div>
											</div>
											<!--[if mso]></td></tr></table><![endif]-->
										</div>
										<div align="center" class="button-container center " style="padding-right: 0px; padding-left: 0px; padding-top:43px; padding-bottom:0px;">
										  <!--[if mso]><table width="100%" cellpadding=0 cellspacing=0 border=0 style="border-spacing: 0; border-collapse: collapse; mso-table-lspace:0pt; mso-table-rspace:0pt;"><tr><td style="padding-right: 0px; padding-left: 0px; padding-top:43px; padding-bottom:0px;" align="center"><v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="" style="height:43pt; v-text-anchor:middle; width:196pt;" arcsize="52%" strokecolor="#3b5998" fillcolor="#3b5998"><w:anchorlock/><v:textbox inset="0,0,0,0"><center style="color:#ffffff; font-family:'Oswald', Arial, 'Helvetica Neue', Helvetica, sans-serif; font-size:24px;"><![endif]-->
											 <a href="https://www.facebook.com/sharer/sharer.php?kid_directed_site=0&u=https%3A%2F%2Fs3-eu-west-1.amazonaws.com%2Falexaecochallenge%2Findex%2Flevel"""+str(level)+""".html&display=popup&ref=plugin&src=share_button" target="_blank" style="display: block;text-decoration: none;-webkit-text-size-adjust: none;text-align: center;color: #ffffff; background-color: #3b5998; border-radius: 30px; -webkit-border-radius: 30px; -moz-border-radius: 30px; max-width: 665px; width: 35%; border-top: 0px solid transparent; border-right: 0px solid transparent; border-bottom: 0px solid transparent; border-left: 0px solid transparent; padding-top: 5px; padding-right: 5px; padding-bottom: 5px; padding-left: 5px; font-family: 'Oswald', Arial, 'Helvetica Neue', Helvetica, sans-serif;mso-border-alt: none">
	  <span style="font-family:'Oswald', Arial, 'Helvetica Neue', Helvetica, sans-serif;font-size:16px;line-height:32px;"><span style="font-size: 24px; line-height: 48px;">SHARE ON FACEBOOK</span></span>
	</a>
										  <!--[if mso]></center></v:textbox></v:roundrect></td></tr></table><![endif]-->
										</div>
										<!--[if (!mso)&(!IE)]><!--></div><!--<![endif]-->
										</div>
									</div>
									<!--[if (mso)|(IE)]></td></tr></table></td></tr></table><![endif]-->
								</div>
							</div>
						</div>
						<div style="background-color:#F0F0F0;">
						  <div style="Margin: 0 auto;min-width: 320px;max-width: 675px;overflow-wrap: break-word;word-wrap: break-word;word-break: break-word;background-color: transparent;" class="block-grid ">
							<div style="border-collapse: collapse;display: table;width: 100%;background-color:transparent;">
							  <!--[if (mso)|(IE)]><table width="100%" cellpadding=0 cellspacing=0 border=0><tr><td style="background-color:#F0F0F0;" align="center"><table cellpadding=0 cellspacing=0 border=0 style="width: 675px;"><tr class="layout-full-width" style="background-color:transparent;"><![endif]-->

								  <!--[if (mso)|(IE)]><td align="center" width="675" style=" width:675px; padding-right: 0px; padding-left: 0px; padding-top:30px; padding-bottom:30px; border-top: 0px solid transparent; border-left: 0px solid transparent; border-bottom: 0px solid transparent; border-right: 0px solid transparent;" valign="top"><![endif]-->
								<div class="col num12" style="min-width: 320px;max-width: 675px;display: table-cell;vertical-align: top;">
									<div style="background-color: transparent; width: 100% !important;">
									<!--[if (!mso)&(!IE)]><!--><div style="border-top: 0px solid transparent; border-left: 0px solid transparent; border-bottom: 0px solid transparent; border-right: 0px solid transparent; padding-top:30px; padding-bottom:30px; padding-right: 0px; padding-left: 0px;"><!--<![endif]-->
									<div align="center" style="padding-right: 10px; padding-left: 10px; padding-bottom: 10px;" class="">
										<div style="line-height:10px;font-size:1px">&#160;</div>
										<div style="display: table; max-width:151px;">
										<!--[if (mso)|(IE)]><table width="131" cellpadding=0 cellspacing=0 border=0><tr><td style="border-collapse:collapse; padding-right: 10px; padding-left: 10px; padding-bottom: 10px;"  align="center"><table width="100%" cellpadding=0 cellspacing=0 border=0 style="border-collapse:collapse; mso-table-lspace: 0pt;mso-table-rspace: 0pt; width:131px;"><tr><td width="32" style="width:32px; padding-right: 5px;" valign="top"><![endif]-->
										<table align="left" border=0 cellspacing=0 cellpadding=0 width="32" height="32" style="border-collapse: collapse;table-layout: fixed;border-spacing: 0;mso-table-lspace: 0pt;mso-table-rspace: 0pt;vertical-align: top;Margin-right: 5px">
										  <tbody>
											  <tr style="vertical-align: top">
												  <td align="left" valign="middle" style="word-break: break-word;border-collapse: collapse !important;vertical-align: top">
													<a href="https://www.facebook.com/wearefxdigital" title="Facebook" target="_blank">
													  <img src="https://s3-eu-west-1.amazonaws.com/alexaecochallenge/facebook.png" alt="Facebook" title="Facebook" width="32" style="outline: none;text-decoration: none;-ms-interpolation-mode: bicubic;clear: both;display: block !important;border: none;height: auto;float: none;max-width: 32px !important">
													</a>
													<div style="line-height:5px;font-size:1px">&#160;</div>
												  </td>
											  </tr>
										  </tbody>
										</table>
										<!--[if (mso)|(IE)]></td><td width="32" style="width:32px; padding-right: 5px;" valign="top"><![endif]-->
										<table align="left" border=0 cellspacing=0 cellpadding=0 width="32" height="32" style="border-collapse: collapse;table-layout: fixed;border-spacing: 0;mso-table-lspace: 0pt;mso-table-rspace: 0pt;vertical-align: top;Margin-right: 5px">
											<tbody>
											  <tr style="vertical-align: top">
												  <td align="left" valign="middle" style="word-break: break-word;border-collapse: collapse !important;vertical-align: top">
													<a href="https://twitter.com/wearefxdigital" title="Twitter" target="_blank">
													  <img src="https://s3-eu-west-1.amazonaws.com/alexaecochallenge/twitter.png" alt="Twitter" title="Twitter" width="32" style="outline: none;text-decoration: none;-ms-interpolation-mode: bicubic;clear: both;display: block !important;border: none;height: auto;float: none;max-width: 32px !important">
													</a>
													<div style="line-height:5px;font-size:1px">&#160;</div>
												  </td>
											  </tr>
											</tbody>
										</table>
										<!--[if (mso)|(IE)]></td><td width="32" style="width:32px; padding-right: 0;" valign="top"><![endif]-->
										<table align="left" border=0 cellspacing=0 cellpadding=0 width="32" height="32" style="border-collapse: collapse;table-layout: fixed;border-spacing: 0;mso-table-lspace: 0pt;mso-table-rspace: 0pt;vertical-align: top;Margin-right: 0">
											<tbody>
												<tr style="vertical-align: top">
												  <td align="left" valign="middle" style="word-break: break-word;border-collapse: collapse !important;vertical-align: top">
													<a href="https://www.instagram.com/wearefxdigital/" title="Instagram" target="_blank">
													  <img src="https://s3-eu-west-1.amazonaws.com/alexaecochallenge/instagram@2x.png" alt="Instagram" title="Instagram" width="32" style="outline: none;text-decoration: none;-ms-interpolation-mode: bicubic;clear: both;display: block !important;border: none;height: auto;float: none;max-width: 32px !important">
													</a>
													<div style="line-height:5px;font-size:1px">&#160;</div>
												  </td>
												</tr>
											</tbody>
										</table>
										<!--[if (mso)|(IE)]></td></tr></table></td></tr></table><![endif]-->
									  </div>
									</div>
								  <!--[if (!mso)&(!IE)]><!--></div><!--<![endif]-->
								  </div>
								</div>
							  <!--[if (mso)|(IE)]></td></tr></table></td></tr></table><![endif]-->
							</div>
						  </div>
						</div>
						<!--[if (mso)|(IE)]></td></tr></table><![endif]-->
					</td>
				</tr>
			</tbody>
		</table>
		<!--[if (mso)|(IE)]></div><![endif]-->
	</body>
</html>

	"""
	return htmled
#<++++++++++++++++++++++++++++++++++++++++++++++++++++++>


#<----------RESPONSE BUILD FUNCS------------->
def buildCardResponse(output, card, repromptText, shouldEndSession,hasDisplay):
	if hasDisplay: 
		return {
			'outputSpeech': {
				'type': 'PlainText',
				'text': output
			},
			'card': card,
			'directives': [
				{
				'type': "Display.RenderTemplate",
				'template': {
					'type': 'BodyTemplate1',
					'token': 'string',
					'backButton': 'HIDDEN',
					"backgroundImage": {
								"contentDescription": "Cover Image",
								"sources": [
									{
										"url": "https://s3-eu-west-1.amazonaws.com/alexaecochallenge/bg.png",
										"widthPixels": 1024,
										"heightPixels": 600
									}
								]
							},
					'title': 'Eco Challenge',
					'textContent': {
						'primaryText': {
							'text': output,
							'type':'RichText'
							}
						}
					}
				},
				{
				'type': 'Hint',
				'hint': {
					'type': 'PlainText',
					'text': 'string'
				}
				}
			],
			'reprompt': {
				'outputSpeech': {
					'type': 'PlainText',
					'text': repromptText
				}
			},
			'shouldEndSession': shouldEndSession
		}
	else:
		return {
			'outputSpeech': {
				'type': 'PlainText',
				'text': output
			},
			'card': card,
			'reprompt': {
				'outputSpeech': {
					'type': 'PlainText',
					'text': repromptText
				}
			},
			'shouldEndSession': shouldEndSession
		}	

def buildSpeechletResponse(output, repromptText, shouldEndSession,hasDisplay):
	if hasDisplay:
		return {
		'outputSpeech': {
			'type': 'PlainText',
			'text': output
		},
		'reprompt': {
			'outputSpeech': {
				'type': 'PlainText',
				'text': repromptText
			}
		},
		'directives': [
			{
			'type': "Display.RenderTemplate",
			'template': {
				'type': 'BodyTemplate1',
				'token': 'string',
				'backButton': 'HIDDEN',
				"backgroundImage": {
							"contentDescription": "Cover Image",
							"sources": [
								{
									"url": "https://s3-eu-west-1.amazonaws.com/alexaecochallenge/bg.png",
									"widthPixels": 1024,
									"heightPixels": 600
								}
							]
						},
				
				'title': 'Eco Challenge',
				'textContent': {
					'primaryText': {
						'text': output,
						'type':'RichText'
						}
					}
				}
			},
			{
			'type': 'Hint',
			'hint': {
				'type': 'PlainText',
				'text': 'string'
				}
			}
		],
		'shouldEndSession': shouldEndSession
	}
	else:
		return {
		'outputSpeech': {
				'type': 'PlainText',
				'text': output
			},
			'reprompt': {
				'outputSpeech': {
					'type': 'PlainText',
					'text': repromptText
				}
			},
			
			'shouldEndSession': shouldEndSession
		}

def buildResponse(sessionAttributes, speechletResponse):
	return {
		'version': '1.0',
		'sessionAttributes': sessionAttributes,
		'response': speechletResponse
	}
def hasDisplay(event):
	if 'Display' in event['context']['System']['device']['supportedInterfaces']:
		return True
	else:
		return False

#<++++++++++++++++++++++++++++++++++++++++++>
