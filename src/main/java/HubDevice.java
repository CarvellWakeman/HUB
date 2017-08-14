
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;
import com.mashape.unirest.http.exceptions.UnirestException;
import org.apache.http.auth.AUTH;
import org.json.JSONArray;
import org.json.JSONML;
import spark.Request;
import spark.Response;
import spark.Route;
import spark.Spark;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.net.SocketException;
import java.net.UnknownHostException;
import java.util.*;


public class HubDevice
{
    // Run from cmd line
    public static void main(String[] args) {

        // Process command line arguments
        if (args.length < 4 || args.length > 5){
            System.out.printf("USAGE: java -jar %s.jar SERVER_IP SERVER_PORT CLIENT_PORT AUTH_TOKEN\n", HubDevice.class.getName());
            System.exit(1);
        } else {
            // Startup
            if (args.length == 5 && args[args.length-1].equals("startup")) {
                try {
                    Utils.CreateStartupScript(GetMachineOS(), HubDevice.class.getName(), Arrays.copyOfRange(args, 0, args.length - 1));
                } catch (Exception ex) {
                    System.out.println(ex.getMessage());
                }
            }
        }


        // Start hub device
        String SERVER_IP = args[0];
        int SERVER_PORT = Integer.valueOf(args[1]);
        int CLIENT_PORT = Integer.valueOf(args[2]);
        String AUTH_KEY = args[3];

        new HubDevice(Utils.CLIENT_LOG, SERVER_IP, SERVER_PORT, CLIENT_PORT, AUTH_KEY);

        // Shutdown unirest
        //try { Unirest.shutdown(); }
        //catch (IOException ex){ System.exit(1); }
    }




    // Device Info
    private String mLogFile;
    private String mDeviceName = Utils.DEVICE_UNKNOWN;
    private String mDeviceIP = Utils.NETWORK_UNKNOWN_IP;
    private int mDevicePort = Utils.DEFAULT_PORT;
    private String mDeviceMAC = Utils.NETWORK_UNKNOWN_MAC;
    private Utils.OS_TYPE mDeviceOS;

    // Authorized tokens
    private Map<String, Utils.CLEARANCE> tokens;

    // Modules
    ArrayList<Module> mModules;



    // General hub device constructor
    public HubDevice(String HUBType, String LogFile){
        // Initialize modules list
        mModules = new ArrayList<>();

        // Set the local log file
        SetLogFile(LogFile);

        // Load tokens from file TODO:Implement
        tokens = new HashMap<>();
        tokens.put("2177", Utils.CLEARANCE.BASIC); //picard
        tokens.put("5990", Utils.CLEARANCE.FULL); //startrekDS9
        tokens.put("3828", Utils.CLEARANCE.FULL); //brobeans

        // Device info
        try {
            SetOS(GetMachineOS());
            SetName(GetMachineName(GetOS()));
            SetIP(GetMachineIP());
            SetMAC(GetMachineMAC());
        } catch (UnknownHostException ex){
            System.out.printf("Device IP or MAC address could not be found:%s\n", ex.getMessage());
        }

        // Header
        Utils.printHeader(HUBType, GetName(), GetIP(), GetMAC());

        // Loading
        Utils.logMsg(new String[]{Utils.LOADING}, true, GetLogFile());

        // Load modules
        LoadModules();
        Utils.logMsg(new String[]{Utils.MODULE_LOAD_COMPLETE}, true, GetLogFile());

    }
    // Hub client constructor
    public HubDevice(String LogFile, String SERVER_IP, int SERVER_PORT, int CLIENT_PORT, String AUTH_KEY){
        this(Utils.CLIENT_TITLE, LogFile);

        // Set client port
        SetPort(CLIENT_PORT);

        // Listen for commands from HUB
        Listen(CLIENT_PORT);

        // Connect to HubServer for registration
        Utils.logMsg(new String[]{Utils.CONTACTING_HUB}, true, null);
        Register(SERVER_IP, SERVER_PORT, Utils.bhash(AUTH_KEY), 10000, false);
    }


    // SYSTEM INFO //
    Utils.OS_TYPE GetOS() { return mDeviceOS; }
    String GetName() { return mDeviceName; }
    String GetIP() { return mDeviceIP; }
    int GetPort() { return mDevicePort; }
    String GetMAC() { return mDeviceMAC; }
    String GetLogFile() { return mLogFile; }

    private void SetOS(Utils.OS_TYPE os) { mDeviceOS = os; }
    private void SetName(String name) { mDeviceName = name; }
    private void SetIP(String ip) { mDeviceIP = ip; }
    private void SetPort(int port) { mDevicePort = port; }
    private void SetMAC(String mac) { mDeviceMAC = mac; }
    private void SetLogFile(String logfile) { mLogFile = logfile; }


