### IMPORTING ###
import requests
import struct
import socket
import sys
import os
from uuid import getnode

#Hub self control
import hub_client


### Load abstract default module ###
sys.path.append('/home/cooper/hub/modules')
from default_module import default_module

#Network
CLIENT_PORT = "5001"
HUB_IP = ""
HUB_MAC = ""


#Taken device names
device_hub = "hub"


### HELPERS ###
def try_int(s):
    try:
        return int(s)
    except ValueError:
        return -1

VALIDMACCHARS = "0123456789abcdefABCDEF"
def valid_mac(MAC):
	split = MAC.split(MAC[2])
	if len(MAC) == 17: #D3:38:9F... > D3389F...
		MAC = "".join(split)
	if len(MAC) == 12:
			if all(C in VALIDMACCHARS for C in MAC): #Valid characters in each section
				return True
	return False
def clean_mac(MAC):
	if len(MAC)==17:
		return MAC.replace(MAC[2], "").upper()
	else:
		return MAC.upper()

def valid_ip(IP):
	SPIP = IP.split(".")
	return IP.count(".")==3 and all(True if (try_int(N) >= 0 and try_int(N) <= 255) else False for N in SPIP)


## NETWORK ##
def get_ip_address():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	return s.getsockname()[0]
def get_mac_address():
	return clean_mac("".join(c + ":" if i % 2 else c for i, c in enumerate(hex( getnode() )[2:].zfill(12)))[:-1])

