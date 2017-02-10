#!python3

#Imports
import os
import sys
import time
import logging


#Hub LIB
from hub_lib import *



#Authorization
auth_key = "picard" #Level 1 auth key

#Settings
MUTE = False


#Client commands
commands = {}


### RECEIVE REQUESTS ###
listener = Flask(__name__)
@listener.route('/', methods=["GET", "POST"])
def cmd_recv():

	#Get Variables
	#command = str(request.form["command"])
	command = str(request.args.get("command"))
	ip = str(request.remote_addr)

	#Command received
	if not MUTE: log_msg(CMD_RECV, "'" + str(command) + "'", "from", ip, log=CLIENT_LOG, header=get_name())#, "auth '" + str(auth) + "' level", str(level))

	if ip == HUB_IP:
		result = cmd_handle(command)

		#Send response
		resp = Response(str(result[1]), mimetype="text/xml")
		resp.headers["Access-Control-Allow-Origin"] = "*"
		return resp


### COMMAND HANDLING ###
def cmd_handle(cmdargs):

	#Split command
	sp = cmdargs.split(" ")
	command = sp[0].lower()
	args = sp[1:]

	#Check if command exists in any module
	if command in commands:
		#Run command in module
		try:
			result = commands[command](*args)
		except Exception as e:
			result = (0, "Command encountered an error while running:" + repr(e))

		#Print result
		if not MUTE: log_msg(result[1])
	else: #Command not found
		result = (0, CMD + " " + command + " " + CMD_NOTFOUND)
		if not MUTE: log_msg(CMD, command, CMD_NOTFOUND, log=CLIENT_LOG, header=get_name())
	
	return result



### CLIENT COMMANDS ###
def shutdown(*args):
	if OS_LINUX:
		exec_cmd(10, func=os.system, args=["sudo shutdown"])
	elif OS_WIN:
		exec_cmd(0, func=os.system, args=["shutdown /t 10 /s"])
	return (1,"Shutting down " + get_name())
commands["shutdown"] = shutdown

def restart(*args):
	if OS_LINUX:
		exec_cmd(10, func=os.system, args=["sudo reboot"])
	elif OS_WIN:
		exec_cmd(0, func=os.system, args=["shutdown /t 10 /r"])
	return (1,"Restarting " + get_name())
commands["restart"] = restart

def hibernate(*args):
	if OS_LINUX:
		return (0,"Not supported")
	elif OS_WIN:
		exec_cmd(10, func=os.system, args=["shutdown /h"])
	return (1,"Hibernating " + get_name())
commands["hibernate"] = hibernate

def logoff(*args):
	if OS_LINUX:
		return (0,"Not supported")
	elif OS_WIN:
		exec_cmd(10, func=os.system, args=["shutdown /l"])
	return (1,"Logging off " + get_name())
commands["logoff"] = logoff

def unregister(*args):
	return (1,"Unregistered from HUB")
commands["unregister"] = unregister

def device_status(*args):
	return (1,"Online")
commands["status"] = device_status



### HUB REGISTRATION ###
def do_register(Register_timeout, INITIAL_REGISTER_ATTEMPT):
	reg_res = (INITIAL_REGISTER_ATTEMPT, False)
	while True:
		reg_res = register(reg_res[0], reg_res[1])
		time.sleep(Register_timeout)

