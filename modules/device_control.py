### IMPORTING ###
import requests
import struct
import socket
import sys
import os

### Load abstract default module ###
sys.path.append('/home/cooper/hub/modules')
from default_module import default_module

#Network
PORT = "5000"

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


class device_control(default_module):

	def __init__(self, *args):
		super().__init__()

		## Devices ##
		self.devices = {}
		self.devices[device_hub] = ("The","HUB")

		## Bind Functions ##
		self.commands["wake"] = self.wake
		self.arguments["wake"] = "<ip address> <mac address>, <device name>"
		self.description["wake"] = "Wake a LAN computer by address or by name"

		self.commands["shutdown"] = self.shutdown
		self.arguments["shutdown"] = "<device name>, pi"
		self.description["shutdown"] = "Shutdown a LAN computer (Cannot be woken using 'wake'), Shutdown this Raspberry PI"

		self.commands["hibernate"] = self.hibernate
		self.arguments["hibernate"] = "<device name>"
		self.description["hibernate"] = "Hibernate a LAN computer (Can be woken using 'wake')"

		self.commands["restart"] = self.restart
		self.arguments["restart"] = "<device name>, pi"
		self.description["restart"] = "Restart a LAN computer, Reboot this Raspberry PI"


		self.commands["ping"] = self.ping
		self.restriction["ping"] = -1
		self.arguments["ping"] = ""
		self.description["ping"] = "Check connection to HUB"

		self.commands["register"] = self.register
		self.restriction["register"] = 1
		self.arguments["register"] = "<ip address> <mac address> <device name>"
		self.description["register"] = "Register device as a client to the HUB"

		self.commands["unregister"] = self.unregister
		self.restriction["unregister"] = 1
		self.arguments["unregister"] = "<device name>"
		self.description["unregister"] = "Un-register device from the HUB"

		self.commands["devices"] = self.get_devices
		self.arguments["devices"] = ""
		self.description["devices"] = "Get the current list of devices"




	### COMMAND FUNCTIONS ###

	### POWER OPTIONS ###
	def wake(self, *args):
		if len(args) > 0:
			target = str(args[0]).lower()
			if target == device_hub:
				return (0, "The HUB cannot be woken from itself")
		if len(args) == 1: #Wake by name
			if target in self.devices:
				d = self.devices[target]
				self.sub_wake(d[0], d[1])
				return (1,"Sending magic packet to " + args[0])
			else:
				return (0,"Device " + target + " could not be found")
		elif len(args) == 2:#Wake by IP and MAC
			self.sub_wake(args[0], args[1])
			return (1,"Sending magic packet to " + args[0] + "(MAC:" + args[1] + ")")
		else:
			return (0,"Incorrect Arguments")
	def sub_wake(self, IP, MAC):
		#os.system("wakeonlan -i " + args[0] + " " + args[1])

		#Pad the synchronization stream.
		data = ''.join(['FFFFFFFFFFFF', MAC * 20])
		send_data = b''

		#Split up the hex values and pack.
		send_data = b''
		for i in range(0, len(data), 2):
			send_data = b''.join([send_data, struct.pack('B', int(data[i: i + 2], 16))])

		#Broadcast WOL
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		sock.sendto(send_data, (IP, 9)) #Port 9

	def shutdown(self, *args):
		#print "shutdown:", args 
		if len(args) > 0:
			target = str(args[0]).lower()
			if target==device_hub:
				os.system("sudo shutdown")
				return (1,"Sent shutdown command to " + args[0])
			else:
				return self.send_cmd(target, "shutdown")
		else:
			return (0,"Missing Arguments")

	def hibernate(self, *args):
		if len(args) > 0:
			target = str(args[0]).lower()
			if target == device_hub:
				return (0, "The HUB cannot hibernate")
		if len(args) > 0:
			return self.send_cmd(target, "hibernate")
		else:
			return (0,"Missing Arguments")

	def restart(self, *args):
		#print "restart:", args
		if len(args) > 0:
			target = str(args[0]).lower()
			if target == device_hub:
				os.system("sleep 10s && sudo reboot &")
				return (1,"Sent restart command to " + args[0])
			else:
				return self.send_cmd(target, "restart")
		else:
			return (0,"Missing Arguments")

	def logoff(self, *args):
		if len(args) > 0:
			target = str(args[0]).lower()
			if target == device_hub:
				os.system("logout")
				return (1,"Sent logoff command to " + args[0])
			else:
				return self.send_cmd(target, "logoff")
		else:
			return (0,"Missing Arguments")



	### REMOTE DEVICE MANAGEMENT ###
	def add_update_device(self, name, ip, mac):
		if name is not device_hub: #Hub cannot be changed or added
			device = get_device(name)

			if device != None: #Edit or do nothing
				if device[0] != ip or device[1] != mac: #Edit
					self.devices[name] = (ip, mac)
					return (1, proper_name + " device information changed")
				else: #do nothing
					return (1, "Device " + proper_name + " already registered")
			else: #New
				if valid_ip(ip):
					if valid_mac(mac):
						mac = clean_mac(mac)

						self.devices[name] = (ip, mac)
						return (1, "Registered device " + proper_name + ", IP=" + ip + ", MAC=" + mac)
					else:
						return (0,"MAC address format incorrect:" + mac)
				else:
					return (0,"IP address format incorrect:" + ip)
		else:
			return (0,"This device name is taken (for the HUB)")

	def get_device(self, name):
		if name in self.devices:
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

	def register(self, *args):
		if len(args) > 2:
			proper_name = str(args[0])
			name = proper_name.lower()
			ip = str(args[1])
			mac = clean_mac(str(args[2]))

			add_update_device(name, ip, mac)
		else:
			return (0,"Missing Arguments")

	def ping(self, *args):
		return (1,"Connection established")

	def unregister(self, *args):
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


	def send_cmd(self, device, cmd):
		device = str(device)
		cmd = str(cmd)
		if device in self.devices:
			ip = self.devices[device][0]
			#Send command
			try:
				r = requests.post("http://"+ ip + ":" + PORT, data={"command": cmd}, timeout=5)
				status_code = 1 if r.status_code < 400 else 0
				result = "Sent " + cmd + " command to " + device + " response=" + (r.text if status_code == 1 else "ERROR")
				return (status_code, result)
			except requests.exceptions.ConnectTimeout as e:
				return (0,"Could not contact " + device + ": Connection timeout")
			except Exception as e:
				return (0,"There was an error while contacting " + device + ":" + repr(e))
		else:
			return (0,"Device " + str(device) + " could not be found")

	### END COMMAND FUNCTIONS ###
