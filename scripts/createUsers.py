from passlib.apps import custom_app_context as pwd_context
import json

userdata = {}
cont = "yes"
while(not "n" in cont):
	username = input("Please enter a username\n>")
	password = input("Please enter a password\n>")
	password_hash = pwd_context.hash(password)

	userdata[username] = {"username":username, "password":password_hash}

	cont = input("Would you like to continue?\n(y)es/(n)o >")

with open('users.json', 'w') as outfile:
	print("Users written to file \"users.json\"")
	json.dump(userdata, outfile)