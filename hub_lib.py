#!python3

#Imports
import os
import sys
import time
import logging
import datetime
import socket
import struct
from importlib import import_module
from multiprocessing import Process
from subprocess import Popen
from uuid import getnode

# MESSAGE STRING CONSTANTS #
TITLE_SERVER = "HUB"
LOG = "LOG"
SERVER_LOG = "server_log.txt"
CLIENT_LOG = "client_log.txt"

#Command
CMD = "Command"
CMD_RECV = "Command received"
CMD_RUN = "Running"
CMD_NOTFOUND = "not Found"
CMD_EXISTS = " duplicate command"
CMD_ADD = "Add"
CMD_LVL = "level"

#Module
MODULE = "Module"
MODULE_INIT = "Initialized"
MODULE_OK = "[ OK ]"
MODULE_FAIL = "[FAIL]"

#Boot
BOOT_SUCCESS = "LOAD SUCCESS"
BOOT_FAILURE = "LOAD FAILURE"
BOOT_SELFCONTROL = "STARTED SELF CONTROL MODULE"
LOADING = "LOADING"

#Network
AUTH_FAIL = "Authorization invalid"
RETRYING = "Retrying connection in"
CONNECTION_LOST = "Connection to HUB lost."
CONNECTION_RESTORED = "Connection restored."
CONTACTING_HUB = "Contacting HUB to register"
READY = "Connected to HUB. Awaiting commands"
VALIDMACCHARS = "0123456789abcdefABCDEF"

#Error
ERROR = "Error:"


### AUTHORIZATION ###
def authorize(key):
	h = bhash(key)
	valid = h in auths
	return (valid, auths[h] if valid else -100)
def bhash(key):
	r = 0
	for i in range(0,len(key)):
		r += (i+1) * ord(key[i])
	return r;


### NETWORK ###
def get_ip_address():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	return s.getsockname()[0]
def get_mac_address():
	return "".join(c + ":" if i % 2 else c for i, c in enumerate(hex( getnode() )[2:].zfill(12)))[:-1]

def valid_mac(MAC):
	#D3:38:9F... (17char)
	#D3389F...   (12char)
	if len(MAC) == 17:
		MAC = "".join(MAC.split(MAC[2]))
	if len(MAC) == 12:
			if all(C in VALIDMACCHARS for C in MAC): #Valid characters in each section
				return True
	return False		
def valid_ip(IP):
	SPIP = IP.split(".")
	return IP.count(".")==3 and all(True if (try_int(N) >= 0 and try_int(N) <= 255) else False for N in SPIP)

def clean_mac(MAC):
	return MAC.replace(MAC[2],"").upper() if len(MAC)==17 else MAC.upper()
	

### SEND REQUESTS ###
def send_cmd(cmd, ip, port, auth_key):
	#Send command
	try:
		r = requests.post("http://"+ ip + ":" + port, data={"command": cmd, "auth": auth_key}, timeout=5)
		if r.status_code < 400:
			return (1, r.text)
		else:
			if r.status_code == 500:
				return (0, ip + " encountered an error processing the request\n" + r.text)
			else:
				return (0, "Something went wrong, status code " + str(r.status_code))
	except requests.exceptions.ConnectTimeout as e:
		return (0,"Could not reach "+ip+": Connection timeout")
	except requests.exceptions.ConnectionError as e:
		return (0,"Cound not reach "+ip+": Machine actively refused connection")
	except Exception as e:
		return (0,"Cound not reach "+ip+" due to general error: " + repr(e))


### TERMINAL COMMAND WAIT ###
def wait_exec_cmd(t, func, args=[]):
	time.sleep(t)
	func(*args) if len(args) > 0 else func()
def exec_cmd(time, func, args=[]):
	p = Process(target=wait_exec_cmd, args=(time, func, args))
	p.start()


### PRINTING STATUS ###
def msg(*messages, header=""):
	comp = " ".join([str(m) for m in messages])
	print (header + (":" if len(header)>0 else ""), comp)
#def status_msg(*messages):
	#comp = " ".join([str(m) for m in messages])
	#print (comp)
def log_msg(*messages, display=True, log="", header=""):
	m = " ".join([str(m) for m in messages])
	if display: msg(m, header=header)

	if len(log)>0:
		lm = "["+str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+"] "   +   m
		try:
			with open(log, "a+") as f:
				f.write(str(lm) + "\n")
		except Exception as e:
			print ("Error: Could not write to " + log + "\n" + repr(e))


### OTHER ###
def try_int(s):
    try:
        return int(s)
    except ValueError:
        return -1


# SYSTEM VARS #

#OS
OS_WIN = os.name == "nt"
OS_LINUX = os.name == "posix"

#Python
PYTHON_CMD = "python3" if OS_LINUX else "python.exe" if OS_WIN else ""

#Authorization
auths = {}
auths[2177] = 0 #picard
auths[5990] = 1 #startrekDS9

#Network (TODO: Load from file)
HUB_IP = "192.168.1.72"
PORT = "5000"
THIS_NAME = socket.gethostname()
THIS_IP = get_ip_address()
THIS_MAC = clean_mac(get_mac_address())

def set_name(name):
	global THIS_NAME
	THIS_NAME = name
def set_ip(ip):
	global THIS_IP
	THIS_IP = ip
def set_mac(mac):
	global THIS_MAC
	THIS_MAC = mac
def get_name():
	return THIS_NAME
def get_ip():
	return THIS_IP
def get_mac():
	return THIS_MAC


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
		os.system(PYTHON_CMD + " \"" + __file__ + "\"")
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
		os.system(PYTHON_CMD + " \"" + __file__ + "\"")
	else:
		sys.exit()