#!python3

#Imports
import os
import sys
import logging
import datetime
from importlib import import_module


#Python version
if sys.version_info[0] < 3:
	print("This program requires python version 3.5.2+. You have version " + str(sys.version_info) + "\nPlease download the latest version.")
	download = raw_input("Would you like to open the python  download page? Y/N:")
	if download.lower()=="y":
		import webbrowser
		webbrowser.open("http://www.python.org/downloads", new=0, autoraise=True)
	sys.exit()

#Flask
try: 
	from flask import Flask, request, Response
except ImportError as e:
	print("Flask library not found. It is necessary for this program to work.")
	install = input("Would you like to install it using 'pip install flask'? Y/N:")
	if install.lower() == "y":
		os.system("pip install flask")
		print("\nRestarting script...\n")
		os.system("python" + ("3 " if os.name=="posix" else " ") + __file__)
	else:
		sys.exit()



#Message string constants
TITLE = "HUB"
LOG = "LOG"

CMD = "Command"
CMD_RECV = "Command received "
CMD_RUN = "Running"
CMD_NOTFOUND = "not Found"
CMD_EXISTS = " duplicate command"
CMD_ADD = "Add"
CMD_LVL = "level"

MODULE = "Module"
MODULE_INIT = "Initialized"
MODULE_OK = "[ OK ]"
MODULE_FAIL = "[FAIL]"

BOOT_SUCCESS = "LOAD SUCCESS"
BOOT_FAILURE = "LOAD FAILURE"
BOOT_SELFCONTROL = "STARTED SELF CONTROL MODULE"

AUTH_FAIL = "Authorization invalid"

LOADING = "LOADING"
ERROR = "Error:"

#OS
OS_WIN = os.name == "nt"
OS_LINUX = os.name == "posix"

PYTHON_CMD = "python" + ("3 " if OS_LINUX else " ")

#Authorization
auth_hash = 5990 #startrekDS9

#Network
SERVER_PORT = "5000"

#Module commands
commands = {}
hub_commands = {}
command_restrict = {}
command_args = {}
command_desc = {}


### INCOMING REQUESTS ###
listener = Flask(__name__)
@listener.route('/', methods=["POST"])
def cmd_post():
	if request.method == "POST":
		
		#Get Variables
		command = str(request.form["command"]) if "command" in request.form else ""
		auth = str(request.form["auth"]) if "auth" in request.form else ""
		level = int(request.form["level"]) if "level" in request.form else 0
		ip = str(request.remote_addr)
		status_code = 200
		
		#Command received
		#log_msg(str(command), "from", ip, "auth '" + str(auth) + "' level", str(level), display=False)


		#Check authorization
		if authorized(auth):
			result = cmd_handle(command, auth, level, ip)
		else:
			result = AUTH_FAIL
			status_code = 401
		
		#Send response
		resp = Response(str(result), mimetype="text/xml")
		resp.headers["Access-Control-Allow-Origin"] = "*"
		return resp, status_code


### AUTHORIZATION ###
def authorized(key):
	return bhash(key) == auth_hash

def bhash(tohash):
	r = 0
	for i in range(0,len(tohash)):
		r += (i+1) * ord(tohash[i])
	return r;


### COMMAND HANDLING ###
def get_cmd_restriction(cmd):
	if cmd in command_restrict:
		return command_restrict[cmd]
	else:
		return 0

def cmd_handle(cmdargs, auth, level, ip):

	#Separate arguments from command
	sp = cmdargs.split(" ")
	command = sp[0].lower()
	args = sp[1:]

	#Command received
	if get_cmd_restriction(command) >= 0:
		log_msg(CMD_RECV, str(cmdargs), "from", ip, "auth '" + str(auth) + "' level", str(level), log=True)

	#Check if command exists in any module
	if command in commands:

		#Authorization level
		if level >= get_cmd_restriction(command):
			#Run command in module
			try:
				result = commands[command](*args)
			except Exception as e:
				result = (0, command + " encountered an error while running: " + repr(e))
		else:
			result = (0, "Authorization level too low to run this command.")
			
		#Print result
		if get_cmd_restriction(command) >= 0:
			status_msg(" "*len(MODULE_OK), result[1]) #log_msg ?

		return result[1]
	else: #Command not found
		if get_cmd_restriction(command) >= 0:
			log_msg(CMD, command, CMD_NOTFOUND)
		return CMD + " " + command + " " + CMD_NOTFOUND



### PRINTING STATUS ###
def msg(*messages, header=True):
	comp = " ".join([str(m) for m in messages])
	print (TITLE + ":" if header else "", comp)
def status_msg(*messages):
	comp = " ".join([str(m) for m in messages])
	print (comp)
