#Imports
#import socket
#import sys

#Static vars
#HOST = socket.gethostname()#'127.0.0.1'
#PORT = 10000

#Attempt connection
#try:
	#s = socket.socket()
	#s.connect((HOST, PORT))

	#if len(sys.argv) > 1:
		#print "args:", str(sys.argv)
		#s.send(" ".join(sys.argv[1:]))
	#else:
		#while 1:
			#msg = raw_input("Command to Send: ")

		    #Send command to hub
		   	#s.send(msg)

			#Close if close message
			#if msg == "close":
				#s.close()
				#sys.exit(0)


#except Exception:
	#print "Connection could not be established."





import requests
import sys

HOST = "192.168.1.72" # Set destination URL here
PORT = "5001"
data = {}     # Set POST fields here




def send(cmddict):
	#Request
	#params = urllib.urlencode(data)
	#headers = {"Content-type": "application/x-www-form-urlencoded"}
	#httpServ = http.client.HTTPConnection(HOST + ":" + PORT)
	#httpServ.request("POST", "", params, headers)

	#Response
	#response = httpServ.getresponse()
	#print("    -> " + response.read())

	#httpServ.close()


	r = requests.post("http://"+ HOST + ":" + PORT, data=cmddict, timeout=5)
	print("    -> " + r.text)

if len(sys.argv) > 1:
	print("args:", str(sys.argv))
	data["command"] = " ".join(sys.argv[1:])
	send(data)
else:
	while 1:
		#Send command to hub
		data["command"] = input("HUB <- ")
		send(data)




