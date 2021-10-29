from functools import wraps
from flask import Flask, render_template, Response, redirect, url_for, request, flash, session, abort, Markup, jsonify, send_from_directory, abort
from passlib.apps import custom_app_context as pwd_context
from datetime import datetime

from Constants import *
from ConfigController import ConfigController
from DataSourceController import DataSourceController, AnnotationExample
from UserController import UserController
from util import getTokenCode, validateHighlights, validateChecks, getChaptListHTML, getParaHtml, getHighlightedSpans, getDataSourceList, getParaList

import json
import os
import threading
import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('config_file', type=str, help='The path to the config file that defines the task.')
args = parser.parse_args()


app = Flask(__name__)
app.secret_key = os.urandom(24)

cc = ConfigController(args.config_file)
mc = DataSourceController(cc.getInputPath(), cc.getOutputPath())
uc = UserController(cc.getParticipatingUsersOutputPath())

ADMIN_USERS = json.loads(open(cc.getAdminUsersPath(), "r").read())

def userdata_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if(not (USER_ID_ENTERED in session.keys() and session[USER_ID_ENTERED])):
            return abort(HTTP_UNAUTHORIZED_403)
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if(not (LOGGED_IN in session.keys() and session[LOGGED_IN])):
            return abort(HTTP_UNAUTHORIZED_403)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET'])
def homepage():
	session[USER_ID_ENTERED] = False
	session[LOGGED_IN] = False
	return render_template('home.html', message="", instructions=cc.getWelcomePageInstructions())

@app.route('/', methods=['POST'])
def welcomeTask():
	if(USER_ID in request.form):
		session.clear()
		session[USER_ID] = request.form[USER_ID]
		session[USER_ID_ENTERED] = True
		session[LOGGED_IN] = False
		session[COMPLETED_ANNOTATIONS] = 0
		return redirect(url_for('startTask'))
	else:
		return render_template('home.html', message="INVALID POST REQUEST", instructions=WELCOME_INSTRUCTIONS.format(N=str(MAX_NUMBER_ANNOTATIONS)))

@app.route('/Task', methods=["GET"])
@userdata_required
def startTask():
	nextAnnotation = mc.getNextAnnotationExample()
	return displayTask(nextAnnotation.getDataSourceId(), nextAnnotation.getParagraphId())

@userdata_required
def displayTask(dataSource, paragraph):
	nextAnnotation = AnnotationExample((dataSource, paragraph))
	toDisplay = getParaHtml(mc, nextAnnotation)
	session[CURRENT_ANNOTATION_EXAMPLE] = nextAnnotation.getIdPair()
	return render_template(cc.getTaskTemplate(), sourceParagraph=toDisplay, instructions=cc.getTaskPageInstructions())

@app.route('/Task', methods=["POST"])
@userdata_required
def stepTask():
	request_data = request.form.to_dict()
	
	print("Here is the data that was returned to you by a user who completed a stage of the task.")
	print(request_data)

	print("Place the logic associated with validating a task submission here. ")

	#Get the spans that the user highlighted for example, or check against other things that they gave you in the dictionary
	#Maybe they said it wasnt human readable
	highlighted = getHighlightedSpans(request_data["sourceParaHidden"])

	data_id = session[CURRENT_ANNOTATION_EXAMPLE][0]
	para_id = session[CURRENT_ANNOTATION_EXAMPLE][1]

	#The annotation that will be logged from this task completion
	annotation = {"user_id":session[USER_ID], "data_id":data_id, "para_id":para_id, "highlighted":highlighted}

	#Check what the user gave you to make sure its valid
	highlightsValid, highlightsErrors = validateHighlights(highlighted, 1)

	valid = False
	if(highlightsValid):
		valid = True
		mc.getDataSource(data_id).getParagraph(para_id).addAnnotation(annotation)
		mc.writeAnnotations()

	#If it is valid, great!
	if(valid):
		#Step through to the next sample in list
		session[COMPLETED_ANNOTATIONS] += 1
		if(session[COMPLETED_ANNOTATIONS] < cc.getSamplesPerTask()):
			nextAnnotation = mc.getNextAnnotationExample()
			return displayTask(nextAnnotation.getDataSourceId(), nextAnnotation.getParagraphId())
		#Or if the user is done, give them their token so they can redeem it with you!
		else:
			token_code = getTokenCode()
			uc.logCompletedTask(session[USER_ID], token_code)
			session.clear()
			return render_template('taskComplete.html', completion_token=token_code)
	
	#If the user gave you something invalid
	else:
		curExample = AnnotationExample(session[CURRENT_ANNOTATION_EXAMPLE])
		toDisplay = getParaHtml(mc, curExample)
		errorMessage = "An error was made with your submission. Please address the following errors and resubmit your question." + "</br>Highlighting Errors: " + str(highlightsErrors)
		prefilledAnswers = []
		prefilledAnswersChecked = []
		return render_template('taskpage.html', sourceParagraph=toDisplay, instructions=cc.getTaskPageInstructions(), message=errorMessage)

