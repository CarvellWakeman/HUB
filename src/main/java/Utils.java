import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;
import com.mashape.unirest.http.exceptions.UnirestException;
import org.json.JSONArray;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.net.SocketException;
import java.net.UnknownHostException;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.ScheduledThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

public class Utils {

    // Logging
    static String SERVER_LOG = "hub_server_log.txt";
    static String CLIENT_LOG = "hub_client_log.txt";

    // Command
    static String CMD = "Command";
    static String CMD_NOTAUTH = "Not authorized to run the command";
    static String CMD_RECV = "Command received";
    static String CMD_RUN = "Running";
    static String CMD_NOTFOUND = "not Found";
    static String CMD_INVALID = "Command Invalid";
    static String CMD_ARGS_INVALID = "Arguments Invalid";
    static String CMD_EXISTS = " duplicate command";
    static String CMD_ADD = "Add";
    static String CMD_LVL = "level";

    // Module
    static String MODULE = "Module";
    static String MODULE_INIT = "Initialized";
    static String MODULE_OK = "[ OK ]";
    static String MODULE_FAIL = "[FAIL]";
    static String MODULE_LOAD_COMPLETE = "MODULES LOADED";

    // Loading
    static String LOADING = "LOADING";

    // Network
    static String NETWORK_LOCALHOST = "127.0.0.1";
    static String NETWORK_REQ_ERROR = "REQUEST_ERROR";
    static String NETWORK_CONNECTION_TIMEOUT = "TIMEOUT";
    static String NETWORK_CONNECTION_REFUSED = "CONNECTION_REFUSED";
    static String NETWORK_GENERAL_FAILURE = "FAILURE";
    static String NETWORK_UNAUTHORIZED = "UNAUTHORIZED";
    static String NETWORK_UNKNOWN_IP = "UNKNOWN IP";
    static String NETWORK_UNKNOWN_MAC = "UNKNOWN MAC";

    static String AUTH_PASS = "Authentication valid";
    static String AUTH_FAIL = "Authentication invalid";
    static String CONTACTING_HUB = "Contacting HUB to register";
    static String CONNECTION_RETRY = "Retrying connection in";
    static String CONNECTION_LOST = "Connection to HUB lost.";
    static String CONNECTION_RESTORED = "Connection restored.";
    static String CONNECTION_READY = "Connected to HUB. Awaiting commands";
    static String CONNECTION_FAILED = "Registration failed, could not contact HUB.";

    static int DEFAULT_PORT = 5000;

    // Device
    static String SERVER_NAME = "HUB";
    static String SERVER_TITLE = "HUB SERVER";
    static String CLIENT_TITLE = "HUB CLIENT";
    static String DEVICE_UNKNOWN = "Unknown";
    static String DEVICE_NOTFOUND = "Device '%s' Not Found";
    static String DEVICE_COULDNOT_CONTACT = "Could not contact '%s'";
    static String DEVICE_ONLINE = "Online";
    static String DEVICE_OFFLINE = "Offline";
    static String DEVICE_ALREADY_REGISTERED = "Device '%s' already registered";
    static String DEVICE_REGISTERED = "Registered device '%s'";
    static String DEVICE_UNREGISTERED = "Device '%s' unregistered";

    static String DEVICE_SHUTDOWN = "Shutting down %s";
    static String DEVICE_RESTART = "Restarting %s";
    static String DEVICE_HIBERNATING = "Hibernating %s";
    static String DEVICE_LOGOFF = "Logging off %s";
    static String DEVICE_WOL = "Sending magic packet to %s";

    // Error
    static String ERROR = "Error:";
    static String ERR_CMD_OS_NOTSUPPORTED = "Could not run command, OS does not support it";
    static String ERR_CMD_UNKNWN = "Could not run command, unknown cause";
    static String ERR_CMD_WOL = "Could not send wake on lan packet";



    // Supported operating systems
    enum OS_TYPE {
        WIN,
        UNIX,
        UNSUPPORTED
    }


    // Clearance levels
    enum CLEARANCE { // IMPORTANT: MUST BE IN INCREASING ORDER - LOWER LEVELS ARE INHERITED
        HIDDEN,
        NONE,
        BASIC,
        FULL
    }


    // AUTHORIZATION //
    public static String bhash(String key){
        int r = 0;
        for (int i = 0; i < key.length(); i++){
            r += (i+1) * key.charAt(i);
        }
        return String.valueOf(r);
    }


    // PRINTING //
    public static void printMsg(String message){ System.out.println(message); }
    public static void printMsg(String[] messages, String header){
        StringBuilder sb = new StringBuilder();
        for (String msg : messages){
            sb.append(msg + " ");
        }

        if (header.length() > 0){
            System.out.println(header + ":" + sb.toString());
        } else {
            System.out.println(sb.toString());
        }

    }

