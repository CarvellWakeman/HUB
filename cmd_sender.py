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

PORT = "5000"
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

if len(sys.argv) > 2:
	print("args:", str(sys.argv))
	data["auth"] = sys.argv[1]
	data["command"] = " ".join(sys.argv[2:])
	send(data)
else:
	HOST = input("HUB IP <- ")
	auth = input("AUTHORIZATION <- ")
	while 1:
		try:
			#Send command to hub
			data["auth"] = auth
			data["command"] = input("HUB <- ")
			send(data)
		except Exception as e:
			print ("Coult not reach HUB")




