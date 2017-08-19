import java.util.ArrayList;

public class HubInfo extends Module {

    public HubInfo(final HubServer hub){
        super("Hub Info");

        // Ping command
        Command ping = new Command("ping", Utils.CLEARANCE.HIDDEN){
            @Override public String Run(ArrayList<String> arguments){
                return Utils.DEVICE_ONLINE;
            }
        };

        // Check Auth command
        Command checkauth = new Command("checkauth", Utils.CLEARANCE.BASIC){
            @Override
            public String Run(ArrayList<String> arguments){
                // If we made it this far, the authentication is valid
                return Utils.AUTH_PASS;
            }
        };
        checkauth.AddArg("token", false);
        checkauth.SetDesc("Checks hashed authentication token");

        // Check Auth command
        Command help = new Command("help", Utils.CLEARANCE.NONE){
            @Override
            public String Run(ArrayList<String> arguments){
                StringBuilder sb = new StringBuilder();
                String cmd = GetValidArgument(arguments, 0);

                for (Module m : hub.mModules){
                    for (Command c : m.mCommands){
                        // Don't shown hidden commands
                        if (c.GetClearance() != Utils.CLEARANCE.HIDDEN) {
                            if (cmd == null || cmd.equals(c.GetName())) {
                                sb.append(c.GetUsage()).append("\n");
                                if (!c.GetDesc().equals("")) {
                                    sb.append("    ").append(c.GetDesc()).append("\n");
                                }
                            }
                        }
                    }
                }

                return sb.toString();
            }
        };
        help.AddArg("command", true);
        help.SetDesc("Show this menu");


        // Add commands
        AddCommand(ping);
        AddCommand(checkauth);
        AddCommand(help);

    }

}
