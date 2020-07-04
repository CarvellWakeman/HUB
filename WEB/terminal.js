
//Terminal layout
var body = document.getElementsByTagName('body')[0];
var terminal_container;
var output_container;
var input_container;
var input_text;
var btn_logout;



//String constants
var SERVER_DOMAIN = '@hub';
var SEP = ':';
var SERVER_DIRECTORY = '/ $ ';
var SERVER_NAME = SERVER_DOMAIN + SEP + SERVER_DIRECTORY;

var ERR_CONTACT = 'Error contacting HUB';
var ERR_FAILSEND = 'Failed to send data';

//Color constants
var TERMINAL_WHITE = '#FFFFFF';
var TERMINAL_GREEN = '#55FF55';
var TERMINAL_BLUE = '#55BFFF';


//Network
IP = window.location.hostname;
PORT = 5000;

//Authentication
username = sessionStorage.getItem("username");
password = sessionStorage.getItem("password");

//Other
drag_threshold = 10
dragging = false
last_mouse_position = {x:0, y:0}

//Command history
var command_history = []
var command_index = -1



window.onload = function() {
	// Get elements
	terminal_container = document.getElementById('terminal_container');
	output_container = document.getElementById('output_container');
	input_container = document.getElementById('input_container');
	input_text = document.getElementById('input_text');
	btn_logout = document.getElementById('btn_logout');

	// Prompt
	input_container.insertBefore(create_input_line(), input_container.firstChild);

	// Send input by keypress
	input_text.addEventListener('keydown', function(event){
		if (event.keyCode == 13){ // Enter key
			handle_input();
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
				}
			}(this)), 0);
		}
		else if (event.keyCode == 40) { //Down arrow
			if (command_index-1 >= 0) {
				command_index=command_index-1;
				input_text.value = command_history[command_index];
			} else if (command_index-1 < 0) {
				command_index = -1;
				input_text.value = '';
			}
			// Move cursor to end
			input_text.focus();
		}
	});


	// Log out
	btn_logout.onclick = function(){
		sessionStorage.setItem("username", "");
		sessionStorage.setItem("password", "");

		window.location.replace("http://" + IP);
	};

	// Focus input when the page is clicked UNLESS the user is dragging
	body.addEventListener('mousedown', function(e) { 
		dragging = false; 
		last_mouse_position = { x:e.clientX, y:e.clientY };
	});
	body.addEventListener('mousemove', function(e) { 
		deltaX = Math.abs(last_mouse_position.x - e.clientX)
		deltaY = Math.abs(last_mouse_position.y - e.clientY)

		if (deltaX > drag_threshold || deltaY > drag_threshold) {
			dragging = true
		}
	});
	body.addEventListener('mouseup', function(e) { 
		if (dragging) { 
			e.preventDefault(); 
			e.stopPropagation(); 
			dragging=false; 
		} else {
			input_text.focus();
		}
	});

}


// Creating input lines
function create_input_line()
{
	var cont = document.createElement('div');
	cont.style.display="flex";

	//Create input server line
	var sdom = document.createElement('div');
		sdom.innerHTML = username + SERVER_DOMAIN;
		sdom.style.color = TERMINAL_GREEN;
		sdom.className = 'output_line';

	var ssep = document.createElement('div');
		ssep.innerHTML = SEP;
		ssep.style.color = TERMINAL_WHITE;
		ssep.className = 'output_line';

	var sdir = document.createElement('div');
		sdir.innerHTML = SERVER_DIRECTORY;
		sdir.style.color = TERMINAL_BLUE;
		sdir.className = 'output_line';
	
	cont.appendChild(sdom);
	cont.appendChild(ssep);
	cont.appendChild(sdir);

	return cont
}

// Creating output lines
function create_output_line(text, header = true)
{
	//Create output line
	var output_line = document.createElement('div');
	output_line.style.display="flex";

		if (header) {
			output_line.appendChild(create_input_line());
		}

		output_line.style.overflow = 'auto';

		var textElement = document.createElement('div')
			textElement.className = 'output_line';
			textElement.innerHTML = text;
		output_line.appendChild(textElement);

	output_container.appendChild(output_line);
}

// Reset for new input
function reset_input()
{
	//Clear input field
	input_text.value = '';

	//Enable input_container
	input_container.style.visibility = 'visible';

	//Focus on input box
	input_text.focus();

	//Scroll terminal container to bottom
	scroll_to_bottom(terminal_container)
}

// Scroll to bottom
function scroll_to_bottom()
{
	body.scrollTop = body.scrollHeight;
}


// Managing terminal
function handle_input() {
	// Split input
	var split = input_text.value.split(' ');
	var cmd = split[0];
	split.splice(0,1);
	var args = split;

	// Check username and pass
	if (username == null || password == null){
		create_output_line("Username and password invalid!");
		window.location.replace("http://" + IP);
		reset_input();
		return;
	}
	

	// Add to history (beginning of array)
	if (input_text.value.length > 0 && input_text.value != command_history[0]) {
		command_history.unshift(input_text.value);
	}
	command_index = -1;

	// Special breaking case for clear command
	if (input_text.value == 'clear') {
		output_container.innerHTML = '';
		input_text.value = '';
		return;
	}

	//Create input line and add it to the output container (Record input in output history)
	create_output_line(input_text.value);

	if (input_text.value.length > 0) {
		//Disable input_container until response received
		input_container.style.visibility = 'hidden';

		//Send input
		send_input(cmd, args, function(result, status) {
			create_output_line(result, false);
			reset_input();
			scroll_to_bottom();
		});
	} else {
		reset_input();
		scroll_to_bottom();
	}		
}


// Authentication encoding
function encode(username, password){
	return btoa(username + ":" + password);
}


// Send input to HUB
function send_input(cmd, args, callback = null) {
	//If data was entered
	if (cmd != null) {

		console.log('Cmd:' + cmd)
		console.log('args:' + JSON.stringify(args))

		//Send request
		$.ajax({
			type: 'GET',
			url: 'http://' + IP + ':' + PORT,
			headers: {
				'Authorization': encode(username, password)
			},
			timeout: 60000,
			dataType: 'text',
			data: {
				'cmd': cmd,
				'args': JSON.stringify(args),
			},
			//Send response
			success: function (response, textStatus, XHR) {
				console.log('Response:');
				console.log(response);
				
				//Add response to the output container
				result = replaceAll(replaceAll(replaceAll(response, '<', '&lt'), '>', '&gt'), '\n', '<br />')
				//if (display) { create_output_line(result, false); }
				if (callback != null) { callback(result, XHR.status); }
			},
			error: function (err) {
				console.log('ERROR:');
				console.log(err);

				//Add response to the output container
				//if (display) { create_output_line(ERR_CONTACT, false) }
				if (callback != null) { callback(ERR_CONTACT, err.status); }
			},
			failure: function (response, textStatus, XHR) {
				console.log('FAIL:');
				console.log(response);

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
		return str.replace(new RegExp(find, 'g'), replace);
	}
	else { return str; }
}

