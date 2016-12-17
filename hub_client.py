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

RETRYING = "Retrying connection..."
CONNECTION_LOST = "Connection to HUB lost."
CONTACTING_HUB = "Contacting HUB to register"
READY = "Connected to HUB. Awaiting commands"
ERROR = "Error:"

#Network
HUB_IP = "192.168.1.72"
PORT = "5000"

#Authorization
auth = "startrekDS9" #NO!
level = 1

REGISTERED = False


#Client commands
commands = {}


### INCOMING REQUESTS ###
listener = Flask(__name__)
@listener.route('/', methods=["POST"])
def cmd_post():

	#Get Variables
	command = str(request.form["command"])
	ip = str(request.remote_addr)

	#Command received
	msg("["+str(datetime.datetime.now().strftime("%H:%M:%S"))+"]", str(command), CMD.lower(), "from", ip)#, "auth '" + str(auth) + "' level", str(level))

	if request.remote_addr == HUB_IP:
		result = cmd_handle(command)

		#Send response
		resp = Response(str(result), mimetype="text/xml")
		resp.headers["Access-Control-Allow-Origin"] = "*"
		return resp


### SEND REQUESTS ###
def send_cmd(cmd):
	cmd = str(cmd)
	#Send command
	try:
		r = requests.post("http://"+ HUB_IP + ":" + PORT, data={"command": cmd, "auth": auth, "level": level}, timeout=5)
		if r.status_code < 400:
			return (1, r.txt)
		else:
			if r.status_code == 500:
				return (0, "The server encountered an error processing the request")
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
	#Command received
	#msg(CMD_RECV + cmd)


	#Split command
	sp = cmdargs.split(" ")
	command = sp[0].lower()
	args = sp[1:]

	#Check if command exists in any module
	if command in commands:
		#Run command in module
		try:
			result = commands[command](*args)
		except Exception:
			result = (0, "Command encountered an error while running.")

		#Print result
		msg(result[1])
		
		return result[1]
	else: #Command not found
		msg(CMD, command, CMD_NOTFOUND)
		return CMD + " " + command + " " + CMD_NOTFOUND
		



### CLIENT COMMANDS ###
def shutdown(*args):
	if OS_LINUX:
		os.system("sudo shutdown")
	elif OS_WIN:
		os.system("shutdown -s")
	return (1,"Shutting down")
commands["shutdown"] = shutdown

def restart(*args):
	if OS_LINUX:
		os.system("sudo reboot")
	elif OS_WIN:
		os.system("shutdown -r")
	return (1,"Restarting")
commands["restart"] = restart

def hibernate(*args):
	if OS_LINUX:
		os.system("sudo shutdown")
	elif OS_WIN:
		os.system("shutdown -s")
	return (1,"Hibernating")
commands["hibernate"] = hibernate

def logoff(*args):
	if OS_LINUX:
		os.system("logout")
	elif OS_WIN:
		os.system("shutdown -l")
	return (1,"Logging off")
commands["logoff"] = logoff

def unregister(*args):
	return (1,"Unregistered from HUB")
commands["unregister"] = unregister




### PRINTING STATUS ###
def msg(*messages):
	comp = " ".join([str(m) for m in messages])
	print (TITLE + ":", comp)
def status_msg(*messages):
	comp = " ".join([str(m) for m in messages])
	print (comp)
def log_msg(*messages):
	comp = " ".join([str(m) for m in messages])
	print ("["+str(datetime.datetime.now().strftime("%H:%M:%S"))+"]", comp)


### HUB REGISTRATION ###
def register(REGISTERED, NAME, IP, MAC):
	register_cmd = "register " + NAME + " " + IP + " " + MAC
	ping = send_cmd("ping")

	if REGISTERED == False:
		log_msg(CONTACTING_HUB)
		result = send_cmd(register_cmd)
		status_msg(" "*5, result[1])

		if result[0] != 0:
			msg(READY)
			REGISTERED = True
	else:
		if ping[0] == 0:
			log_msg(CONNECTION_LOST, RETRYING)
			status_msg(" "*5, ping[1])
		

	#Schedule next contact attempt
	connection_scheduler = sched.scheduler(time.time, time.sleep)
	connection_scheduler.enter(delay=10, priority=1, action=register, argument=([REGISTERED, NAME, IP, MAC]))
	connection_scheduler.run()


### MAIN ###
def main():

	#Get device IP, MAC and name
	NAME = socket.gethostname()
	IP = socket.gethostbyname(socket.getfqdn())
	MAC = "".join(c + ":" if i % 2 else c for i, c in enumerate(hex( getnode() )[2:].zfill(12)))[:-1]
	OS_WIN = os.name == "nt"
	OS_LINUX = os.name == "posix"


	#Register client with HUB
	register(REGISTERED, NAME, IP, MAC)



	#Set FLASK logging to verbose (only error)
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.ERROR)

	#Start FLASK listening 
	#listener.debug = True
	listener.run(host='0.0.0.0')


#Silly windows, __main__ is for kids!
if __name__ == "__main__":
	main()