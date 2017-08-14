import com.mashape.unirest.http.HttpResponse;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.util.ArrayList;
import java.util.Arrays;

public class DeviceManagement extends Module {

    // Private members
    private ArrayList<Device> mDevices;

    public DeviceManagement(){
        super("Device Management");

        mDevices = new ArrayList<>();

        // Is Registered command
        Command isregistered = new Command("isregistered", Utils.CLEARANCE.HIDDEN){
            @Override
            public String Run(ArrayList<String> arguments){
                String validArgs = ValidateArguments(arguments);
                if (validArgs != null){ return validArgs; }

                String deviceName = GetValidArgument(arguments, 0);
                Device d = GetDevice(deviceName);

                if (d == null){
                    return "";
                } else {
                    return d.name;
                }
            }
        };
        isregistered.AddArg("device", false);

        // Register command
        Command register = new Command("register", Utils.CLEARANCE.BASIC){
            @Override
            public String Run(ArrayList<String> arguments){
                String validArgs = ValidateArguments(arguments);
                if (validArgs != null){ return validArgs; }

                String deviceName = GetValidArgument(arguments, 0);
                Device d = GetDevice(deviceName);

                // Register (or update) new device
                RegisterDevice(deviceName, GetValidArgument(arguments, 1), Integer.valueOf(GetValidArgument(arguments, 2)), GetValidArgument(arguments, 3), GetValidArgument(arguments, 4));

                if (d == null){
                    return String.format(Utils.DEVICE_REGISTERED, deviceName);
                } else {
                    return String.format(Utils.DEVICE_ALREADY_REGISTERED, deviceName);
                }
            }
        };
        register.AddArg("device", false);
        register.AddArg("ip", false);
        register.AddArg("port", false);
        register.AddArg("mac", false);
        register.AddArg("authToken", false);
        register.SetDesc("Register device as a client to the HUB");


        // UnRegister command
        Command unregister = new Command("unregister", Utils.CLEARANCE.BASIC){
            @Override
            public String Run(ArrayList<String> arguments){
                String validArgs = ValidateArguments(arguments);
                if (validArgs != null){ return validArgs; }

                String deviceName = GetValidArgument(arguments, 0);
                Device d = GetDevice(deviceName);

                // Unregister existing device
                if (d != null){
                    UnRegisterDevice(d);
                    return String.format(Utils.DEVICE_UNREGISTERED, deviceName);
                } else {
                    return String.format(Utils.DEVICE_NOTFOUND, deviceName);
                }
            }
        };
        unregister.AddArg("device", false);
        unregister.SetDesc("Un-register device from the HUB");

        // Status command
        Command status = new Command("status", Utils.CLEARANCE.FULL){
            @Override
            public String Run(ArrayList<String> arguments){
                String validArgs = ValidateArguments(arguments);
                if (validArgs != null){ return validArgs; }

                String deviceName = GetValidArgument(arguments, 0);
                Device d = GetDevice(deviceName);

                if (d != null){
                    // Online or offline
                    String deviceResp = SendDeviceCommand(GetName(), d);
                    if (!deviceResp.equals(Utils.DEVICE_ONLINE)){
                        return Utils.DEVICE_OFFLINE;
                    }
                    return deviceResp;
                } else {
                    return String.format(Utils.DEVICE_NOTFOUND, deviceName);
                }
            }
        };
        status.AddArg("device", false);
        status.SetDesc("Get network status of LAN device");

        // Devices command
        Command devices = new Command("devices", Utils.CLEARANCE.FULL){
            @Override
            public String Run(ArrayList<String> arguments){
                StringBuilder sb = new StringBuilder();
                sb.append("NAME       IP              MAC                 STATUS\n");
                for (Device d : mDevices){
                    String s = "";

                    // HUB shortcut
                    if (d.name.equals(Utils.SERVER_NAME)){
                        s = Utils.DEVICE_ONLINE;
                    } else {
                        if (GetCommand("status") != null) {
                            s = GetCommand("status").Run(new ArrayList<>(Arrays.asList(d.name)));
                        }
                    }

                    String nmTrunc = (d.name.length()>10?d.name.substring(0,10):d.name);
                    int nmOffset = 11-nmTrunc.length();
                    int ipOffset = 16-d.IP.length();
                    int macOffset = 3;
                    sb.append(String.format("%s%s%s%s%s%s%s\n",
                            nmTrunc,
                            String.format("%" + String.valueOf(nmOffset) + "s", " "),
                            d.IP,
                            String.format("%" + String.valueOf(ipOffset) + "s", " "),
                            d.MAC,
                            String.format("%" + String.valueOf(macOffset) + "s", " "),
                            s));
                }

                return sb.toString();
            }
        };
        devices.SetDesc("Get devices registered to the HUB");

        // Shutdown command
        Command shutdown = new Command("shutdown", Utils.CLEARANCE.FULL){
            @Override
            public String Run(ArrayList<String> arguments){
                String validArgs = ValidateArguments(arguments);
                if (validArgs != null){ return validArgs; }

                String deviceName = GetValidArgument(arguments, 0);
                Device d = GetDevice(deviceName);

                if (d != null){
                    return SendDeviceCommand(GetName(), d);
                } else {
                    return String.format(Utils.DEVICE_NOTFOUND, deviceName);
                }
            }
        };
        shutdown.AddArg("device", false);
        shutdown.SetDesc("Shutdown a registered HUB device");

        // Restart command
        Command restart = new Command("restart", Utils.CLEARANCE.FULL){
            @Override
            public String Run(ArrayList<String> arguments){
                String validArgs = ValidateArguments(arguments);
                if (validArgs != null){ return validArgs; }

                String deviceName = GetValidArgument(arguments, 0);
                Device d = GetDevice(deviceName);

                if (d != null){
                    return SendDeviceCommand(GetName(), d);
                } else {
                    return String.format(Utils.DEVICE_NOTFOUND, deviceName);
                }
            }
        };
        restart.AddArg("device", false);
        restart.SetDesc("Restart a registered HUB device");

        // Hibernate command
        Command hibernate = new Command("hibernate", Utils.CLEARANCE.FULL){
            @Override
            public String Run(ArrayList<String> arguments){
                String validArgs = ValidateArguments(arguments);
                if (validArgs != null){ return validArgs; }

                String deviceName = GetValidArgument(arguments, 0);
                Device d = GetDevice(deviceName);

                if (d != null){
                    return SendDeviceCommand(GetName(), d);
                } else {
                    return String.format(Utils.DEVICE_NOTFOUND, deviceName);
                }
            }
        };
        hibernate.AddArg("device", false);
        hibernate.SetDesc("Hibernate a registered HUB device");

        // Log Off command
        Command logoff = new Command("logoff", Utils.CLEARANCE.FULL){
            @Override
            public String Run(ArrayList<String> arguments){
                String validArgs = ValidateArguments(arguments);
                if (validArgs != null){ return validArgs; }

                String deviceName = GetValidArgument(arguments, 0);
                Device d = GetDevice(deviceName);

                if (d != null){
                    return SendDeviceCommand(GetName(), d);
                } else {
                    return String.format(Utils.DEVICE_NOTFOUND, deviceName);
                }
            }
        };
        logoff.AddArg("device", false);
        logoff.SetDesc("Log off a registered HUB device");

        // Wake command
        Command wake = new Command("wake", Utils.CLEARANCE.FULL){
            @Override
            public String Run(ArrayList<String> arguments){
                String validArgs = ValidateArguments(arguments);
                if (validArgs != null){ return validArgs; }

                String deviceName = GetValidArgument(arguments, 0);
                Device d = GetDevice(deviceName);

                if (d != null){
                    try {
                        byte[] macBytes = getMacBytes(d.MAC);
                        byte[] bytes = new byte[6 + 16 * macBytes.length];
                        for (int i = 0; i < 6; i++) { bytes[i] = (byte) 0xff; }
                        for (int i = 6; i < bytes.length; i += macBytes.length) { System.arraycopy(macBytes, 0, bytes, i, macBytes.length); }

                        InetAddress address = InetAddress.getByName(d.IP);
                        DatagramPacket packet = new DatagramPacket(bytes, bytes.length, address, d.PORT);
                        DatagramSocket socket = new DatagramSocket();
                        socket.send(packet);
                        socket.close();

                        return String.format(Utils.DEVICE_WOL, deviceName);
                    } catch (Exception e) {
                        return Utils.ERR_CMD_WOL;
                    }
                } else {
                    return String.format(Utils.DEVICE_NOTFOUND, deviceName);
                }
            }
        };
        wake.AddArg("device", false);
        wake.SetDesc("Wake (wake on lan) a registered HUB device");


        // Add commands
        AddCommand(isregistered);
        AddCommand(register);
        AddCommand(unregister);
        AddCommand(devices);
        AddCommand(status);
        AddCommand(shutdown);
        AddCommand(restart);
        AddCommand(hibernate);
        AddCommand(logoff);
        AddCommand(wake);

    }


