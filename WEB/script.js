
//Terminal layout
var body = document.getElementsByTagName("body")[0];
var terminal_container;
var output_container;
var input_container;
var input;
var input_title;



//String constants
var SERVER_DOMAIN = "user@hub";
var SEP = ":";
var SERVER_DIRECTORY = "/ $ ";
var SERVER_NAME = SERVER_DOMAIN + SEP + SERVER_DIRECTORY;
var SERVER_HEADERS = ["Welcome to the HUB.", "Enter a command below."];

var ENTER_AUTH = "Enter authentication: ";
var AUTH_FAIL = "Authentication invalid";

var ERR_CONTACT = "Error contacting HUB";
var ERR_FAILSEND = "Failed to send data";

//Color constants
var TERMINAL_WHITE = "#FFFFFF";
var TERMINAL_GREEN = "#55FF55";
var TERMINAL_BLUE = "#55BFFF";


//Network
IP = window.location.host
PORT = 5000;

//Authentication
auth_key = null;

//Other
drag_threshold = 10
dragging = false
last_mouse_position = {x:0, y:0}



function buildTerminal()
{
	//Black body background
	body.style.background = "black";

	//Create terminal container
	terminal_container = document.createElement("div");
		//terminal_container.style.border = "1px solid red"

		//terminal_container.style.position = "fixed";
		terminal_container.style.display = "block"

		terminal_container.style.marginLeft = "5px"
		terminal_container.style.marginTop = "20px"
		terminal_container.style.marginBottom = "20px"

		terminal_container.style.overflow = "hidden";
		//terminal_container.style.overflowY = "scroll";

	body.appendChild(terminal_container);

	//Create output container
	output_container = document.createElement("div");
		//output_container.style.border = "1px solid green"

		output_container.style.width = "100%";

		output_container.style.overflow = "auto";

		output_container.style.whiteSpace = "pre";

		output_container.style.fontSize = "12pt";
		output_container.style.fontFamily = "Courier New"
	terminal_container.appendChild(output_container);


	//Create input container
	input_container = document.createElement("div");
		//input_container.style.border = "1px solid blue"

		input_container.style.width = "100%";

		input_container.style.display = "flex";
		input_container.style.alignItems = "center";

		input_container.style.whiteSpace = "pre";

		input_container.style.fontSize = "12pt";
		input_container.style.fontFamily = "Courier New";
	terminal_container.appendChild(input_container);

	//Terminal input title
	input_title = document.createElement("div");
		input_title.style.color = TERMINAL_WHITE;
		input_title.innerHTML = ENTER_AUTH;
	input_container.appendChild(input_title)


	//Create input box
	input = document.createElement("input");
		input.style.height = "14px";

		input.style.background = "Black"; //Black
		input.style.color = TERMINAL_WHITE;
		input.style.borderColor = "black";

		input.style.padding = "0px";
		input.style.margin = "0px";
		input.style.marginLeft = "-2px";

		input.style.fontSize = "12pt";
		input.style.fontFamily = "Courier New";

	input_container.appendChild(input);

	//Send input by keypress
	input.addEventListener("keypress", handle_input);

	//Focus input when the page is clicked UNLESS the user is dragging
	body.addEventListener("mousedown", function(e){ 
		dragging = false; 
		last_mouse_position = { x:e.clientX, y:e.clientY };
	});
	body.addEventListener("mousemove", function(e){ 
		deltaX = Math.abs(last_mouse_position.x - e.clientX)
		deltaY = Math.abs(last_mouse_position.y - e.clientY)

		if (deltaX > drag_threshold || deltaY > drag_threshold){
			dragging = true
		}
	});
	body.addEventListener("mouseup", function(e){ 
		if (dragging) { 
			e.preventDefault(); 
			e.stopPropagation(); 
			dragging=false; 
		} else {
			input.focus();
		}
	});
}

//Creating input lines
function get_server_input_line(){
	var cont = document.createElement("div");

	//Create input server line
	var sdom = document.createElement("div");
		sdom.innerHTML = SERVER_DOMAIN;
		sdom.style.color = TERMINAL_GREEN;
		sdom.style.float = "left";
		sdom.style.fontSize = "12pt";
		sdom.style.fontFamily = "Courier New";

	var ssep = document.createElement("div");
		ssep.innerHTML = SEP;
		ssep.style.color = TERMINAL_WHITE;
		ssep.style.float = "left";
		ssep.style.fontSize = "12pt";
		ssep.style.fontFamily = "Courier New";

	var sdir = document.createElement("div");
		sdir.innerHTML = SERVER_DIRECTORY;
		sdir.style.color = TERMINAL_BLUE;
		sdir.style.float = "left";
		sdir.style.fontSize = "12pt";
		sdir.style.fontFamily = "Courier New";
	
	cont.appendChild(sdom);
	cont.appendChild(ssep);
	cont.appendChild(sdir);

	return cont
}

