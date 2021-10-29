import json

class ConfigController:
	def __init__(self, path_to_config):
		self.__path = path_to_config
		try:
			self.__config_data = json.loads(open(self.__path, "r").read())
		except FileNotFoundError as e:
			print("Error passed config file not found.")
			raise e

	def getOutputPath(self):
		return self.__config_data["output_path"]

	def getInputPath(self):
		return self.__config_data["input_path"]

	def getAdminUsersPath(self):
		return self.__config_data["admin_users_path"]

	def getParticipatingUsersOutputPath(self):
		return self.__config_data["participating_users_output_path"]

	def getTaskTemplate(self):
		return self.__config_data["task_template_path"]

	def getSamplesPerTask(self):
		return self.__config_data["samples_per_task"]

	def getWelcomePageInstructions(self):
		return self.__config_data["welcome_page_instructions"]
	
	def getTaskPageInstructions(self):
		return self.__config_data["task_page_instructions"]

