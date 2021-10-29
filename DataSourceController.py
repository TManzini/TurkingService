from shutil import copyfile

import json
import sys
import threading
import random
import datetime
import pickle

class DataSourceController:
	def __init__(self, dataJsonPath, annotationsPath):
		try:
			json_data = json.loads(open(dataJsonPath, "r").read())
		except FileNotFoundError:
			print("Error paragraph data not found, starting with no paragraphs.")
			json_data = []
		try:
			annotation_data = json.loads(open(annotationsPath, "r").read())
		except FileNotFoundError:
			print("Error annotation data not found, starting with no annotation.")
			annotation_data = []

		self.__dataSources = {}
		self.__dataLock = threading.Lock()
		self.__annotationLock = threading.Lock()
		self.__maxId = 0

		self.__dataJsonPath = dataJsonPath
		self.__annotationsPath = annotationsPath

		self.__dataFileLock = threading.Lock()

		for dataInfo in json_data:
			dataSourceId = dataInfo["data_id"]
			if(self.__maxId < dataSourceId):
				self.__maxId = dataSourceId
			self.__dataSources[dataSourceId] = DataSource(dataSourceId, dataInfo["data_name"])
			for paraInfo in dataInfo["data_paragraphs"]:
				self.__dataSources[dataSourceId].addParagraph(paraInfo["title"], paraInfo["contents"])

		for annotation_block in annotation_data:
			data_id = annotation_block["data_id"]
			para_id = annotation_block["para_id"]
			annotations = annotation_block["annotations"]
			for annotation in annotations:
				self.__dataSources[data_id].getParagraphs()[para_id].addAnnotation(annotation)

	def getNextAnnotationExample(self):
		candidates = []
		mins = float("inf")
		for dataSourceId, _ in self.__dataSources.items():
			for paraId, para in self.__dataSources[dataSourceId].getParagraphs().items():
				value = len(para.getAnnotations())
				if(value < mins):
					mins = value
					candidates = []
				if(value == mins):
					candidates.append(AnnotationExample((dataSourceId, paraId)))

		return random.choice(candidates)

	def saveDataToDisk(self):
		data = []
		for dataSourceId, dataSource in self.__dataSources.items():
			data.append({"data_name":dataSource.getName(), "data_id":dataSourceId, "data_paragraphs":[]})
			for paraId, para in dataSource.getParagraphs().items():
				data[-1]["data_paragraphs"].append({"id":paraId, "title":para.getTitle(), "contents":para.getContent()})
				
		toWrite = json.dumps(data, indent=4, sort_keys=True)
		self.__dataFileLock.acquire()
		copyfile(self.__dataJsonPath, self.__dataJsonPath + "_" + str(datetime.datetime.now()).replace("-", "").replace(" ", "").replace(":","") + ".json")
		f = open(self.__dataJsonPath, "w")
		f.write(toWrite)
		f.close()
		self.__dataFileLock.release()

	def getDataSource(self, dataSourceId):
		return self.__dataSources[dataSourceId]

	def getDataSources(self):
		return self.__dataSources

	def addDataSource(self, name):
		self.__dataLock.acquire()
		self.__maxId += 1
		self.__dataSources[self.__maxId] = DataSource(self.__maxId, name)
		self.__dataLock.release()

	def removeDataSource(self, sourceId):
		self.__dataLock.acquire()
		del self.__dataSources[sourceId]
		self.__dataLock.release()

	def writeAnnotations(self):
		annotations = []
		for data_id, data_source in self.__dataSources.items():
			for para_id, para in data_source.getParagraphs().items():
				if(len(para.getAnnotations()) > 0):
					annotations.append({})
					annotations[-1]["data_id"] = data_id
					annotations[-1]["para_id"] = para_id
					annotations[-1]["para_title"] = para.getTitle()
					annotations[-1]["para_content"] = para.getContent()
					annotations[-1]["annotations"] = para.getAnnotations()

		toWrite = json.dumps(annotations, indent=4, sort_keys=True)
		self.__annotationLock.acquire()
		f = open(self.__annotationsPath, "w")
		f.write(toWrite)
		f.close()
		self.__annotationLock.release()



class DataSource:
	def __init__(self, sourceId, name):
		self.__sourceId = sourceId
		self.__name = name
		self.__paragraphs = {}
		self.__maxId = 0
		self.__paraLock = threading.Lock()

	def getSourceId(self):
		return self.__sourceId
	def getName(self):
		return self.__name
	def getParagraphs(self):
		return self.__paragraphs
	def getParagraph(self, paraId):
		return self.__paragraphs[paraId]

	def addParagraph(self, title, content):
		self.__paraLock.acquire()
		self.__paragraphs[self.__maxId] = DataSourceParagraph(self.__maxId, title, content)
		self.__maxId += 1
		self.__paraLock.release()

	def removeParagraph(self, paragraphId):
		self.__paraLock.acquire()
		del self.__paragraphs[paragraphId]
		self.__paraLock.release()

class DataSourceParagraph:
	def __init__(self, paraId, title, content):
		self.__paraId = paraId
		self.__title = title
		self.__content = content
		self.__annotations = []

	def getParagraphId(self):
		return self.__paraId
	def getTitle(self):
		return self.__title
	def getContent(self):
		return self.__content
	def addAnnotation(self, annotation):
		self.__annotations.append(annotation)
	def getAnnotations(self):
		return self.__annotations

class AnnotationExample:
	def __init__(self, dataParaIdPair):
		self.__sourceId = dataParaIdPair[0]
		self.__paraId = dataParaIdPair[1]

	def getDataSourceId(self):
		return self.__sourceId
	def getParagraphId(self):
		return self.__paraId
	def getIdPair(self):
		return (self.__sourceId, self.__paraId)