def register(INITIAL_REGISTER_ATTEMPT=False, RETRYING_CONNECTION=False):
	register_cmd = "register " + get_name() + " " + get_ip() + " " + get_mac()
	is_registered_cmd = "isregistered " + get_name()


	#Have ever registered
	if not INITIAL_REGISTER_ATTEMPT:
		if not MUTE: log_msg(CONTACTING_HUB, header=get_name())
		#Try register
		result = send_cmd(register_cmd, HUB_IP, PORT, auth_key)
		if not MUTE: log_msg(" "*5, result[1])

		#Successful register
		if result[0] != 0:
			if not MUTE: log_msg(READY, header=get_name())
			INITIAL_REGISTER_ATTEMPT = True
	else: #Have been registered before
		is_registered = send_cmd(is_registered_cmd, HUB_IP, PORT, auth_key)

		#Could not contact HUB
		if is_registered[0] == 0 and not RETRYING_CONNECTION:
			if not MUTE: log_msg(CONNECTION_LOST, header=get_name(), log=CLIENT_LOG)
			RETRYING_CONNECTION = True
		elif is_registered[0] != 0 and is_registered[1] == "no": #Contacted hub, we're not registered
			if not MUTE and RETRYING_CONNECTION: log_msg(CONNECTION_RESTORED, header=get_name(), log=CLIENT_LOG)

			#Try register
			result = send_cmd(register_cmd, HUB_IP, PORT, auth_key)

			#Successful re-register
			if result[0] != 0:
				RETRYING_CONNECTION = False
	
	return (INITIAL_REGISTER_ATTEMPT, RETRYING_CONNECTION)


### MAIN ###
def main(*args):
	Register_timeout = 10 #Default 30?
	INITIAL_REGISTER_ATTEMPT = False
	LOCAL_MODE = False

	global MUTE

	windows_startup_folder = "AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"


	#Arguments
	if len(args)==0:
		args = sys.argv

	if len(args) > 0:
		for arg in args:
			if "name=" in arg:
				set_name(arg.replace("name=",""))
			if "ip=" in arg:
				set_ip(arg.replace("ip=",""))
			if "mac=" in arg:
				set_mac(arg.replace("mac=",""))
			if "mute" in arg:
				MUTE = True
			if "registered" in arg:
				INITIAL_REGISTER_ATTEMPT = True
			if "local_mode" in arg:
				LOCAL_MODE = True
				INITIAL_REGISTER_ATTEMPT = True
			if "startup" in arg:
				#Run hub_client on startup
				path = os.path.abspath(__file__)
				if OS_LINUX:
					log_msg ("Create a file called 'hub_launcher.sh'\nIn it, include 'sudo " + path + "' in the file.\nEdit /etc/rc.local and add 'sleep 6s' and 'sudo sh <path to hub_launcher.sh> &' BEFORE 'exit 0'", header=get_name())
				elif OS_WIN:
					#sch_task_startup("hub_client", "\"" + path + "\"")

					#user_folder = os.environ['USERPROFILE']

					#os.system("copy \"" + __file__ + "\" " + "\"" + user_folder + "\\" + windows_startup_folder + "\"")

					startup_dir = user_folder + "\\" + windows_startup_folder
					batch_file = "hub_client_shortcut.bat"
					contents = PYTHON_CMD + " \"" + path + "\""

					exists = any([batch_file in f for f in os.listdir(startup_dir)])
					
					if not exists:
						shortcut = open(startup_dir + "\\" + batch_file, 'w')
						shortcut.write(contents)
						shortcut.close()

						if not MUTE: log_msg("Client program shortcut copied to startup directory: " + user_folder + "\\" + windows_startup_folder, header=get_name())
					else:
						if not MUTE: log_msg("Client program is already in the startup directory.", header=get_name())
	
	#Startup header
	if not MUTE:
		#Startup tip
		if not "startup" in args:
			log_msg("TIP: Execute '"+PYTHON_CMD+" hub_client.py startup' with admin priviledges to run this on startup.")
		
		print_header("HUB CLIENT")

	
	#Remote mode (listener and registration)
	if not LOCAL_MODE:
		#Register client with HUB (On another thread, so that connection scheduler does not stop client from receiving data)
		from multiprocessing import Pool
		pool = Pool(processes=1)
		pool.apply_async(func=do_register, args=(Register_timeout, INITIAL_REGISTER_ATTEMPT))


		#Set FLASK logging to verbose (only error)
		log = logging.getLogger('werkzeug')
		log.setLevel(logging.ERROR)

		#Start FLASK listening on CLIENT_PORT
		#listener.debug = True
		listener.run(host="0.0.0.0", port=PORT)


#Silly windows, __main__ is for kids!
if __name__ == "__main__":
	main()