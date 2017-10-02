
import com.mashape.unirest.http.HttpResponse;
import org.apache.commons.codec.binary.Base64;
import org.json.JSONArray;
import org.json.JSONObject;
import spark.Request;
import spark.Response;
import spark.Route;
import spark.Spark;

import java.io.*;
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
        if (args.length < 5 || args.length > 6){
            System.out.printf("USAGE: java -jar %s.jar SERVER_IP SERVER_PORT CLIENT_PORT USERNAME PASSWORD\n", HubDevice.class.getName());
            System.exit(1);
        } else {
            // Startup
            if (args[args.length-1].equals("startup")) {
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
        String USERNAME = args[3];
        String PASSWORD = args[4];

        new HubDevice(Utils.CLIENT_LOG, SERVER_IP, SERVER_PORT, CLIENT_PORT, USERNAME, PASSWORD);
    }




    // Device Info
    private String mLogFile;
    private String mDeviceName = Utils.DEVICE_UNKNOWN;
    private String mDeviceIP = Utils.NETWORK_UNKNOWN_IP;
    private int mDevicePort = Utils.DEFAULT_PORT;
    private String mDeviceMAC = Utils.NETWORK_UNKNOWN_MAC;
    private Utils.OS_TYPE mDeviceOS;

    // Authentication
    private Map<String, Auth> users;

    // Modules
    ArrayList<Module> mModules;


    // General hub device constructor
    public HubDevice(String HUBType, String LogFile){
        // Initialize modules list
        mModules = new ArrayList<>();

        // Set the local log file
        SetLogFile(LogFile);

        // Load tokens from auth file
        users = new HashMap<>();

        try {
            // Read auth file
            InputStream is = new FileInputStream("auth.json");
            BufferedReader buf = new BufferedReader(new InputStreamReader(is));

            String line = buf.readLine();
            StringBuilder sb = new StringBuilder();

            while (line != null){
                sb.append(line).append("\n");
                line = buf.readLine();
            }

            // Decode JSON
            JSONObject base = new JSONObject(sb.toString());
            JSONArray clearanceLevels = base.getJSONArray("auth");
            for (int i = 0; i < clearanceLevels.length(); i++){
                JSONObject auth = clearanceLevels.getJSONObject(i);
                String clearance = auth.get("clearance").toString();
                JSONArray userList = auth.getJSONArray("users");
                for (int j = 0; j < userList.length(); j++){
                    JSONObject user = userList.getJSONObject(j);
                    users.put(user.get("username").toString(),
                            new Auth(user.get("username").toString(), user.get("password").toString(), Utils.CLEARANCE.valueOf(clearance)));
                }
            }

        }
        catch (Exception ex){
            Utils.logMsg(new String[]{Utils.ERROR, "could not retrieve users list: " + ex.getMessage()}, true, GetLogFile());
        }

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
    public HubDevice(String LogFile, String SERVER_IP, int SERVER_PORT, int CLIENT_PORT, String USERNAME, String PASSWORD){
        this(Utils.CLIENT_TITLE, LogFile);

        // Set client port
        SetPort(CLIENT_PORT);

        // Listen for commands from HUB
        Listen(CLIENT_PORT);

        // Connect to HubServer for registration
        Utils.logMsg(new String[]{Utils.CONTACTING_HUB}, true, null);
        Register(SERVER_IP, SERVER_PORT, USERNAME, PASSWORD, 10000, false);
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
    protected boolean isAuthValid(String username, String password){
        Auth auth = users.get(username);
        if (auth != null && auth.username.equals(username)){
            return auth.password.equals(password);
        }
        return false;
    }
    protected Utils.CLEARANCE getAuthorization(String username, String password){
        Auth auth = users.get(username);
        if (auth != null && auth.username.equals(username) && auth.password.equals(password)){
            return auth.clearance;
        }
        return Utils.CLEARANCE.NONE;
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
        Spark.options("/", new Route() {
            @Override public Object handle(Request request, Response response) throws Exception {
                response.header("Access-Control-Allow-Origin", "*");
                response.header("Access-Control-Allow-Headers", "Authorization");
                response.type("text/xml");
                return "Connection Established";
            }
        });
    }

    // Registration with the HUB
    protected void Register(final String HUBIP, final int HUBPort, final String username, final String password, final int retryDelay, boolean connected){
        // Check if device is registered
        HttpResponse isRegistered = Utils.SendCommand("isregistered", new String[]{GetName()}, HUBIP, HUBPort, username, password);

        if (isRegistered == null){
            if (connected) {
                // Connection lost
                Utils.logMsg(new String[]{Utils.CONNECTION_LOST, Utils.CONNECTION_RETRY, String.valueOf(retryDelay / 1000), "seconds." }, true, GetLogFile());
            } else {
                // Connection failed
                Utils.logMsg(new String[]{ Utils.CONNECTION_RETRY, String.valueOf(retryDelay / 1000), "seconds." }, true, null);
            }
            // Try again
            Utils.ExecuteBackgroundTask(new Runnable() { @Override public void run() { Register(HUBIP, HUBPort, username, password, retryDelay, false); } }, retryDelay);
        } else {
            if (isRegistered.getBody().toString().toLowerCase().equals("")){
                // Try to register
                HttpResponse registerResp = Utils.SendCommand("register", new String[]{GetName(), GetIP(), String.valueOf(GetPort()), GetMAC(), username, password}, HUBIP, HUBPort, username, password);
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
            Utils.ExecuteBackgroundTask(new Runnable() { @Override public void run() { Register(HUBIP, HUBPort, username, password, retryDelay, true); } }, retryDelay);
        }

    }


    // MODULES & COMMANDS //
    protected void LoadModules(){
        // Add modules
        mModules.add(new DeviceControl(HubDevice.this));
    }

    protected String CommandReceive(Request request, Response response){
        // Build header
        response.header("Access-Control-Allow-Origin", "*");
        response.header("Access-Control-Allow-Headers", "Authorization");
        response.type("text/xml");

        // Get request variables
        String command = request.queryParams("cmd");
        ArrayList<String> arguments = new ArrayList<>();
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

        // Authorization
        String username = request.queryParams("user");
        String password = request.queryParams("pass");
        if (username.equals("") | password.equals("")) {
            String authHeader = new String(Base64.decodeBase64(request.headers("Authorization")));
            //System.out.println("AuthHeader:" + request.headers("Authorization"));
            if (authHeader.equals("")) {
                response.status(401);
                return Utils.AUTH_FAIL;
            }
            String[] credentials = authHeader.split(":");
            username = credentials[0];
            password = credentials[1];
        }
        boolean authIsValid = isAuthValid(username, password);
        Utils.CLEARANCE userClearance = getAuthorization(username, password);

        String handle;
        if (authIsValid){
            response.status(200);
            handle = CommandHandle(command, arguments, userClearance);
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
                    "from " + (authIsValid ? "valid" : "invalid") + " user '" + username + ":" + password + "'",
                    "(" + ip + ":" + String.valueOf(port) + ")",
                    "Responding '" + handle + "';",
            },
            true, GetLogFile());
        }

        return handle;
    }

    // Command handling
    protected String CommandHandle(String command, ArrayList<String> arguments, Utils.CLEARANCE clearance){
        // Find appropriate command
        for (Module m : mModules){
            Command c = m.GetCommand(command);

            // Command found
            if (c != null){

                // Check authorization level of command
                if (clearance.ordinal() >= c.GetClearance().ordinal()){
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
