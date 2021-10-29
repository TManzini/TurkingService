import threading

class UserController:
	def __init__(self, logPath):
		self.__logPath = logPath
		self.__fileLock = threading.Lock()

	def logCompletedTask(self, userID, surveyCode):
		self.__fileLock.acquire()
		f = open(self.__logPath, "a")
		f.write("ID:" + str(userID) + "\nCode:" + str(surveyCode) + "\n\n")
		f.close()
		self.__fileLock.release()