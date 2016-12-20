#!python3

#Imports
import os
import sys
import datetime
import time
import logging

#Finding IP/Name/MAC
import socket
from uuid import getnode

#Contacting HUB
import sched

#Python version
if sys.version_info[0] < 3:
	print("This program requires python version 3.5.2+. You have version " + str(sys.version_info) + "\nPlease download the latest version.")
	download = raw_input("Would you like to open the python  download page? Y/N:")
	if download.lower()=="y":
		import webbrowser
		webbrowser.open("http://www.python.org/downloads", new=0, autoraise=True)
	sys.exit()

#Requests
try: 
	import requests
except ImportError as e:
	print("Requests library not found. It is necessary for this program to work.")
	install = input("Would you like to install it using 'pip install requests'? Y/N:")
	if install.lower() == "y":
		os.system("pip install requests")
		print("\nRestarting script...\n")
		os.system("python" + ("3 " if os.name=="posix" else " ") + __file__)
	else:
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
TITLE = "CLIENT"
LOG = "LOG"

AUTH_FAIL = "Authorization invalid"

CMD = "Command"
CMD_NOTFOUND = "not Found"

RETRYING = "Retrying connection in"
CONNECTION_LOST = "Connection to HUB lost."
CONNECTION_RESTORED = "Connection restored."
CONTACTING_HUB = "Contacting HUB to register"
READY = "Connected to HUB. Awaiting commands"
ERROR = "Error:"

#Network
HUB_IP = "192.168.1.72"
CLIENT_PORT = "5001"
SERVER_PORT = "5000"

#Authorization

#Settings
INITIAL_REGISTER_ATTEMPT = False
RETRYING_CONNECTION = False
MUTE = False
Register_timeout = 10 #Default 30?
LOCAL_MODE = False


## NETWORK ##
def get_ip_address():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	return s.getsockname()[0]
def get_mac_address():
	return "".join(c + ":" if i % 2 else c for i, c in enumerate(hex( getnode() )[2:].zfill(12)))[:-1]


#Get device IP, MAC and name
NAME = socket.gethostname()
IP = get_ip_address()
MAC = get_mac_address()
OS_WIN = os.name == "nt"
OS_LINUX = os.name == "posix"


#Client commands
commands = {}


### RECEIVE REQUESTS ###
listener = Flask(__name__)
@listener.route('/', methods=["POST"])
def cmd_post():

	#Get Variables
	command = str(request.form["command"])
	ip = str(request.remote_addr)

	#Command received
	log_msg(str(command), "from", ip)#, "auth '" + str(auth) + "' level", str(level))

	if ip == HUB_IP:
		result = cmd_handle(command)

		#Send response
		resp = Response(str(result[1]), mimetype="text/xml")
		resp.headers["Access-Control-Allow-Origin"] = "*"
		return resp


### SEND REQUESTS ###
def send_cmd(cmd):
	cmd = str(cmd)
	ip = HUB_IP
	#Send command
	try:
		r = requests.post("http://"+ ip + ":" + SERVER_PORT, data={"command": cmd, "auth": "startrekDS9", "level": 1}, timeout=10) #NO AUTH IN FILE!
		if r.status_code < 400:
			return (1, r.text)
		else:
			if r.status_code == 500:
				return (0, "The server encountered an error processing the request\n" + r.text)
			else:
				return (0, "Something went wrong, status code " + str(r.status_code))
	except requests.exceptions.ConnectTimeout as e:
		return (0,"Could not reach HUB: Connection timeout")
	except requests.exceptions.ConnectionError as e:
		return (0,"Cound not reach HUB: Target machine actively refused connection")
	except Exception as e:
		return (0,"Cound not reach HUB due to general error: " + repr(e))


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
		log_msg(result[1], showheader=False)
	else: #Command not found
		result = (0, CMD + " " + command + " " + CMD_NOTFOUND)
		log_msg(CMD, command, CMD_NOTFOUND)
	
	return result

		
### TIME ###
def make_2_digits(st):
	st = str(st)
	return (st if len(st)>=2 else "0" + st)
def get_time_offset(offset):
	now = datetime.datetime.now()
	offset_now = now + datetime.timedelta(seconds=offset*60)
	offset_now_time = offset_now.time()
	future_time = (make_2_digits(offset_now_time.hour) + ":" + make_2_digits(offset_now_time.minute) + ":" + make_2_digits(offset_now_time.second) )
	return future_time

### SCHTASK WINDOWS ###
def sch_task(name, time, task):
	os.system("schtasks /create /tn \"" + str(name) + "\" /sc once /st " + str(time) + " /tr \"" + str(task) + "\" /f")



### CLIENT COMMANDS ###
def shutdown(*args):
	if OS_LINUX:
		os.system("sleep 60s && sudo shutdown &")
	elif OS_WIN:
		os.system("shutdown /t 60 /s")
		#os.system("start /wait timeout 10 && shutdown -s")
	return (1,"Shutting down " + NAME + " in 1 minute.")
commands["shutdown"] = shutdown

def restart(*args):
	if OS_LINUX:
		os.system("sleep 60s && sudo reboot &")
	elif OS_WIN:
		os.system("shutdown /t 60 /r")
		#os.system("start /wait timeout 10 && shutdown -r")
	return (1,"Restarting " + NAME + " in 1 minute.")
commands["restart"] = restart

def hibernate(*args):
	if OS_LINUX:
		return (0,"Not supported")
	elif OS_WIN:
		sch_task("hub_client_task_hibernate", get_time_offset(1), "shutdown /h")
		#os.system("schtasks /create /tn hub_client_task /sc once /st " + get_time_offset(10) + " /tr \"shutdown /h\"")
		#os.system("shutdown /t 10 /h")
		#os.system("start /wait timeout 10 && shutdown -h")
	return (1,"Hibernating " + NAME + " in 1 minute.")
