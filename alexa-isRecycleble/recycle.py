#recycle.py
import logging 
import os
from flask import Flask, request, jsonify
from flask_ask import Ask, statement, question, session, delegate

app = Flask(__name__)
ask = Ask(app,"/")



logging.getLogger("flask_ask").setLevel(logging.DEBUG)

@ask.launch
def start():
	welcome_msg = "Welcome, you can ask me your material."
	return question(welcome_msg)


my_path = os.path.abspath(os.path.dirname(__file__))
path = os.path.join(my_path, "recyclable_list.txt")
f=open(path, "r")

@ask.intent("isRecyclableIntent")
def recyclable(material):
	f.seek(0)
	f1 = f.readlines()
	a=0
	for x in f1:
		print (x)
		if material in x:
			a = 1
	if a==1:
		retMsg = "Yes please, you can throw {} to the recycle bin".format(material)
	else:
		retMsg = "No please, throw {} to the garbage bin".format(material)
	#print ('MESSAGE: ' +get_dialog_state())
	return	question(retMsg)

@ask.intent("isThisInThis")
def inThis(city,material):
	if((city == None )& (material == None)):#NO SLOT
		dialog ={
				"version": "1.0",
				"sessionAttributes": {},
				"response": {
					"outputSpeech": {
					"type": "PlainText",
					"text": "which city you will recycle in"
				},
				"shouldEndSession": 'false',
				"directives": [
					{
					"type": "Dialog.ElicitSlot",
						"slotToElicit": "city",
						"updatedIntent": {
							"name": "isThisInThis",
							"confirmationStatus": "NONE",
							"slots": {
								"city": {
								"name": "city",
								"confirmationStatus": "NONE"
								},
								"material":{
								"name": "material",
								"confirmationStatus": "NONE"
								}
							}
						}
					}]
				}
			}

		return jsonify(dialog)
	elif((city != None) & (material == None)):#ONLY CITY
		dialog ={
				"version": "1.0",
				"sessionAttributes": {},
				"response": {
					"outputSpeech": {
					"type": "PlainText",
					"text": "which material you would like to recycle"
				},
				"shouldEndSession": 'false',
				"directives": [
					{
					"type": "Dialog.ElicitSlot",
						"slotToElicit": "material",
						"updatedIntent": {
							"name": "isThisInThis",
							"confirmationStatus": "NONE",
							"slots": {
								"city": {
								"name": "city",
								"value": city,
								"confirmationStatus": "NONE"
								},
								"material":{
								"name": "material",
								"confirmationStatus": "NONE"
								}
							}
						}
					}]
				}
			}

		return jsonify(dialog)
	elif((city == None) & (material != None)):#ONLY MATERIAL
		dialog ={
				"version": "1.0",
				"sessionAttributes": {},
				"response": {
					"outputSpeech": {
					"type": "PlainText",
					"text": "which city you will recycle in"
				},
				"shouldEndSession": 'false',
				"directives": [
					{
					"type": "Dialog.ElicitSlot",
						"slotToElicit": "city",
						"updatedIntent": {
							"name": "isThisInThis",
							"confirmationStatus": "NONE",
							"slots": {
								"city": {
								"name": "city",
								"confirmationStatus": "NONE"
								},
								"material":{
								"name": "material",
								"value": material,
								"confirmationStatus": "NONE"
								}
							}
						}
					}]
				}
			}

		return jsonify(dialog)
	else:#CITY AND MATERIAL
		if (city =="London"):
			f.seek(0)
			f1 = f.readlines()
			a=0
			for x in f1:
				print (x)
				if material in x:
					a = 1
			if a==1:
				retMsg = "Yes please, you can throw {} to the recycle bin".format(material)
				return	statement(retMsg) \
				.standard_card(title='YES',text='please remember to throw recycle bin',large_image_url='https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Recycle001.svg/2000px-Recycle001.svg.png')
			else:
				retMsg = "No please, throw {} to the garbage bin".format(material)
				return	statement(retMsg) \
				.standard_card(title='NO',text='please remember to throw garbage bin',large_image_url='https://thumbs.dreamstime.com/b/no-recycling-allowed-sign-no-recycling-sign-113167663.jpg')
			
			
	



if __name__ == '__main__':
	if 'ASK_VERIFY_REQUESTS' in os.environ:
		verify = str(os.environ.get('ASK_VERIFY_REQUESTS', '')).lower()
		if verify == 'false':
			app.config['ASK_VERIFY_REQUESTS'] = False
	app.run(debug=True)