    // Device registration
    public Device RegisterDevice(String name, String IP, int PORT, String MAC, String AUTH){
        Device d = GetDevice(name);
        if (d == null){
            d = new Device(name, IP, PORT, MAC, AUTH);
        }

        d.IP = IP;
        d.PORT = PORT;
        d.MAC = MAC;
        d.AUTH = AUTH;
        mDevices.add(d);

        return d;
    }
    public void UnRegisterDevice(Device device){ mDevices.remove(device); }
    public void UnRegisterDevice(String name){ UnRegisterDevice(GetDevice(name)); }

    public Device GetDevice(String name){
        for (Device d : mDevices){
            if (d.name.toLowerCase().equals(name.toLowerCase())){ return d; }
        }
        return null;
    }


    // Pass command along to a device
    public String SendDeviceCommand(String command, Device device) {

        // No such device was found
        if (device == null){
            return String.format(Utils.DEVICE_NOTFOUND, "");
        }

        // Send Command
        HttpResponse<String> resp = Utils.SendCommand(command, new String[]{device.name}, device.IP, device.PORT, device.AUTH);
        if (resp == null){
            return String.format(Utils.DEVICE_COULDNOT_CONTACT, device.name);
        }
        return resp.getBody();
    }

   // Wake on lan helper method (credit: http://www.jibble.org/wake-on-lan/)
   private static byte[] getMacBytes(String macStr) throws IllegalArgumentException {
       byte[] bytes = new byte[6];
       String[] hex = macStr.split("(\\:|\\-)");
       if (hex.length != 6) {
           throw new IllegalArgumentException("Invalid MAC address.");
       }
       try {
           for (int i = 0; i < 6; i++) {
               bytes[i] = (byte) Integer.parseInt(hex[i], 16);
           }
       }
       catch (NumberFormatException e) {
           throw new IllegalArgumentException("Invalid hex digit in MAC address.");
       }
       return bytes;
   }


    // Data holder for remote device
    private class Device{
        protected String name;
        protected String IP;
        protected int PORT;
        protected String MAC;
        protected String AUTH;

        public Device(String name, String IP, int PORT, String MAC, String AUTH) {
            this.name = name;
            this.IP = IP;
            this.PORT = PORT;
            this.MAC = MAC;
            this.AUTH = AUTH;
        }
    }
}