class device_control(default_module):

	def __init__(self, *args):
		super().__init__()

		#Get HUB address info
		HUB_IP = get_ip_address()
		HUB_MAC = get_mac_address()

		#from multiprocessing import Pool
		#pool = Pool(processes=1)
		#pool.apply_async(func=hub_client.main, args=["name=hub"])
		#log_msg(BOOT_SELFCONTROL, log=False)
		hub_client.main("name=hub", "local_mode", "mute")#, "mute", "registered"])
		

		## Devices ##
		self.devices = {}
		self.devices[device_hub] = (HUB_IP, HUB_MAC)

		## Bind Functions ##
		self.commands["wake"] = self.wake
		self.arguments["wake"] = "<ip address> <mac address>, <device name>"
		self.description["wake"] = "Wake a LAN computer by address or by name. Only works for WIRED computers."

		self.commands["shutdown"] = self.shutdown
		self.arguments["shutdown"] = "<device name>"
		self.description["shutdown"] = "Shutdown a LAN computer (Cannot be woken using 'wake')"

		self.commands["hibernate"] = self.hibernate
		self.arguments["hibernate"] = "<device name>"
		self.description["hibernate"] = "Hibernate a LAN computer (Can be woken using 'wake')"

		self.commands["restart"] = self.restart
		self.arguments["restart"] = "<device name>"
		self.description["restart"] = "Restart a LAN computer"

		self.commands["logoff"] = self.logoff
		self.arguments["logoff"] = "<device name>"
		self.description["logoff"] = "Log off a LAN computer"

		self.commands["ping"] = self.ping
		self.restriction["ping"] = -1
		self.arguments["ping"] = ""
		self.description["ping"] = "Check connection to HUB"

		self.commands["isregistered"] = self.device_is_registered
		self.restriction["isregistered"] = -1
		self.arguments["isregistered"] = ""
		self.description["isregistered"] = "Check if device is registered to the HUB"


		self.commands["register"] = self.register_device
		self.restriction["register"] = 1
		self.arguments["register"] = "<device name> <ip address> <mac address>"
		self.description["register"] = "Register device as a client to the HUB"

		self.commands["unregister"] = self.unregister_device
		self.restriction["unregister"] = 1
		self.arguments["unregister"] = "<device name>"
		self.description["unregister"] = "Un-register device from the HUB"

		self.commands["devices"] = self.get_devices
		self.arguments["devices"] = ""
		self.description["devices"] = "Get the current list of devices"

		self.commands["status"] = self.device_status
		self.arguments["status"] = "<device name>"
		self.description["status"] = "Get network status of LAN device"




	### COMMAND FUNCTIONS ###

	### POWER OPTIONS ###
	def wake(self, *args):
		if len(args) == 1: #Wake by device name
			name = str(args[0])
			target = self.get_device(name)
			if target != None:
				self.sub_wake(target[0], target[1])
				return (1,"Sending magic packet to " + name)
			else:
				return (0,"Device " + name + " could not be found")
		elif len(args) == 2:#Wake by IP and MAC
			return self.sub_wake(args[0], args[1])
		else:
			return (0,"Incorrect Arguments")
	def sub_wake(self, IP, MAC):
		#os.system("wakeonlan -i " + args[0] + " " + args[1])
		try:
			if valid_ip(IP):
				if valid_mac(MAC):
					MAC = clean_mac(MAC)
					#Pad the synchronization stream.
					data = ''.join(['FFFFFFFFFFFF', MAC * 20])
					send_data = b''

					#Split up the hex values and pack.
					send_data = b''
					for i in range(0, len(data), 2):
						send_data = b''.join([send_data, struct.pack('B', int(data[i: i + 2], 16))])

					#Broadcast WOL
					#sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
					#sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
					#sock.sendto(send_data, (IP, 9)) #Port 9

					return (1,"Sending magic packet to " + args[0] + "(MAC:" + args[1] + ")")
				else:
					return(0,"Invalid MAC address " + MAC)
			else:
				return (0,"Invalid IP address " + IP)
		except Exception as e:
			return (0,"Wake encountered an error while running: " + repr(e))


	def shutdown(self, *args):
		#print "shutdown:", args 
		if len(args) > 0:
			target = str(args[0]).lower()
			return self.send_cmd(target, "shutdown")
		else:
			return (0,"Missing Arguments")

	def hibernate(self, *args):
		if len(args) > 0:
			target = str(args[0]).lower()
			return self.send_cmd(target, "hibernate")
		else:
			return (0,"Missing Arguments")

	def restart(self, *args):
		#print "restart:", args
		if len(args) > 0:
			target = str(args[0]).lower()
			return self.send_cmd(target, "restart")
		else:
			return (0,"Missing Arguments")

	def logoff(self, *args):
		if len(args) > 0:
			target = str(args[0]).lower()
			return self.send_cmd(target, "logoff")
		else:
			return (0,"Missing Arguments")

	def device_is_registered(self, *args):
		if len(args) > 0:
			target = str(args[0]).lower()
			device = self.get_device(target)
			if device != None:
				return (1,"yes")
			else:
				return (0,"no")
		else:
			return (0,"Missing Arguments")
	def device_status(self, *args):
		if len(args) > 0:
			target = str(args[0]).lower()
			status = self.send_cmd(target, "status")
			return (0,"Offline" if status[0]==0 else status)
		else:
			return (0,"Missing Arguments")



	### REMOTE DEVICE MANAGEMENT ###
	def add_update_device(self, name, ip, mac):
		if name is not device_hub: #Hub cannot be changed or added
			device = self.get_device(name)

			if device != None: #Edit or do nothing
				if device[0] != ip or device[1] != mac: #Edit
					self.devices[name] = (ip, mac)
					return (1, name + " device information changed")
				else: #do nothing
					return (1, "Device " + name + " already registered")
			else: #New
				if valid_ip(ip):
					if valid_mac(mac):
						mac = clean_mac(mac)

						self.devices[name] = (ip, mac)
						return (1, "Registered device " + name + ", IP=" + ip + ", MAC=" + mac)
					else:
						return (0,"MAC address format incorrect:" + mac)
				else:
					return (0,"IP address format incorrect:" + ip)
		else:
			return (0,"This device name is taken (for the HUB)")

	def get_device(self, name):
		if name.lower() in self.devices:
			return self.devices[name]
		else:
			return None

	def get_devices(self, *args):
		s = "Name" + " "*6 + "IP" + " "*13 + "MAC" + "\n"
		for n,a in self.devices.items():
			ip = a[0]
			mac = a[1]
			s += n[0:10] + " "*(10-len(n)) + str(ip) + " "*(15-len(ip)) + str(mac) + "\n"
		return (1,s)

	def register_device(self, *args):
		if len(args) > 2:
			proper_name = str(args[0])
			name = proper_name.lower()
			ip = str(args[1])
			mac = clean_mac(str(args[2]))

			return self.add_update_device(name, ip, mac)
		else:
			return (0,"Missing Arguments")

	def ping(self, *args):
		return (1,"Connection established")

	def unregister_device(self, *args):
		if len(args) == 1:
			device = args[0].lower()

			if device != device_hub:
				if device in self.devices:
					self.send_cmd(device, "unregister")
					self.devices.pop(device, None)
					return (1,"Un-registered " + device)
				else:
					return (0,"Device " + device + " could not be found")
			else:
				return (0,"Cannot unregister the HUB")
		else:
			return (0,"Missing Arguments")


	def send_cmd(self, target, cmd):
		if target == device_hub:
			return hub_client.cmd_handle(cmd)
		else:
			device = self.get_device(str(target))
			cmd = str(cmd)
			if device != None:
				ip = device[0]

				#Send command
				try:
					r = requests.post("http://"+ ip + ":" + CLIENT_PORT, data={"command": cmd}, timeout=10) #"auth": "startrekDS9", "level": 1
					if r.status_code < 400:
						return (1, r.text)
					else:
						if r.status_code == 500:
							return (0, "The server encountered an error processing the request")
						else:
							return (0, "Something went wrong, status code " + str(r.status_code))
				except requests.exceptions.ConnectTimeout as e:
					return (0,"Could not reach " + target + ": Connection timeout")
				except requests.exceptions.ConnectionError as e:
					return (0,"Cound not reach " + target + ": Target machine actively refused connection")
				except Exception as e:
					return (0,"Cound not reach " + target + " due to general error: " + repr(e))
	### END COMMAND FUNCTIONS ###
