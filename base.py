#!python3

#Imports
import os
import datetime
from importlib import import_module

from flask import Flask, request, Response
import logging


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

AUTH_FAIL = "Authorization invalid"

LOADING = "LOADING"
ERROR = "Error:"

#Network
HOST = '192.168.1.72'

#Authorization
auth_hash = 5990 #startrekDS9


#Module commands
commands = {}
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
		log_msg(str(command), "from", ip, "auth '" + str(auth) + "' level", str(level))


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


### EXCEPTIONS ###
def GetStackTrace():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    return ('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))

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
		msg(CMD_RECV + cmdargs)

	#Check if command exists in any module
	if command in commands:

		#Authorization level
		if level >= get_cmd_restriction(command):
			#Run command in module
			try:
				result = commands[command](*args)
			except Exception as e:
				result = (0, command + " encountered an error while running: " + GetStackTrace())
		else:
			result = (0, "Authorization level too low to run this command.")
			
		#Print result
		if get_cmd_restriction(command) >= 0:
			status_msg(" "*len(MODULE_OK), result[1])

		return result[1]
	else: #Command not found
		if get_cmd_restriction(command) >= 0:
			msg(CMD, command, CMD_NOTFOUND)
		return CMD + " " + command + " " + CMD_NOTFOUND



### PRINTING STATUS ###
def msg(*messages):
	comp = " ".join([str(m) for m in messages])
	print (TITLE + ":", comp)
def status_msg(*messages):
	comp = " ".join([str(m) for m in messages])
	print (comp)
def log_msg(*messages):
	msg = "["+str(datetime.datetime.now().strftime("%H:%M:%S"))+"]"   +   " ".join([str(m) for m in messages])
	try:
		f = open("log.txt", "w")
		f.write(str(msg))
		f.close()
	except Exception as e:
		print ("Error: Could not write to log.txt\n" + repr(e))


### MODULES ###
def load_modules():
	#Add reload command
	commands["reloadmodules"] = reload_modules
	command_args["reloadmodules"] = ""
	command_desc["reloadmodules"] = "Discard current modules and commands, re-load from /modules/"
	#Add help command
	commands["help"] = cmd_help
	command_args["help"] = ""
	command_desc["help"] = "Shows this menu. Help <command> for details on a specific command."

	path = os.path.dirname(os.path.realpath(__file__)) + "/modules"

	for file in os.listdir(path):
		if file[-3:]==".py" and not "__init__" in file and not "default_module" in file:
			file = file.replace(".py","")

			#try:
			module = getattr(import_module("modules." + file), file)()

			#Get interface functions
			modcomms = module.get_commands()


			#Call module init
			#if init_result[0]==1: #OK
			status_msg(MODULE_OK, MODULE, file, MODULE_INIT)
			#elif init_result[0]==0: #FAIL
				#status_msg(MODULE_FAIL, MODULE, file, MODULE_INIT)
				#status_msg(" "*len(MODULE_OK), ERROR, init_result[1])
			#elif init_result[0]==-1: #IGNORE
				#continue

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

					status_msg(" "*len(MODULE_OK), CMD_ADD, CMD_LVL, str(restriction), CMD.lower(), cmd)
				else: #Command already exists
					status_msg(" "*len(MODULE_OK), ERROR, CMD_EXISTS, cmd)
			#except TypeError:
				#print ("Tried to initialize abstract class " + file)
				#continue
			#except Exception:
				#return 0

	#Successful load
	return 1

def reload_modules():
	commands.clear()
	command_args.clear()
	command_desc.clear()

	mod = load_modules()
	if mod==1:
		msg(BOOT_SUCCESS)
		return (1, "Modules reloaded")
	elif mod==0:
		msg(BOOT_FAILURE)
		return (0, "Error loading modules")

	
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
	msg(LOADING)

	#Load modules
	reload_modules()
	
	#Set FLASK logging to verbose (only error)
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.ERROR)

	#Start FLASK listening 
	#listener.debug = True
	listener.run(host='0.0.0.0')



	#while 1:
		#cmd = client.recv(MAX_LENGTH)

		#Client terminated connection
		#if cmd == "": return 

    #Open socket
	#serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #Don't make me wait when I force close a socket to open another one
	#serversocket.bind((HOST, PORT))
	#serversocket.listen(5) #Five requests possible

	#Accept connections from outside
	#while True:
		#(client, address) = serversocket.accept()

		#ct = Thread(target=cmd_handle, args=(client,))
		#ct.run()


if __name__ == "__main__":
	main()