//Creating output lines
function create_output_line(text, header = true)
{
	//Create output line
	var output_line = document.createElement("div");

		if (header) { output_line.appendChild(get_server_input_line()); }

		output_line.style.overflow = "auto";

		var textElement = document.createElement("div")
			textElement.style.fontSize = "12pt";
			textElement.style.fontFamily = "Courier New";
			textElement.style.color = TERMINAL_WHITE;
			textElement.innerHTML = text;
		output_line.appendChild(textElement);

	output_container.appendChild(output_line);
}

//Reset for new input
function reset_input()
{
	//Clear input field
	input.value = "";

	//Enable input_container
	input_container.style.visibility = "visible";

	//Focus on input box
	input.focus();

	//Scroll terminal container to bottom
	scroll_to_bottom(terminal_container)
}

//Scroll to bottom
function scroll_to_bottom(){
	body.scrollTop = body.scrollHeight;
}

//Managing terminal
function handle_input(event){
	
	//Enter key
	if (event.keyCode == 13){
		//Is this input an auth key?
		if (auth_key == null){
			send_input("checkauth", input.value, function(result, status){
				if (status < 400 && status > 0 && status != null){
					//Set auth key
					auth_key = input.value

					//Header text
					for (i = 0; i < SERVER_HEADERS.length; i++) { create_output_line(SERVER_HEADERS[i]); }

					//Set server domain/directory title
					input_container.replaceChild(get_server_input_line(), input_title);
				}
				else {
					//No response
					if (status == 0){
						create_output_line(ERR_CONTACT, false)
					} else {
						create_output_line(AUTH_FAIL, false)
					}
				}

				reset_input()
				scroll_to_bottom()
			});
		}
		else{
			//Create input line and add it to the output container (Record input in output history)
			create_output_line(input.value);

			if (input.value.length > 0) {
				//Disable input_container until response received
				input_container.style.visibility = "hidden";

				//Send input
				send_input(input.value, auth_key, function(result, status){
					create_output_line(result, false)
					reset_input()
					scroll_to_bottom()
				});
			} else {
				reset_input()
				scroll_to_bottom()
			}
		}
		
	}
}

window.onload = function() {
	//setTimeout(function(){
	url = window.location.href
	split = url.split("?")
	auth = ""
	cmd = "checkauth"

	//If parameters were included
	if (split.length > 1){
		params = split[1].split("&")

		for (i = 0; i < params.length; i++){
			param = params[i]

			//Auth parameter
			if (param.includes("auth=")){
				auth = param.replace("auth=","")
			}
			//Command parameter
			else if (param.includes("command=")){
				cmd = param.replace("command=","")
			}
			//Else ignore it
		}

		//Check if auth and command are present
		if (auth != ""){
			send_input(cmd, auth, function(result, status){
				if (status < 400 && status > 0 && status != null){
					//Set auth key
					auth_key = auth

					//Set server domain/directory title
					input_container.replaceChild(get_server_input_line(), input_title);

					//Print result
					create_output_line(result, false)
				} else {
					//No response
					if (status == 0){
						create_output_line(ERR_CONTACT, false)
					} else {
						create_output_line(AUTH_FAIL, false)
					}
				}

				reset_input()
				scroll_to_bottom()
			})
		}
	}
	
}//);

//TODO Weird bug when sending request from mobile browser: Exception happened during processing of request from ('50.188.131.99', 47675)
function send_input(cmd, auth, callback = null){
	//If data was entered
	if (cmd != null && cmd.length > 0 && auth != null) {
		console.log("http://" + IP + ":" + PORT + "/?auth=" + auth + "&command=" + cmd)
		//Send request
		$.ajax({
			type: "GET",
			url: "http://" + IP + ":" + PORT + "/?auth=" + auth + "&command=" + cmd,
			timeout: 10000,
			dataType: "text",
			//data: {
			//	"auth": auth, 
			//	"command": cmd,
			//},
			//Send response
			success: function (response, textStatus, XHR) {
				console.log("Response:")
				console.log(response)
				
				//Add response to the output container
				result = replaceAll(replaceAll(replaceAll(response, "<", "&lt"), ">", "&gt"), "\n", "<br />")
				//if (display) { create_output_line(result, false); }
				if (callback != null) { callback(result, XHR.status); }
			},
			error: function (err) {
				console.log("ERROR:")
				console.log(err)

				//Add response to the output container
				//if (display) { create_output_line(ERR_CONTACT, false) }
				if (callback != null) { callback(ERR_CONTACT, err.status); }
			},
			failure: function (response, textStatus, XHR) {
				console.log("FAIL:")
				console.log(response)

				//Add response to the output container
				//if (display) { create_output_line(ERR_FAILSEND, false) }
				if (callback != null) { callback(ERR_FAILSEND, XHR.status); }
			},
		});
	}
}

function replaceAll(str, find, replace) {
	if (str != null && str.length > 0){
		return str.replace(new RegExp(find, "g"), replace);
	}
	else { return str; }
}





buildTerminal()