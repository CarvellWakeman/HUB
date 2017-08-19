import java.util.ArrayList;

public class Module {

    // Private members
    String mName;
    String mDescription;
    ArrayList<Command> mCommands;


    // Constructor
    public Module(String name){
        mName = name;
        mCommands = new ArrayList<>();
    }


    // Accessors
    public String GetName(){ return mName; }
    public String GetDescription(){ return mDescription; }


    // Mutators
    public void SetName(String name){ mName = name; }
    public void SetDescription(String description){ mDescription = description; }


    // Commands
    public void AddCommand(Command command){ mCommands.add(command); }
    public void RemoveCommand(Command command) { mCommands.remove(command); }
    public Command GetCommand(String name){
        for (Command c : mCommands){
            if (c.GetName().toLowerCase().equals(name.toLowerCase())){ return c; }
        }
        return null;
    }
}