    // AUTHORIZATION //
    protected boolean tokenIsValid(String token){
        return tokens.containsKey(token);
    }
    protected Utils.CLEARANCE tokenClearance(String token){
        return (tokenIsValid(token) ? tokens.get(token) : Utils.CLEARANCE.NONE);
    }


    // NETWORK //
    protected void Listen(int PORT){
        // Start listening
        Spark.port(PORT);
        Spark.get("/", new Route() {
            @Override public Object handle(Request request, Response response) throws Exception {
                return CommandReceive(request, response);
            }
        });
        Spark.post("/", new Route() {
            @Override public Object handle(Request request, Response response) throws Exception {
                return CommandReceive(request, response);
            }
        });
    }

    // Registration with the HUB
    protected void Register(final String HUBIP, final int HUBPort, final String authToken, final int retryDelay, boolean connected){
        // Check if device is registered
        HttpResponse isRegistered = Utils.SendCommand("isregistered", new String[]{GetName()}, HUBIP, HUBPort, authToken);

        if (isRegistered == null){
            if (connected) {
                // Connection lost
                Utils.logMsg(new String[]{Utils.CONNECTION_LOST, Utils.CONNECTION_RETRY, String.valueOf(retryDelay / 1000), "seconds." }, true, GetLogFile());
            } else {
                // Connection failed
                Utils.logMsg(new String[]{"Herp", Utils.CONNECTION_RETRY, String.valueOf(retryDelay / 1000), "seconds." }, true, null);
            }
            // Try again
            Utils.ExecuteBackgroundTask(new Runnable() { @Override public void run() { Register(HUBIP, HUBPort, authToken, retryDelay, false); } }, retryDelay);
        } else {
            if (isRegistered.getBody().toString().toLowerCase().equals("")){
                // Try to register
                HttpResponse registerResp = Utils.SendCommand("register", new String[]{GetName(), GetIP(), String.valueOf(GetPort()), GetMAC(), String.valueOf(authToken)}, HUBIP, HUBPort, authToken);
                if (registerResp == null){
                    Utils.logMsg(new String[]{Utils.CONNECTION_FAILED, Utils.CONNECTION_RETRY, String.valueOf(retryDelay / 1000), "seconds." }, true, null);
                } else {
                    // Success
                    Utils.logMsg(Utils.CONNECTION_READY, true, GetLogFile());
                }
            } else {
                if (!connected) {
                    Utils.logMsg(Utils.CONNECTION_READY, true, GetLogFile());
                }
            }

            // Try again
            Utils.ExecuteBackgroundTask(new Runnable() { @Override public void run() { Register(HUBIP, HUBPort, authToken, retryDelay, true); } }, retryDelay);
        }

    }


    // MODULES & COMMANDS //
    protected void LoadModules(){
        // Add modules
        mModules.add(new DeviceControl(HubDevice.this));
    }

    protected String CommandReceive(Request request, Response response){
        // Get request variables
        String command = request.queryParams("cmd");
        ArrayList<String> arguments = new ArrayList<>();
        String authToken = request.queryParams("auth");
        boolean authTokenIsValid = tokenIsValid(authToken);
        String ip = request.ip();
        int port = request.port();


        // Load arguments
        String jargs = request.queryParams("args");
        if (jargs != null){
            JSONArray ja = new JSONArray(request.queryParams("args"));
            for (int i = 0; i < ja.length(); i++){
                if (ja.getString(i).length() > 0){ arguments.add(ja.getString(i)); }
            }
        }


        // Build header
        response.header("Access-Control-Allow-Origin", "*");
        response.type("text/xml");


        // Check authorization token and Process command
        String handle;
        if (authTokenIsValid){
            response.status(200);
            handle = CommandHandle(command, arguments, authToken);
        } else {
            response.status(401);
            handle = Utils.AUTH_FAIL;
        }


        // Log command received (only if it's not hidden)
        Command cmdClr = null;
        for (Module m : mModules){
            for (Command c : m.mCommands){
                if (c.GetName().equals(command)){ cmdClr = c; }
            }
        }
        if (cmdClr == null || cmdClr.GetClearance() != Utils.CLEARANCE.HIDDEN) {
            Utils.logMsg(new String[]{
                            Utils.CMD_RECV, "'" + command + ":" + arguments.toString() + "'",
                            "from", ip, "on port " + String.valueOf(port),
                            "with " + (authTokenIsValid ? "VALID" : "INVALID"),
                            "auth '" + authToken + "'.",
                            "Responding '" + handle + "';",
                    },
                    true, GetLogFile());
        }

        return handle;
    }

