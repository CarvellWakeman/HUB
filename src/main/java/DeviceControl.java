import java.io.IOException;
import java.util.ArrayList;

public class DeviceControl extends Module {

    // Private members

    public DeviceControl(final HubDevice device){
        super("Device Control");

        // Status command
        Command status = new Command("status", Utils.CLEARANCE.BASIC){
            @Override public String Run(String username, String password, ArrayList<String> arguments){
                return Utils.DEVICE_ONLINE;
            }
        };

        // Shutdown command
        Command shutdown = new Command("shutdown", Utils.CLEARANCE.FULL){
            @Override public String Run(String username, String password, ArrayList<String> arguments){
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
            @Override public String Run(String username, String password, ArrayList<String> arguments){
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
                return String.format(Utils.DEVICE_RESTART, deviceName);
            }
        };

        // Hibernate command
        Command hibernate = new Command("hibernate", Utils.CLEARANCE.FULL){
            @Override public String Run(String username, String password, ArrayList<String> arguments){
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
            @Override public String Run(String username, String password, ArrayList<String> arguments){
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
}
