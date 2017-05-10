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
#import netifaces

# MESSAGE STRING CONSTANTS #
TITLE_SERVER = "HUB"
LOG = "LOG"
SERVER_LOG = "hub_server_log.txt"
CLIENT_LOG = "hub_client_log.txt"

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
BOOT_SUCCESS = "LOAD COMPLETE"
BOOT_FAILURE = "LOAD FAILURE"
BOOT_SELFCONTROL = "STARTED SELF CONTROL MODULE"
LOADING = "LOADING"

#Network
AUTH_FAIL = "Authentication invalid"
RETRYING = "Retrying connection in"
CONNECTION_LOST = "Connection to HUB lost."
CONNECTION_RESTORED = "Connection restored."
CONTACTING_HUB = "Contacting HUB to register"
READY = "Connected to HUB. Awaiting commands"
VALIDMACCHARS = "0123456789abcdefABCDEF"

#Error
ERROR = "Error:"


# SYSTEM VARS #

#OS
OS_WIN = os.name == "nt"
OS_LINUX = os.name == "posix"

#Logging
user_folder = os.path.expanduser("~")

#Python
PYTHON_CMD = "python3" if OS_LINUX else "python.exe" if OS_WIN else ""

#Authorization
auths = {}
auths[2177] = 0 #picard
auths[5990] = 1 #startrekDS9
#auths[3828] = 1 #brobeans

#Network (TODO: Load from file)
HUB_IP = "192.168.1.72"
PORT = 5000

#This device
THIS_NAME = ""
THIS_IP = ""
THIS_MAC = ""


### NETWORK ###
def get_hostname():
	global THIS_NAME
	if THIS_NAME == "":
		THIS_NAME = socket.gethostname()
	return THIS_NAME

def get_ip_address():
	global THIS_IP
	if THIS_IP == "":
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(("8.8.8.8", 80))
		THIS_IP = s.getsockname()[0]
	return THIS_IP



def get_mac_address():
	global THIS_MAC

	if THIS_MAC == "":
		if OS_WIN: 
			for line in os.popen("ipconfig /all"): 
				if line.lstrip().startswith('Physical Address'):
					mac = line.split(':')[1].strip().replace('-',':')
					break 
		else: 
			for line in os.popen("/sbin/ifconfig"): 
				if line.find('Ether') > -1: 
					mac = line.split()[4] 
					break
		THIS_MAC = clean_mac(mac)
	#THIS_MAC = clean_mac("".join(c + ":" if i % 2 else c for i, c in enumerate(hex( getnode() )[2:].zfill(12)))[:-1])
	return THIS_MAC

def valid_mac(MAC):
	#D3:38:9F... (17char)
	#D3389F...   (12char)
	if len(MAC) == 17:
		MAC = "".join(MAC.split(MAC[2]))
	if len(MAC) == 12:
			if all(C in VALIDMACCHARS for C in MAC): #Valid characters in each section
				return True
	return False
	
def try_int(s):
    try: return int(s)
    except ValueError: return -1			
def valid_ip(IP):
	SPIP = IP.split(".")
	return IP.count(".")==3 and all(True if (try_int(N) >= 0 and try_int(N) <= 255) else False for N in SPIP)

def clean_mac(MAC):
	return MAC.replace(MAC[2],"").upper() if len(MAC)==17 else MAC.upper()

def set_name(name):
	global THIS_NAME
	THIS_NAME = name
def set_ip(ip):
	global THIS_IP
	THIS_IP = ip
def set_mac(mac):
	global THIS_MAC
	THIS_MAC = mac



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


### SEND REQUESTS  ###
def send_cmd(cmd, ip, port, auth_key):
	try:

		#Send request
		r = requests.get("http://"+ str(ip) + ":" + str(port) + "/?auth=" + str(auth_key) + "&command=" + str(cmd), timeout=5)

		#Request response
		if r.status_code < 400: #Response good
			return (1, r.text)
		elif r.status_code == 500: #Response server error
			return (0, str(ip) + " encountered an error processing the request\n" + r.text)
		else: #Response bad
			return (0, "Something went wrong, status code " + str(r.status_code))

	except requests.exceptions.ConnectTimeout as e:
		return (0,"Could not reach "+str(ip)+": Connection timeout")
	except requests.exceptions.ConnectionError as e:
		return (0,"Cound not reach "+str(ip)+": Machine actively refused connection")
	except Exception as e:
		return (0,"Cound not reach "+str(ip)+" due to general error: " + repr(e))


### RUN TERMINAL COMMAND AFTER SLEEP ###
def wait_exec_cmd(t, func, args=[]):
	time.sleep(t)
	func(*args) if len(args) > 0 else func()
def exec_cmd(time, func, args=[]):
	p = Process(target=wait_exec_cmd, args=(time, func, args))
	p.start()


### PRINTING STATUS ###
def msg(*messages, header=""):
	comp = " ".join([str(m) for m in messages])
	print(header + (":" if len(header)>0 else ""), comp)

def log_msg(*messages, display=True, log="", header=""):
	m = " ".join([str(m) for m in messages])
	lm = "["+str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+"] "   +   m
	
	if len(log)>0:
		try:
			dir = (user_folder + ( "\\Desktop\\") if OS_WIN else "")
			f = open( dir + log, "a+")
			f.write(str(lm) + "\n")
			f.close()
		except Exception as e:
			print("Error: Could not write to " + log + "\n" + repr(e))
			
	if display: msg(lm, header=header)

def print_header(title):
	try:
		import math

		N0 = (22-len(title))
		N0S = math.floor(N0/2)
		N0E = (N0S+1) if N0%2!=0 else N0S

		N = (22-len(get_name()))
		NS = math.floor(N/2)
		NE = (NS+1) if N%2!=0 else NS

		N1 = (22-len(get_ip_address()))
		N1S = math.floor(N1/2)
		N1E = (N1S+1) if N1%2!=0 else N1S

		N2 = (22-len(get_mac()))
		N2S = math.floor(N2/2)
		N2E = (N2S+1) if N2%2!=0 else N2S

		#Creator
		log_msg("################################")
		log_msg("#####" + " "*N0S + title + " "*N0E + "#####")
		log_msg("#####   Zach Lerew 2016    #####")
		log_msg("#####                      #####")

		#Device
		log_msg("#####" + " "*NS  + get_name() + " " *NE  + "#####")
		log_msg("##IP#" + " "*N1S + get_ip_address()   + " " *N1E + "#####")
		log_msg("#MAC#" + " "*N2S + get_mac()  + " " *N2E + "#####")

		log_msg("################################")
	except Exception as e:
		pass #Meh, if the header breaks don't throw a fit


### OTHER ###



### SCHTASK WINDOWS ###
#def sch_task_startup(name, task):
#	os.system("schtasks /create /tn \"" + str(name) + "\" /sc onstart /tr \"" + str(task) + "\" /f")


### VERIFY PYTHON VERSION ###
if sys.version_info[0] < 3:
	print("This program requires python version 3.5.2+. You have version " + str(sys.version_info) + "\nPlease download the latest version.")
	download = raw_input("Would you like to open the python  download page? Y/N:")
	if download.lower()=="y":
		import webbrowser
		webbrowser.open("http://www.python.org/downloads", new=0, autoraise=True)
	sys.exit()
### VERIFY REQUESTS LIBRARY ###
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
### VERIFY FLASK LIBRARY ###
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
