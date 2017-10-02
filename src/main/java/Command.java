import java.util.ArrayList;

public class Command {

    // Private members
    private String mName;
    private ArrayList<CmdArg> mArgs;
    private String mDesc;
    private Utils.CLEARANCE mClearance;


    // Constructor
    public Command(String name, Utils.CLEARANCE clearance){
        mName = name;
        mDesc = "";
        mArgs = new ArrayList<>();
        mClearance = clearance;
    }


    // Accessors
    public String GetName(){ return mName; }
    public int GetNumReqArgs(){
        int tot = 0;
        for (CmdArg ca : GetArgs()){ if (!ca.optional) { tot++; } }
        return tot;
    }
    public ArrayList<CmdArg> GetArgs(){ return mArgs; }
    public String GetDesc(){ return mDesc; }
    public Utils.CLEARANCE GetClearance() { return mClearance; }


    // Mutators
    public void SetName(String name){ mName = name; }
    public void SetDesc(String desc){ mDesc = desc; }
    public void SetClearance(Utils.CLEARANCE clearance) { mClearance = clearance; }


    // Arguments
    public void AddArg(String arg, boolean optional){ mArgs.add(new CmdArg(arg, optional)); }

    public static String GetValidArgument(ArrayList<String> arguments, int index){
        if (arguments != null && arguments.size() > 0 && index < arguments.size()){ return arguments.get(index); }
        return null;
    }
    public String ValidateArguments(ArrayList<String> arguments){
        if (arguments != null && arguments.size() >= GetNumReqArgs()){
            return null;
        } else {
            return String.format("%s\n    USAGE:%s", Utils.CMD_ARGS_INVALID, GetUsage());
        }
    }
    public String GetUsage(){
        StringBuilder sb = new StringBuilder();
        sb.append(GetName()).append(" ");
        for (CmdArg ca : GetArgs()){
            if (ca.optional){
                sb.append("[").append(ca.arg_name).append("] ");
            } else {
                sb.append(ca.arg_name).append(" ");
            }
        }
        return sb.toString();
    }


    // Command
    public String Run(String username, String password, ArrayList<String> arguments){
        return "Not Implemented";
    }


    // Small class for command arguments
    private class CmdArg{
        public CmdArg(String arg_name, boolean optional){
            this.arg_name = arg_name;
            this.optional = optional;
        }
        String arg_name = "";
        boolean optional = false;
    }

}