@app.route('/admin-cms', methods=["GET"])
def adminEnter():
	return render_template('login.html')

@app.route('/admin-cms', methods=['POST'])
def loginHandler():
	session[LOGGED_IN] = False
	errorMsg = "Error: No login data entered"
	if('username' in request.form and 'password' in request.form):
		try:
			username = request.form['username']
			password = request.form['password']
			try:
				if(pwd_context.verify(password, ADMIN_USERS[username]['password'])):
					session[LOGGED_IN] = True
				else:
					errorMsg = "Error: Invalid password for that username"
			except KeyError as e:
				errorMsg = "Error: Invalid username and password"
		except Exception as e:
			errorMsg = "General Error:" + str(e)
		if(session[LOGGED_IN]):
			return redirect(url_for('dataSourceList'))
	return render_template('login.html', errorMsg=str(errorMsg))

@app.route('/admin-cms/dataSources', methods=['GET'])
@login_required
def dataSourceList():
	manList = getDataSourceList(mc)
	return render_template('listDataSources.html', manList=str(manList))

@app.route('/admin-cms/dataSources/<int:dataSourceId>/', methods=['GET'])
@login_required
def dataSourceParaList(dataSourceId):
	paraList = getParaList(mc, dataSourceId)
	return render_template('listPara.html', paraList=str(paraList))

@app.route('/admin-cms/dataSources/<int:dataSourceId>/', methods=['POST'])
@login_required
def addDataSourcePara(dataSourceId):
	if('paraTitle' in request.form and 'paraContent' in request.form):
		mc.getDataSource(dataSourceId).addParagraph(request.form["paraTitle"], request.form['paraContent'])
	paraList = getParaList(mc, dataSourceId)
	return render_template('listPara.html', paraList=str(paraList))


@app.route('/admin-cms/dataSources/<int:dataSourceId>/remove/<int:paraId>/', methods=['POST'])
@login_required
def removeDataSourcePara(dataSourceId, paraId):
	mc.getDataSource(dataSourceId).removeParagraph(paraId)
	paraList = getParaList(mc, dataSourceId)
	return render_template('listPara.html', paraList=str(paraList))

@app.route('/admin-cms/dataSources', methods=['POST'])
@login_required
def addDataSource():
	if('manName' in request.form):
		mc.addDataSource(request.form["manName"])
	return redirect(url_for('dataSourceList'))

@app.route('/admin-cms/dataSources/remove/<int:dataSourceId>/', methods=['POST'])
@login_required
def removeDataSource(dataSourceId):
	mc.removeDataSource(dataSourceId)
	return redirect(url_for('dataSourceList'))

@app.route('/admin-cms/flushToDisk', methods=['POST'])
@login_required
def flushToDisk():
	mc.saveDataToDisk()
	return redirect(url_for('dataSourceList'))

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=FLASK_PORT, threaded=True)