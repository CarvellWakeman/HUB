import java.io.IOException;
import java.util.ArrayList;

public class DeviceControl extends Module {

    // Private members

    public DeviceControl(final HubDevice device){
        super("Device Control");

        // Status command
        Command status = new Command("status", Utils.CLEARANCE.BASIC){
            @Override public String Run(ArrayList<String> arguments){
                return Utils.DEVICE_ONLINE;
            }
        };

        // Shutdown command
        Command shutdown = new Command("shutdown", Utils.CLEARANCE.FULL){
            @Override public String Run(ArrayList<String> arguments){
                String validArgs = ValidateArguments(arguments);
                if (validArgs != null){ return validArgs; }
                String deviceName = GetValidArgument(arguments, 0);

                // OS switch
                switch (device.GetOS()){
                    case WIN:
                        Utils.ExecuteBackgroundTask(new Runnable() {
                            @Override public void run() {
                                try { Runtime.getRuntime().exec("shutdown"); }
                                catch (IOException ex){}
                            }
                        }, 10000);
                        break;
                    case UNIX:
                        Utils.ExecuteBackgroundTask(new Runnable() {
                            @Override public void run() {
                                try { Runtime.getRuntime().exec("sudo shutdown"); }
                                catch (IOException ex){}
                            }
                        }, 10000);
                        break;
                }
                return String.format(Utils.DEVICE_SHUTDOWN, deviceName);
            }
        };

        // Restart command
        Command restart = new Command("restart", Utils.CLEARANCE.FULL){
            @Override public String Run(ArrayList<String> arguments){
                String validArgs = ValidateArguments(arguments);
                if (validArgs != null){ return validArgs; }
                String deviceName = GetValidArgument(arguments, 0);

                // OS switch
                switch (device.GetOS()){
                    case WIN:
                        Utils.ExecuteBackgroundTask(new Runnable() {
                            @Override public void run() {
                                try { Runtime.getRuntime().exec("shutdown /r"); }
                                catch (IOException ex){}
                            }
                        }, 10000);
                        break;
                    case UNIX:
                        Utils.ExecuteBackgroundTask(new Runnable() {
                            @Override public void run() {
                                try { Runtime.getRuntime().exec("sudo reboot"); }
                                catch (IOException ex){}
                            }
                        }, 10000);
                        break;
                }
                return String.format(Utils.DEVICE_SHUTDOWN, deviceName);
            }
        };

        // Hibernate command
        Command hibernate = new Command("hibernate", Utils.CLEARANCE.FULL){
            @Override public String Run(ArrayList<String> arguments){
                String validArgs = ValidateArguments(arguments);
                if (validArgs != null){ return validArgs; }
                String deviceName = GetValidArgument(arguments, 0);

                // OS switch
                switch (device.GetOS()){
                    case WIN:
                        Utils.ExecuteBackgroundTask(new Runnable() {
                            @Override public void run() {
                                try { Runtime.getRuntime().exec("shutdown /h"); }
                                catch (IOException ex){}
                            }
                        }, 10000);

                        return String.format(Utils.DEVICE_HIBERNATING, deviceName);

                    case UNIX:
                        return Utils.ERR_CMD_OS_NOTSUPPORTED;
                }
                return Utils.ERR_CMD_OS_NOTSUPPORTED;
            }
        };

        // Log off command
        Command logoff = new Command("logoff", Utils.CLEARANCE.FULL){
            @Override public String Run(ArrayList<String> arguments){
                String validArgs = ValidateArguments(arguments);
                if (validArgs != null){ return validArgs; }
                String deviceName = GetValidArgument(arguments, 0);

                // OS switch
                switch (device.GetOS()){
                    case WIN:
                        Utils.ExecuteBackgroundTask(new Runnable() {
                            @Override public void run() {
                                try { Runtime.getRuntime().exec("shutdown /l"); }
                                catch (IOException ex){}
                            }
                        }, 10000);
                        break;
                    case UNIX:
                        return Utils.ERR_CMD_OS_NOTSUPPORTED;
                }
                return String.format(Utils.DEVICE_SHUTDOWN, deviceName);
            }
        };



        // Add commands
        AddCommand(status);
        AddCommand(shutdown);
        AddCommand(restart);
        AddCommand(hibernate);
        AddCommand(logoff);
    }


    // Device control
    /*

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

     */

}
