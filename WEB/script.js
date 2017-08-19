
//Terminal layout
var body = document.getElementsByTagName("body")[0];
var terminal_container;
var output_container;
var input_container;
var input_text;
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
IP = window.location.host;
PORT = 5000;

//Authentication
auth_key = null;

//Other
drag_threshold = 10
dragging = false
last_mouse_position = {x:0, y:0}

//Command history
var command_history = []
var command_index = -1



// Creating input lines
function create_input_line()
{
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

// Creating output lines
function create_output_line(text, header = true)
{
	//Create output line
	var output_line = document.createElement("div");

		if (header) { output_line.appendChild(create_input_line()); }

		output_line.style.overflow = "auto";

		var textElement = document.createElement("div")
			textElement.style.fontSize = "12pt";
			textElement.style.fontFamily = "Courier New";
			textElement.style.color = TERMINAL_WHITE;
			textElement.innerHTML = text;
		output_line.appendChild(textElement);

	output_container.appendChild(output_line);
}

// Reset for new input
function reset_input()
{
	//Clear input field
	input_text.value = "";

	//Enable input_container
	input_container.style.visibility = "visible";

	//Focus on input box
	input_text.focus();

	//Scroll terminal container to bottom
	scroll_to_bottom(terminal_container)
}

// Scroll to bottom
function scroll_to_bottom() {
	body.scrollTop = body.scrollHeight;
}

// Authorization
function bhash(key) {
	r = 0;
	for (i = 0; i < key.length; i++) {
		r += (i+1) * key.charCodeAt(i);
	}
	return r;
}

// Managing terminal
function handle_input(event) {
	//Enter key
	if (event.keyCode == 13) { 
		// Split input
		var split = input_text.value.split(" ");
		var cmd = split[0];
		split.splice(0,1);
		var args = split;

		//Is this input an auth key?
		if (auth_key == null) {
			// input was provided
			if (input_text.value.length > 0) {
				send_input("checkauth", [], input_text.value, function(result, status) {
					if (status < 400 && status > 0 && status != null) {
						//Set auth key
						auth_key = input_text.value;

						//Header text
						for (i = 0; i < SERVER_HEADERS.length; i++) {
							create_output_line(SERVER_HEADERS[i]);
						}

						//Set server domain/directory title
						input_container.replaceChild(create_input_line(), input_title);

						//Set input field back to regular text input
						input_text.type = "text";
					}
					else {
						//No response
						if (status == 0) {
							create_output_line(ERR_CONTACT, false);
						} else {
							create_output_line(AUTH_FAIL, false);
						}
					}

					reset_input();
					scroll_to_bottom();
				});
			}
		}
		else {

			// Add to history (beginning of array)
			if (input_text.value.length > 0 && input_text.value != command_history[0]) {
				command_history.unshift(input_text.value);
			}
			
			command_index = -1;

			// Special breaking case for clear command
			if (input_text.value == "clear") {
				output_container.innerHTML = "";
				input_text.value = "";
				return;
			}

			//Create input line and add it to the output container (Record input in output history)
			create_output_line(input_text.value);

			if (input_text.value.length > 0) {
				//Disable input_container until response received
				input_container.style.visibility = "hidden";

				//Send input
				send_input(cmd, args, auth_key, function(result, status) {
					create_output_line(result, false);
					reset_input();
					scroll_to_bottom();
				});
			} else {
				reset_input();
				scroll_to_bottom();
			}
		}
	}
	else if (event.keyCode == 38) { //Up arrow
		if (command_index+1 < command_history.length) {
			command_index=command_index+1;
			input_text.value = command_history[command_index];
		}

		// Move cursor to end
		setTimeout((function(input_text) {
        var strLength = input_text.value.length;
        return function() {
            if(input_text.setSelectionRange !== undefined) {
                input_text.setSelectionRange(strLength, strLength);
            } else {
                $(input_text).val(input_text.value);
            }
    	}}(this)), 0);
	}
	else if (event.keyCode == 40) { //Down arrow
		if (command_index-1 >= 0) {
			command_index=command_index-1;
			input_text.value = command_history[command_index];
		} else if (command_index-1 < 0) {
			command_index = -1;
			input_text.value = "";
		}
		// Move cursor to end
		input_text.focus();
	}
}

window.onload = function() {
	// Get elements
	terminal_container = document.getElementById("terminal_container");
	output_container = document.getElementById("output_container");
	input_container = document.getElementById("input_container");
	input_title = document.getElementById("input_title");
	input_text = document.getElementById("input_text");


	//Send input by keypress
	input_text.addEventListener("keydown", handle_input);

	//Focus input when the page is clicked UNLESS the user is dragging
	body.addEventListener("mousedown", function(e) { 
		dragging = false; 
		last_mouse_position = { x:e.clientX, y:e.clientY };
	});
	body.addEventListener("mousemove", function(e) { 
		deltaX = Math.abs(last_mouse_position.x - e.clientX)
		deltaY = Math.abs(last_mouse_position.y - e.clientY)

		if (deltaX > drag_threshold || deltaY > drag_threshold) {
			dragging = true
		}
	});
	body.addEventListener("mouseup", function(e) { 
		if (dragging) { 
			e.preventDefault(); 
			e.stopPropagation(); 
			dragging=false; 
		} else {
			input_text.focus();
		}
	});

	
	// URL parameters
	url = window.location.href;
	split = url.split("?");
	auth = "";
	cmd = "";
	args = [];

	//If parameters were included
	if (split.length > 1) {
		params = split[1].split("&");

		for (i = 0; i < params.length; i++) {
			param = params[i];

			//Auth parameter
			if (param.includes("auth=")) {
				auth = param.replace("auth=","");
				cmd = "checkauth";
			}
			//Command parameter
			else if (param.includes("cmd=")) {
				cmd = param.replace("cmd=","");
			}
			//Argument parameter
			else if (param.includes("args=")) {
				args.push(param.replace("args=", ""));
			}
		}

		//Check if auth and command are present
		if (auth != "") {
			send_input(cmd, args, auth, function(result, status) {
				if (status < 400 && status > 0 && status != null) {
					//Set auth key
					auth_key = auth;

					//Set server domain/directory title
					input_container.replaceChild(create_input_line(), input_title);

					//Print result
					create_output_line(result, false);

					// Text input set to regular text mode
					input_text.type = "text";
				} else {
					//No response
					if (status == 0) {
						create_output_line(ERR_CONTACT, false);
					} else {
						create_output_line(AUTH_FAIL, false);
					}
				}

				reset_input();
				scroll_to_bottom();
			})
		}
	}
}

// Send input to HUB
function send_input(cmd, args, auth, callback = null) {
	//If data was entered
	if (cmd != null && auth != null) {

		console.log("Cmd:" + cmd)
		console.log("args:" + JSON.stringify(args))

		//Send request
		$.ajax({
			type: "GET",
			url: "http://" + IP + ":" + PORT,// + "/?auth=" + auth + "&cmd=" + cmd,
			timeout: 10000,
			dataType: "text",
			data: {
				"auth": bhash(auth),
				"cmd": cmd,
				"args": JSON.stringify(args),
			},
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

// Helpers
function replaceAll(str, find, replace) {
	if (str != null && str.length > 0) {
		return str.replace(new RegExp(find, "g"), replace);
	}
	else { return str; }
}

