import spark.Request;
import spark.Response;

import java.util.ArrayList;
import java.util.Arrays;

public class HubServer extends HubDevice
{
    // Run from cmd line
    public static void main(String[] args) {

        // Process command line arguments
        if (args.length < 1 || args.length > 2){
            System.out.printf("USAGE: java -jar %s.jar SERVER_PORT\n", HubServer.class.getName());
            System.exit(1);
        } else {
            // Startup
            if (args.length == 2 && args[args.length-1].equals("startup")) {
                try {
                    Utils.CreateStartupScript(GetMachineOS(), HubServer.class.getName(), Arrays.copyOfRange(args, 0, args.length - 1));
                } catch (Exception ex) {
                    System.out.println(ex.getMessage());
                }
            }
        }

        // Start hub server
        int PORT = Integer.valueOf(args[0]);
        new HubServer(PORT);
    }


    // Device management module
    DeviceManagement deviceManagement;

    // Device control module (separate from normal modules because these commands are not exposed to the outside world)
    DeviceControl deviceControl;

    // Constructor
    public HubServer(int PORT){
        super(Utils.SERVER_TITLE, Utils.SERVER_LOG);

        // Register HUB to itself
        deviceManagement.RegisterDevice(Utils.SERVER_NAME, GetIP(), PORT, GetMAC());

        // Listen for commands from Devices
        Listen(PORT);
    }


    // HubServer machine name is 'HUB'
    @Override
    public String GetName(){ return Utils.SERVER_NAME; }

    @Override
    protected void LoadModules() {
        // Server unique modules
        deviceManagement = new DeviceManagement();
        deviceControl = new DeviceControl(HubServer.this);

        mModules.add(deviceManagement);
        mModules.add(new HubInfo(HubServer.this));
    }


    // Process commands differently
    @Override
    protected String CommandHandle(String username, String password, String command, ArrayList<String> arguments, Utils.CLEARANCE clearance){
        Command c = null;

        // If arguments contain HUB name, check device control
        if (arguments.size() != 0 && (arguments.contains(Utils.SERVER_NAME) || arguments.contains(Utils.SERVER_NAME.toLowerCase()))) {
            c = deviceControl.GetCommand(command);
        }

        // Search all modules
        if (c == null) {
            return super.CommandHandle(username, password, command, arguments, clearance);
        } else {
            // Check authorization level of command
            if (clearance.ordinal() >= c.GetClearance().ordinal()){
                return c.Run(username, password, arguments);
            } else { // Not authorized
                String notAuth = Utils.CMD_NOTAUTH + " '" + command + "'";
                Utils.logMsg(notAuth, true, GetLogFile());
                return notAuth;
            }
        }
    }

    /*
    @Override
    public String CommandReceive(Request request, Response response){
        // Get request variables
        String command = request.queryParams("cmd");
        ArrayList<String> arguments = new ArrayList<>();
        String deviceName = Utils.DEVICE_UNKNOWN;
        String authToken = request.queryParams("auth");
        boolean authTokenIsValid = tokenIsValid(authToken);
        String ip = request.ip();
        int port = request.port();

        // Load arguments
        if (request.queryParamsValues("args") != null){
            arguments.addAll(Arrays.asList(request.queryParamsValues("args")));
            deviceName = arguments.get(0);
            arguments.remove(0);
        }

        // Log command received
        Utils.logMsg(new String[]{
                Utils.CMD_RECV,
                "'" + command + ":" + arguments.toString() + "'",
                "from", ip, "on port " + String.valueOf(port),
                "with auth '" + authToken + "'",
                (authTokenIsValid?"(VALID)":"(INVALID)")},
            true, GetLogFile());

        // Build header
        response.header("Access-Control-Allow-Origin", "*");
        response.type("text/xml");

        // Check authorization token
        if (!authTokenIsValid) {
            response.status(401);
            return Utils.AUTH_FAIL;
        }

        // Check arguments
        if (arguments.size() >= 1 && !deviceName.equals("") && !command.equals("")) {
            // Process command
            response.status(200);
            return CommandHandle(command, arguments, authToken);
        }

        return Utils.CMD_INVALID;
    }
    */

}
