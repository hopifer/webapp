var timeoutID;
var timeout = 600;

function setup() {
	document.getElementById("theButton").addEventListener("click", makePost, true);

	timeoutID = window.setInterval(poller, 600);
}

function makePost() {
	var httpRequest = new XMLHttpRequest();

	if (!httpRequest) {
		alert('Giving up :( Cannot create an XMLHTTP instance');
		return false;
	}

	var one = document.getElementById("messagey").value;
    var two = document.getElementById("user").value;
    var three = document.getElementById("titl").innerHTML;
	var row = [one, two];
	httpRequest.onreadystatechange = function() { handlePost(httpRequest, one, two) };
	
	httpRequest.open("POST", "/updatechat/"+three);
	httpRequest.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

	var data;
	data = "one=" + one + "&two=" + two;
	
	httpRequest.send(data);
}

function handlePost(httpRequest, row) {
	if (httpRequest.readyState === XMLHttpRequest.DONE) {
		if (httpRequest.status === 200) {
			addRow(row);
			clearInput();
		} else {
			alert("There was a problem with the post request.");
		}
	}
}

function poller() {
	var httpRequest = new XMLHttpRequest();
    var three = document.getElementById("titl").innerHTML;
	if (!httpRequest) {
		alert('Cannot create an XMLHTTP instance');
		return false;
	}

	httpRequest.onreadystatechange = function() { handlePoll(httpRequest) };
	httpRequest.open("GET", "/chatty/"+three);
	httpRequest.send();
}

function handlePoll(httpRequest) {
	if (httpRequest.readyState === XMLHttpRequest.DONE) {
		if (httpRequest.status === 200) {
			var tab = document.getElementById("theTable");
			while (tab.rows.length > 0) {
				tab.deleteRow(0);
			}
			
			var rows = JSON.parse(httpRequest.responseText);
			for (var i = 0; i < rows.length; i++) {
				addRow(rows[i]);
			}
			
			timeoutID = window.setTimeout(poller, timeout);
			
		} else {
            alert("The chat has been deleted!");
            timeoutID = window.setTimeout(poller, timeout);
            httpRequest.open("GET", "/lobby");
            return false;
		}
	}
}

function clearInput() {
	document.getElementById("messagey").value = "";
	document.getElementById("user").value = "";

}

function addRow(row) {
	var tableRef = document.getElementById("theTable");
	var newRow   = tableRef.insertRow();

	var newCell, newText;
	for (var i = 0; i < row.length; i++) {
		newCell  = newRow.insertCell();
		newText  = document.createTextNode(row[i]);
		newCell.appendChild(newText);
	}
}

window.addEventListener("load", setup, true);