def log_msg(*messages, display=True, log=True, showheader=True):
	m = " ".join([str(m) for m in messages])
	if display: msg(m, header=showheader)

	if log:
		lm = "["+str(datetime.datetime.now().strftime("%H:%M:%S"))+"] "   +   m
		try:
			with open("server_log.txt", "a+") as f:
				f.write(str(lm) + "\n")
		except Exception as e:
			print ("Error: Could not write to log.txt\n" + repr(e))


### MODULES ###
def load_modules():
	#Add reload hub command
	commands["reloadhub"] = reload_hub
	command_args["reloadhub"] = ""
	command_desc["reloadhub"] = "Restart HUB server process. Hardware will remain online. Could take up to 30s."

	#Add help command
	commands["help"] = cmd_help
	command_args["help"] = ""
	command_desc["help"] = "Shows this menu. Help <command> for details on a specific command."

	#Load modules and their commands
	path = os.path.dirname(os.path.realpath(__file__)) + "/modules"
	for file in os.listdir(path):
		if file[-3:]==".py" and not "__init__" in file and not "default_module" in file:
			file = file.replace(".py","")

			try:
				module = getattr(import_module("modules." + file), file)()

				#Get interface functions
				modcomms = module.get_commands()

				#Call module init
				log_msg(MODULE_OK, MODULE, file, MODULE_INIT, log=False)

				#Load module commands
				for c,f in modcomms.items():
					cmd = c.lower().split(" ")[0]
					if not cmd in commands: #New command	
						#Register commands in dictionaries
						commands[cmd] = f
						args = module.get_args(cmd)
						desc = module.get_desc(cmd)
						restriction = module.get_restriction(cmd)

						command_restrict[cmd] = restriction
						if args != "": command_args[cmd] = args
						if desc != "": command_desc[cmd] = desc

						log_msg(" "*len(MODULE_OK), CMD_ADD, CMD_LVL, str(restriction), CMD.lower(), cmd, log=False, showheader=False)
					else: #Command already exists
						log_msg(" "*len(MODULE_OK), ERROR, CMD_EXISTS, cmd, log=False)
			except Exception as e:
				log_msg("Error loading module " + file + ":" + repr(e))
				return 0

	#Successful load
	return 1

### BUILT IN COMMANDS ###
def reload_hub():
	if OS_LINUX:
		os.system("sleep 5s && sudo killall python3 &")
		os.system("sleep 10s && " + PYTHON_CMD + __file__ + " &")
		return (1,"Reloading HUB process")
	elif OS_WIN:
		os.system("timeout 5 && TASKKILL /IM " + __file__)
		os.system("timeout 10 && " + PYTHON_CMD + __file__)
		return (1,"Reloading HUB process")


def cmd_help(*args):
	if len(args) > 0:
		cmds = [a for a in args if a != ""]
	else:
		cmds = commands.keys()

	if len(cmds)>0:
		s = "Supported commands\n"
	
		for cmd in cmds:
			if cmd in commands:
				s += (" "*len(MODULE_OK) + cmd + "(" + CMD_LVL + " " + str(command_restrict[cmd] if cmd in command_restrict else 0) + "): ")
				if cmd in command_args:
					s += command_args[cmd]
				s +=  "\n"
				if cmd in command_desc: 
					s += (" "*len(MODULE_OK)*2 + command_desc[cmd] + "\n")
				s += "\n"
		
		if len([c for c in commands.keys() if c in cmds]) > 0:
			return (1,s)
		else:
			return (0,"Commands ("+",".join(cmds)+") not found")


	

### MAIN ###
def main():
	log_msg(LOADING, log=False)

	#Start client service for HUB control
	#listener.before_first_request(self_control)

	#Load modules
	mod = load_modules()
	if mod==1:
		log_msg(BOOT_SUCCESS, log=False)
	elif mod==0:
		log_msg(BOOT_FAILURE, log=False)
	
	#Set FLASK logging to verbose (only error)
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.ERROR)






	#from multiprocessing import Pool
	#pool = Pool(processes=1)
	#pool.apply_async(func=self_control, args=["name=hub", "mute", "registered"])
	#hub_client.main(["name=hub", "mute", "registered"])
	#msg("Started self control module")

	#if OS_LINUX:
		#os.system("sleep 10s && " + PYTHON_CMD + "hub_client.py name=hub mute registered" + " &")
	#elif OS_WIN:
		#os.system("timeout 10 >nul && hub_client.py") #Run in background?
	
	#Start FLASK listening on SERVER_PORT
	#listener.debug = True
	listener.run(host="0.0.0.0", port=SERVER_PORT)


if __name__ == "__main__":
	main()