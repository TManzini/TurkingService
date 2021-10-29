import uuid

def getTokenCode():
	return uuid.uuid4()

def validateHighlights(highlights, spanMin=1):
	if(len(highlights) >= spanMin):
		return True, None
	return False, "You must make at least " + str(spanMin) + " highlight selection"

def validateChecks(checks):
	if(sum(checks) == 1):
		return True, None
	return False, "You must select at exactly one label from the list of check boxes"

def getChaptListHTML(data_source_controller):
	res = ""
	for data_source in data_source_controller.getDataSources().values():
		res += "<h1>" + str(data_source.getName()) + "</h1>"
		for paragraph in data_source.getParagraphs().values():
			res += '<a href="/MCQ-Task/' + str(data_source.getSourceId()) +"/" + str(paragraph.getParagraphId()) + '">' + str(paragraph.getTitle().encode("ascii", "replace")) + "</a></br>"
	return res


#HTML UTILS BELOW

HL_START_TOKEN = "data-highlighted=\"true\">"
HL_END_TOKEN = "</span>"

def getParaHtml(dataSourceController, annotation):
	manual = dataSourceController.getDataSource(annotation.getDataSourceId())
	paragraph = manual.getParagraph(annotation.getParagraphId())
	res = paragraph.getContent()
	return res

def getDataSourceList(dataSourceController):
	res = "<ul>"
	dataSources = dataSourceController.getDataSources()
	for manId, manual in dataSources.items():
		res += "<li><a href=\"/admin-cms/dataSources/" + str(manId) + "/\">" + str(manual.getName()) + "</a><form method=\"POST\" action=\"/admin-cms/dataSources/remove/" + str(manId) + "/\"><input type=\"button\" value=\"Delete This Manual\" onclick=\"confSubmit(this.form);\"></form></li>"
	res += "</ul>"
	return res

def getParaList(dataSourceController, manualId):
	res = ""
	paragraphs = dataSourceController.getDataSource(manualId).getParagraphs()
	for paraId, para in paragraphs.items():
		res += "<p><b>ID: </b>" + str(para.getParagraphId()) + "</p>"
		res += "<p><b>Title: </b>" + str(para.getTitle()) + "</p>"
		res += "<p><b>Content: </b>" + str(para.getContent()) + "</p>"
		res += "<form method=\"POST\" action=\"/admin-cms/dataSources/" + str(manualId) + "/remove/" + str(paraId) + "/\"><input type=\"button\" value=\"Delete This Parapgraph\" onclick=\"confSubmit(this.form);\"></form>"
		res += "<hr>"
	return res

def getHighlightedSpans(recievedHtml):
	res = []
	offset = 0
	workingString = str(recievedHtml)
	startIndex = safeIndex(workingString, HL_START_TOKEN)
	endIndex = safeIndex(workingString, HL_END_TOKEN)
	while(startIndex != -1 and endIndex != -1 and len(workingString) > 0):
		highlighted_text = recievedHtml[offset + startIndex + len(HL_START_TOKEN):offset + endIndex]
		res.append({"text":highlighted_text})
		offset += endIndex+len(HL_END_TOKEN)
		startIndex = safeIndex(workingString[offset:], HL_START_TOKEN)
		endIndex = safeIndex(workingString[offset:], HL_END_TOKEN)
	return res

def safeIndex(source, target):
	try:
		return source.index(target)
	except:
		return -1