public class Auth {
    String username;
    String password;
    Utils.CLEARANCE clearance;

    public Auth(String username, String password, Utils.CLEARANCE clearance){
        this.username = username;
        this.password = password;
        this.clearance = clearance;
    }
}
