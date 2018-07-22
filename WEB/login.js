
//Terminal layout
var body = document.getElementsByTagName("body")[0];
var input_username;
var username_validate;
var input_password;
var password_validate;
var input_login;
var login_status;

var connection_status;



//Network
IP = window.location.host;
PORT = 5000;

var ERR_CONTACT = 'Error contacting HUB';
var ERR_FAILSEND = 'Failed to send data';

var username = null;
var password = null;

window.onload = function() {
	// Get elements
	input_username = document.getElementById("input_username");
	username_validate = document.getElementById("username_validate");
	input_password = document.getElementById("input_password");
	password_validate = document.getElementById("password_validate");
	login_status = document.getElementById("login_status");
	input_login = document.getElementById("input_login");
	connection_status = document.getElementById("connection_status");


	// Enter key in input field
	input_password.addEventListener("keydown", function(event){
		if (event.keyCode == 13){
			tryLogin();
		}
	});

	// Login press
	input_login.onclick = function(){
		tryLogin();
	}


	// URL parameters
	url = window.location.href;
	split = url.split('?');
	cmd = '';
	args = [];

	//If parameters were included
	if (split.length > 1) {
		params = split[1].split('&');

		for (i = 0; i < params.length; i++) {
			param = params[i];

			//Auth parameters
			if (param.includes('user=')) {
				username = param.replace('user=','');
			}
			else if (param.includes('pass=')) {
				password = param.replace('pass=','');
			}
			//Command parameter
			else if (param.includes('cmd=')) {
				cmd = param.replace('cmd=','');
			}
			//Argument parameter
			else if (param.includes('args=')) {
				args.push(param.replace('args=', ''));
			}
		}

		// Check and send command
		if (username != null && password != null && username != '' && password != '' && cmd != '') {
			send_input(cmd, args, function(result, status) {
				if (status > 0 && status < 400 && status != null) {
					window.location.replace("http://" + IP + "/terminal.html");
				} else {
					//No response
					if (status == 0) {
						create_output_line(ERR_CONTACT, false);
					} else {
						create_output_line(AUTH_FAIL, false);
					}
				}
			});
		}
	}


	// Connection status
	var ping = function(){
		updateConnectionStatus(null);

		send_input('ping', [], function(result,status){
			if (status >0 && status < 500){
				updateConnectionStatus(true);
			} else {
				updateConnectionStatus(false);
			}
			setTimeout(ping, 5000);
		}, timeout=5000, log=false);
	};
	ping();
}


// Hide/show inputs
function hideInputs(){
	input_username.disabled = true;
	input_password.disabled = true;
	input_login.disabled = true;
}
function showInputs(){
	input_username.disabled = false;
	input_password.disabled = false;
	input_login.disabled = false;
}

function clearInput(){
	input_username.value = '';
	input_password.value = '';
	login_status.innerHTML = '';
	login_status.style.display = 'none';
}


// Connection status
function updateConnectionStatus(connected){
	if (connected == null){
		connection_status.style.color = "#d1a300";
		connection_status.innerHTML = "Refreshing <i class='fa fa-spinner fa-pulse fa-fw'></i>";
	}
	else if (connected == true){
		connection_status.style.color = "#00db28";
		connection_status.innerHTML = "Online <i class='fa fa-check'></i>";
	} else {
		connection_status.style.color = "#db0000";
		connection_status.innerHTML = "Offline <i class='fa fa-times'></i>";
	}
}


// Attempt to login
function tryLogin() {
	// Field validation
	if (input_username.value.length == 0){
		username_validate.style.display = "block";
	} else {
		username_validate.style.display = "none";
	}

	if (input_password.value.length == 0){
		password_validate.style.display = "block";
	} else {
		password_validate.style.display = "none";
	}

	if (input_username.value.length > 0 && input_password.value.length > 0){
		hideInputs();
	} else {
		showInputs();
	}

	// Send input
	username = input_username.value;
	password = input_password.value;
	send_input('checkauth', [], function(result, status){
		if (status > 0 && status < 400){
			console.log("Result:");
			console.log(result);
			console.log("status:" + status);
			// Reset password field
			showInputs();
			clearInput();

			// Store username and password for terminal
			sessionStorage.SessionName = "HUB_LOGIN_VALID";
			sessionStorage.setItem("username", username);
			sessionStorage.setItem("password", password);

			// Open terminal
			window.location.replace("http://" + IP + "/terminal.html");
		} else {
			showInputs();
			input_password.value = '';
			if (result.responseText==undefined){
				login_status.innerHTML = ERR_CONTACT;
			} else {
				login_status.innerHTML = result.responseText;
			}
			login_status.style.display = 'block';
		}
	});
}


// Send input to HUB
function send_input(cmd, args, callback = null, timeout = 10000, log = true) {
	//If data was entered
	if (cmd != null) {

		if (log){
			console.log('Cmd:' + cmd)
			console.log('args:' + JSON.stringify(args))
		}

		//Send request
		$.ajax({
			type: 'GET',
			url: 'http://' + IP + ':' + PORT,
			headers: {
				'Authorization': encode(username, password)
			},
			timeout: timeout,
			dataType: 'text',
			data: {
				'cmd': cmd,
				'args': JSON.stringify(args),
			},
			//Send response
			success: function (response, textStatus, XHR) {
				if (log){
					console.log('Response:');
					console.log(response);
				}
				
				result = replaceAll(replaceAll(replaceAll(response, '<', '&lt'), '>', '&gt'), '\n', '<br />')
				if (callback != null) { callback(result, XHR.status); }
			},
			error: function (err) {
				if (log){
					console.log('ERROR:');
					console.log(err);
				}

				if (callback != null) { callback(err, err.status); }
			},
			failure: function (response, textStatus, XHR) {
				if (log){
					console.log('FAIL:');
					console.log(response);
				}

				if (callback != null) { callback(response, XHR.status); }
			},
		});
	}
}

// Authentication encoding
function encode(username, password){
	return btoa(username + ":" + password);
}


// Helpers
function replaceAll(str, find, replace) {
	if (str != null && str.length > 0) {
		return str.replace(new RegExp(find, "g"), replace);
	}
	else { return str; }
}
