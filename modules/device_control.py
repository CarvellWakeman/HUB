### IMPORTING ###
import sys
import os

#HUB LIB
from hub_lib import *

#Hub self control
import hub_client


### Load abstract default module ###
sys.path.append(str(os.path.dirname(os.path.realpath(__file__)))) #Append modules path so we know where to find default_module
from default_module import default_module

#HUB device control
device_hub = "hub"

class Device(object):
	def __init__(self, name, ip, mac):
		self.name = name
		self.ip = ip
		self.mac = mac
		#self.status = "Online"

	def get_ip(self): return self.ip
	def get_mac(self): return self.mac
	#def get_status(self): return self.status



class device_control(default_module):

	def __init__(self, *args):
		super().__init__()

		#Self control
		hub_client.main("name=hub", "local_mode", "mute")


		## Devices ##
		self.devices = {}
		self.devices[device_hub] = Device(device_hub, get_ip_address(), get_mac_address())

		## Bind Functions ##
		self.commands["wake"] = self.wake
		self.arguments["wake"] = "<ip address> <mac address>, <device>"
		self.description["wake"] = "Wake a wired LAN computer"

		#Temporary disable
		self.commands["shutdown"] = self.shutdown
		self.arguments["shutdown"] = "<device name>"
		self.description["shutdown"] = "Shutdown a LAN computer (Cannot be woken using 'wake')"

		self.commands["hibernate"] = self.hibernate
		self.arguments["hibernate"] = "<device>"
		self.description["hibernate"] = "Hibernate a LAN computer"

		self.commands["restart"] = self.restart
		self.arguments["restart"] = "<device>"
		self.description["restart"] = "Restart a LAN computer"

		self.commands["logoff"] = self.logoff
		self.arguments["logoff"] = "<device>"
		self.description["logoff"] = "Log off a LAN computer"

		self.commands["isregistered"] = self.device_is_registered
		self.restriction["isregistered"] = -1
		self.arguments["isregistered"] = "<device>"
		self.description["isregistered"] = "Check if device is registered to the HUB"


		self.commands["register"] = self.register_device
		self.restriction["register"] = 0
		self.arguments["register"] = "<device> <ip address> <mac address>"
		self.description["register"] = "Register device as a client to the HUB"

		self.commands["unregister"] = self.unregister_device
		self.restriction["unregister"] = 0
		self.arguments["unregister"] = "<device>"
		self.description["unregister"] = "Un-register device from the HUB"

		self.commands["devices"] = self.get_devices
		self.arguments["devices"] = ""
		self.description["devices"] = "Get the current list of devices"

		self.commands["status"] = self.device_status
		self.arguments["status"] = "<device>"
		self.description["status"] = "Get network status of LAN device"




	### COMMANDS ###

	## POWER OPTIONS ##
	def wake(self, *args):
		if len(args) == 2: #Wake by device name
			name = str(args[1]).lower()
			device = self.get_device(name)
			if device != None:
				self.sub_wake(device.get_ip(), device.get_mac())
				return (1,"Sending magic packet to " + name)
			else:
				return (0,"Device " + name + " could not be found")
		elif len(args) == 2:#Wake by IP and MAC
			return self.sub_wake(args[1], args[2])
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
					sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
					sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
					sock.sendto(send_data, (IP, 9)) #Port 9

					return (1,"Sending magic packet to " + IP + " (MAC:" + MAC + ")")
				else:
					return(0,"Invalid MAC address " + MAC)
			else:
				return (0,"Invalid IP address " + IP)
		except Exception as e:
			return (0,"Wake encountered an error while running: " + repr(e))


	def shutdown(self, *args):
		if len(args) > 1:
			name = str(args[1]).lower()
			return self.try_send_cmd(args[0], name, "shutdown")
		else:
			return (0,"Missing Arguments")

	def hibernate(self, *args):
		if len(args) > 1:
			name = str(args[1]).lower()
			return self.try_send_cmd(args[0], name, "hibernate")
		else:
			return (0,"Missing Arguments")

	def restart(self, *args):
		if len(args) > 1:
			name = str(args[1]).lower()
			return self.try_send_cmd(args[0], name, "restart")
		else:
			return (0,"Missing Arguments")

	def logoff(self, *args):
		if len(args) > 1:
			name = str(args[1]).lower()
			return self.try_send_cmd(args[0], name, "logoff")
		else:
			return (0,"Missing Arguments")

	def device_is_registered(self, *args):
		if len(args) > 1:
			name = str(args[1]).lower()
			device = self.get_device(name)
			if device != None:
				return (1,"yes")
			else:
				return (0,"no")
		else:
			return (0,"Missing Arguments")
	def device_status(self, *args):
		if len(args) > 1:   
			name = str(args[1]).lower()
			status = self.try_send_cmd(args[0], name, "status")
			if status != None:
				return (0,"Offline" if status[0]==0 else status[1])
			else:
				return (0,"Device " + name + " could not be found")
		else:
			return (0,"Missing Arguments")

	def get_devices(self, *args):
			s = "NAME" + " "*7 + "IP" + " "*14 + "MAC" + " "*12 + "STATUS" + "\n"
			for n,a in self.devices.items():
				ip = a.get_ip()
				mac = a.get_mac()
				status = self.device_status(args[0], n)[1]
				s += n[0:10] + " "*(11-len(n)) + str(ip) + " "*(16-len(ip)) + str(mac) + " "*3 + str(status) + "\n"
			return (1,s)



	### REMOTE DEVICE MANAGEMENT ###
	def add_update_device(self, name, ip, phys_addr):
		if name is not device_hub: #Hub cannot be changed or added
			device = self.get_device(name)

			if device != None: #Edit or do nothing
				if device.get_ip() != ip:# or device[1] != mac: #Edit
					self.devices[name] = Device(name, ip, phys_addr)
					return (1, name + " device information changed")
				else: #do nothing
					return (1, "Device " + name + " already registered")
			else: #New
				if valid_ip(ip):
					if valid_mac(phys_addr):
						mac = clean_mac(phys_addr)

						self.devices[name] = Device(name, ip, mac)
						return (1, "Registered device " + name + ", IP=" + ip + ", MAC=" + mac)
					else:
						return (0,"MAC address format incorrect:" + mac)
				else:
					return (0,"IP address format incorrect:" + ip)
		else:
			return (0,"This device name is taken (for the HUB itself)")

	def get_device(self, name):
		if len(self.devices) > 0 and name != None and name != "":
			if name.lower() in self.devices:
				return self.devices[name]
		return None

	def register_device(self, *args):
		if len(args) > 3:
			name = str(args[1]).lower()
			ip = str(args[2])
			mac = clean_mac(str(args[3]))

			return self.add_update_device(name, ip, mac)
		else:
			return (0,"Missing Arguments")

	def unregister_device(self, *args):
		if len(args) == 2:
			name = args[1].lower()

			if name != device_hub:
				if name in self.devices:
					self.try_send_cmd(args[0], name, "unregister")
					self.devices.pop(name, None)
					return (1,"Un-registered " + name)
				else:
					return (0,"Device " + name + " could not be found")
			else:
				return (0,"Cannot unregister the HUB")
		else:
			return (0,"Missing Arguments")


	def try_send_cmd(self, auth, name, cmd):
		if name == device_hub:
			return hub_client.cmd_handle(cmd)
		else:
			device = self.get_device(name)
			if device != None:
				ip = device.get_ip()
				return send_cmd(cmd, ip, PORT, auth)
			return (0,"Device " + name + " could not be found")
	### END COMMAND FUNCTIONS ###
