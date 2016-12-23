IP = (window.location).toString().replace("//", "*").replace("/","").replace("*","//")
PORT = 5000

$(document).ready(function(){
	var output = document.getElementById("commandResponse");

	var input_auth = $("#authorization")
	var input_command = $("#commandData")

	var button_submit = $("#commandSubmit")

	//Submit click
    button_submit.click(function(){
    	//If data was entered
    	if (input_command.val().length > 0) {

    		//Send request
	    	$.ajax({
			    type: "POST",
			    url: IP + ":" + PORT,
			    dataType:"text",
			    data: {
			    	"auth": input_auth.val(), 
	        		"command": input_command.val(),
	    		},
	    		//Send response
				success: function (response) {
					console.log(response)
					output.innerHTML = replaceAll(replaceAll(response, "<", "&lt"), ">", "&gt")
				},
				error: function (err) {
					console.log("ERROR:")
					console.log(err)
					//alert("ERROR:" + err)
					output.innerHTML = "Error: Could not contact HUB"
				},
				failure: function (response) {
					console.log("FAIL" + response)
					//alert("FAIL" + response);
					output.innerHTML = "Failed to send data"
				},
			});
    	}
    });

    input_command.keyup(function(event){
	    if(event.keyCode == 13){
	        button_submit.click();
	    }
	});
});


function replaceAll(str, find, replace) {
	if (str != null && str.length > 0){
		return str.replace(new RegExp(find, "g"), replace);
	}
	else { return str; }
}