    public static void logMsg(String message, boolean display, String fileName){ logMsg(new String[]{message}, display, fileName); }
    public static void logMsg(String[] messages, boolean display, String fileName){
        // Assemble message
        StringBuilder sb = new StringBuilder();
        for (String msg : messages){
            sb.append(msg.replace("\n", "\\n") + " "); //Replace newline with literal newline
        }

        // Get timestamp
        String timeStamp = new SimpleDateFormat("[yyyy-MM-dd HH:mm:ss] ").format(new Date());

        // Assemble message
        String msg = timeStamp + sb.toString();

        // Display
        if (display){
            printMsg(msg);
        }

        // Try to write
        if (fileName != null && fileName.length() > 0) {
            FileWriter fw = null;
            BufferedWriter bw = null;
            try {
                File logFile = new File(fileName);

                // Create file if it DNE
                if (!logFile.exists()) {
                    logFile.createNewFile();
                }

                // Write to log
                fw = new FileWriter(logFile.getAbsoluteFile(), true);
                bw = new BufferedWriter(fw);

                // Write
                bw.write(msg + "\n");
            } catch (IOException ex) {
                System.out.println("Error: Could not write to logfile '" + fileName + "'");
            } finally {
                try {
                    if (bw != null) bw.close();
                    if (fw != null) fw.close();
                } catch (IOException ex) {
                    ex.printStackTrace();
                }
            }
        }
    }

    public static void printHeader(String title, String deviceName, String deviceIP, String deviceMAC){
        int numSlashes = 10;

        //Program info
        String m_creator = "Zach Lerew 2016-17";

        // Assemble sub messages
        List<String> rows = Arrays.asList(title, m_creator, "", deviceName, deviceIP, deviceMAC);
        int maxLen = rows.get(0).length();
        for (String s : rows) { if (s.length() > maxLen) { maxLen = s.length(); } }

        // Print top row of slashes
        System.out.printf("%s\n", String.format("%" + String.valueOf(maxLen + numSlashes*2 + 2) + "s", "/").replace(' ', '/'));

        // Pad the messages
        int offset;
        for (String str : rows){
            offset = (int)Math.floor( (maxLen - str.length())/2 ) + 1; //+1 to avoid offset=0
            System.out.printf("%s%s%s%s%s\n",
                    String.format("%" + String.valueOf(numSlashes) + "s", "/").replace(' ', '/'),
                    String.format("%" + String.valueOf(offset) + "s", " "),
                    str,
                    String.format("%" + String.valueOf(offset + (str.length()%2!=0?1:0)) + "s", " "),
                    String.format("%" + String.valueOf(numSlashes) + "s", "/").replace(' ', '/')
            );
        }

        // Print bottom row of slashes
        System.out.printf("%s\n", String.format("%" + String.valueOf(maxLen + numSlashes*2 + 2) + "s", "/").replace(' ', '/'));
    }


    // DEVICE EXECUTION //
    public static void ExecuteBackgroundTask(final Runnable runnable, final int delay){
        //final ScheduledThreadPoolExecutor executor = new ScheduledThreadPoolExecutor(1);
        //executor.schedule(runnable, delay, TimeUnit.MILLISECONDS);

        Thread thread = new Thread(new Runnable() {
            @Override public void run() {
                try {
                    Thread.sleep(delay);
                    runnable.run();
                } catch (Exception ex){}
            }
        });
        thread.run();
    }


    // NETWORK //

    public static HttpResponse<String> SendCommand(String Command, String[] Arguments, String IP, int Port, String Token) {
        String URL = "http://" + IP + ":" + String.valueOf(Port);
        HttpResponse<String> response = null;

        try {
            JSONArray ja = new JSONArray(Arguments);
            response = Unirest.post(URL)
                    .header("connection", "close")
                    .field("auth", String.valueOf(Token))
                    .field("cmd", Command)
                    .field("args", ja.toString())
                    .asString();

            /* Example of a GET request equivalent
            response = Unirest.get(URL)
                    .header("connection", "close")
                    .queryString("auth", String.valueOf(bhash(Token)))
                    .queryString("cmd", Command)
                    .queryString("args", new ArrayList<>(Arrays.asList(Arguments)))
                    .asString();
            */

            //return response;
            /*
            //Request response
            if (response.getStatus() < 400) //Response good
                return "Status Code:" + String.valueOf(response.getStatus()) + "\n" + response.getBody();
            else if (response.getStatus() == 500) //Response server error
                return NETWORK_REQ_ERROR + ":" + IP + " encountered an error processing the request\n" + response.getBody();
            else if (response.getStatus() == 401) {//Unauthorized
                return NETWORK_REQ_ERROR + ":" + NETWORK_UNAUTHORIZED;
            }
            else //Response bad
                return NETWORK_REQ_ERROR + ":Unknown error (status code " + String.valueOf(response.getStatus()) + ")";
            */
        } catch (UnirestException ex){
            // timeout
            if (ex.getMessage().contains("ConnectTimeoutException")){
                //return NETWORK_REQ_ERROR + ":" + NETWORK_CONNECTION_TIMEOUT;
            }
            // refused
            if (ex.getMessage().contains("HttpHostConnectException")) {
                //return NETWORK_REQ_ERROR + ":" + NETWORK_CONNECTION_REFUSED;
            }
            // other failure
            //return NETWORK_REQ_ERROR + ":" + NETWORK_GENERAL_FAILURE + "\n    Reason:" + ex.getMessage();
        }

        return response;
    }

}