    // Command handling
    protected String CommandHandle(String command, ArrayList<String> arguments, String authToken){
        // Find appropriate command
        for (Module m : mModules){
            Command c = m.GetCommand(command);

            // Command found
            if (c != null){

                // Check authorization level of command
                if (tokenClearance(authToken).ordinal() >= c.GetClearance().ordinal()){
                    return c.Run(arguments);
                } else { // Not authorized
                    String notAuth = Utils.CMD_NOTAUTH + " '" + command + "'";
                    Utils.logMsg(notAuth, true, GetLogFile());
                    return notAuth;
                }
            }
        }

        // Command not found
        return Utils.CMD + " '" + command + "' " + Utils.CMD_NOTFOUND;
    }


    // DEVICE INFO //
    public static Utils.OS_TYPE GetMachineOS() {
        String OS = System.getProperty("os.name").toLowerCase();
        if (OS.contains("windows")){ return Utils.OS_TYPE.WIN; }
        if (OS.contains("mac os x") || OS.contains("linux")){ return Utils.OS_TYPE.UNIX; }
        return Utils.OS_TYPE.UNSUPPORTED;
    }
    public static String GetMachineName(Utils.OS_TYPE OS) {
        Map<String, String> env = System.getenv();

        // Windows machine name
        if (OS == Utils.OS_TYPE.WIN){
            if (env.containsKey("COMPUTERNAME")){ return env.get("COMPUTERNAME"); }
        } else if (OS == Utils.OS_TYPE.UNIX){
            if (env.containsKey("HOSTNAME")){ return env.get("HOSTNAME"); }
        }

        // Could not find OS specific device name, resort to network name
        try {
            return InetAddress.getLocalHost().getHostName();
        } catch (UnknownHostException ex) {
            return Utils.DEVICE_UNKNOWN;
        }
    }

    public static String GetMachineIP() throws UnknownHostException{
        try {

            // Look through the rest of the interfaces
            ArrayList<String> addressCandidates = new ArrayList<>();
            Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();
            while (interfaces.hasMoreElements()){
                NetworkInterface ni = interfaces.nextElement();

                // Ignore loopbacks and check if interfaces has any addresses
                if (ni.isLoopback() || !ni.getInetAddresses().hasMoreElements()) continue;

                // Loop through addresses
                Enumeration<InetAddress> addresses = ni.getInetAddresses();
                while(addresses.hasMoreElements()) {
                    InetAddress ia = addresses.nextElement();
                    String addr = ia.getHostAddress();

                    // Validate (###.###.###.###)
                    if (addr.split("\\.").length == 4 && !addr.equals(Utils.NETWORK_LOCALHOST)) {
                        addressCandidates.add(ni.getName() + "|" + addr);
                    }
                }
            }

            // Look through candidates for best match
            Collections.sort(addressCandidates, new Comparator<String>() {
                @Override public int compare(String o1, String o2) {
                    return o1.split("|")[0].compareTo(o2.split("|")[0]);
                }
            });
            if (addressCandidates.size() > 0) {
                String addr = addressCandidates.get(0);
                return addr.substring(addr.indexOf("|")+1, addr.length());
            }

            throw new UnknownHostException("Either no suitable adapter was found or there was a network error.");
        } catch (SocketException ex) {
            throw new UnknownHostException("Either no suitable adapter was found or there was a network error.");
        }
    }

    public static String GetMachineMAC() throws UnknownHostException{
        try {
            ArrayList<String> macCandidates = new ArrayList<>();
            Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();
            while (interfaces.hasMoreElements()){
                NetworkInterface ni = interfaces.nextElement();

                // Ignore loopbacks and check if adapter has any addresses
                if (ni.isLoopback() || !ni.getInetAddresses().hasMoreElements()) continue;

                // Format address
                byte[] addr = ni.getHardwareAddress();
                StringBuilder sb = new StringBuilder();
                for (int i = 0; i < addr.length; i++) {
                    sb.append(String.format("%02X%s", addr[i], (i < addr.length - 1) ? ":" : ""));
                }

                // Validate
                if (sb.toString().split(":").length == 6) {
                    macCandidates.add(ni.getName() + "|" + sb.toString());
                }
            }

            // Look through candidates for best match
            Collections.sort(macCandidates, new Comparator<String>() {
                @Override public int compare(String o1, String o2) {
                    return o1.split("|")[0].compareTo(o2.split("|")[0]);
                }
            });
            if (macCandidates.size() > 0) {
                String mac = macCandidates.get(0);
                return mac.substring(mac.indexOf("|")+1, mac.length());
            }

            throw new UnknownHostException("MACHINE address could not be determined");
        } catch (SocketException ex) {
            throw new UnknownHostException("MACHINE address could not be determined");
        }
    }

}