commands["hibernate"] = hibernate

def logoff(*args):
	if OS_LINUX:
		os.system("sleep 60s && logout &")
	elif OS_WIN:
		sch_task("hub_client_task_logoff", get_time_offset(1), "shutdown /l")
		#os.system("schtasks /create /tn hub_client_task /sc once /st " + get_time_offset(10) + " /tr \"shutdown /l\"")
		#os.system("start /wait timeout 10 && shutdown -l")
	return (1,"Logging off " + NAME + " in 1 minute.")
commands["logoff"] = logoff

def unregister(*args):
	return (1,"Unregistered from HUB")
commands["unregister"] = unregister

def device_status(*args):
	return (1,"Online")
commands["status"] = device_status



### PRINTING STATUS ###
def msg(*messages, header=True):
	if not MUTE:
		comp = " ".join([str(m) for m in messages])
		print (NAME + ":" if header else "", comp)
def status_msg(*messages):
	if not MUTE:
		comp = " ".join([str(m) for m in messages])
		print (comp)
def log_msg(*messages, display=True, log=True, showheader=True):
	m = "["+str(datetime.datetime.now().strftime("%H:%M:%S"))+"] "   +   " ".join([str(m) for m in messages])
	if display: msg(m, header=showheader)

	if log:
		pass
		#try:
			#with open("client_log.txt", "a+") as f:
				#f.write(str(m) + "\n")
		#except Exception as e:
			#print ("Error: Could not write to log\n" + repr(e))


### HUB REGISTRATION ###
def register():
	global INITIAL_REGISTER_ATTEMPT
	global Register_timeout
	global RETRYING_CONNECTION


	register_cmd = "register " + NAME + " " + IP + " " + MAC
	is_registered_cmd = "isregistered " + NAME

	#Have ever registered
	if not INITIAL_REGISTER_ATTEMPT:

		log_msg(CONTACTING_HUB)
		#Try register
		result = send_cmd(register_cmd)
		status_msg(" "*5, result[1])

		#Successful register
		if result[0] != 0:
			log_msg(READY, log=False)
			INITIAL_REGISTER_ATTEMPT = True
	else: #Have been registered before
		is_registered = send_cmd(is_registered_cmd)

		#Could not contact HUB
		if is_registered[0] == 0 and not RETRYING_CONNECTION:
			log_msg(CONNECTION_LOST)
			RETRYING_CONNECTION = True

		#Is not registered now
		if is_registered[1] == "no":

			#Try register
			result = send_cmd(register_cmd)

			#Successful re-register
			if result[0] != 0:
				log_msg(CONNECTION_RESTORED)
				RETRYING_CONNECTION = False
		

	#Schedule next contact attempt
	time.sleep(Register_timeout)
	register()
	#connection_scheduler = sched.scheduler(time.time, time.sleep)
	#connection_scheduler.enter(delay=Register_timeout, priority=1, action=register)
	#connection_scheduler.run()


### MAIN ###
def main(*args):
	
	global INITIAL_REGISTER_ATTEMPT
	global MUTE
	global LOCAL_MODE
	global NAME
	global IP
	global MAC

	windows_startup_folder = "AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"


	#Arguments
	if len(args)==0:
		args = sys.argv

	if len(args) > 0:
		for arg in args:
			if "name=" in arg:
				NAME = arg.replace("name=","")
			if "ip=" in arg:
				IP = arg.replace("ip=","")
			if "mac=" in arg:
				MAC = arg.replace("mac=","")
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
					print ("Create a file called 'hub_launcher.sh'\nIn it, include 'sudo " + path + "' in the file.\nEdit /etc/rc.local and add 'sleep 6s' and 'sudo sh <path to hub_launcher.sh> &' BEFORE 'exit 0'")
					#os.system("sudo echo sleep 6s >> /etc/rc.local")
					#os.system("sudo echo sudo sh /home/cooper/hub/hub_launcher.sh & >> /etc/rc.local")
				elif OS_WIN:
					user_folder = os.environ['USERPROFILE']

					if not windows_startup_folder.lower() in path.lower():
						#cmdp = "C:/Windows/System32/cmd.exe"
						#os.system("SchTasks /Create /SC ONSTART /TN hub_client /TR \"" + cmdp + " \\\"" + path + "\\\"\"")
						os.system("copy \"" + __file__ + "\" " + "\"" + user_folder + "\\" + windows_startup_folder + "\"")
						log_msg("Client program copied to startup directory: " + user_folder + "\\" + windows_startup_folder)
					else:
						log_msg("Client program is already in the startup directory.", log=false)
	
	#Startup tip
	if not MUTE and not "startup" in args:
		if OS_LINUX:
			log_msg("Run 'python3 hub_client startup' to launch this client on startup.", log=False, showheader=False)
		elif OS_WIN:
			if not windows_startup_folder in __file__:
				log_msg("Run 'hub_client.py startup' to launch this client on startup.", log=False, showheader=False)
	

	#Remote mode (listener and registration)
	if not LOCAL_MODE:
		#Register client with HUB (On another thread, so that connection scheduler does not stop client from receiving data)
		from multiprocessing import Pool
		pool = Pool(processes=1)
		pool.apply_async(func=register)



		#Set FLASK logging to verbose (only error)
		log = logging.getLogger('werkzeug')
		log.setLevel(logging.ERROR)

		#Start FLASK listening on CLIENT_PORT
		#listener.debug = True
		listener.run(host="0.0.0.0", port=CLIENT_PORT)


#Silly windows, __main__ is for kids!
if __name__ == "__main__":
	main()