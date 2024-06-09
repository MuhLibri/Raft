/* Input text value */
const key = document.getElementById('key');
const value = document.getElementById('value');

/* Input */
const commandSelect = document.getElementById('command');

/* Output */
// Text
const serverOutput = document.getElementById('server-info-out');
const commandOutput = document.getElementById('command-info-out');
const resultOutput = document.getElementById('result-info-out');


/* UI */
const loadingSpinner = document.getElementById('loading-spinner');
const valueGroup = document.getElementById('value-group');
const keyGroup = document.getElementById('key-group');

function sendCommand() {
    loadingSpinner.style.display = 'block';  // Show spinner before sending the request

    let url = '';
    let method = 'GET';
    let body = null;

    if (commandSelect.value === 'ping') {
        url = '/ping';
    } else if (commandSelect.value === 'get') {
        url = `/get/${key}`;
    } else if (commandSelect.value === 'set') {
        url = '/set';
        method = 'POST';
        body = JSON.stringify({ key: key, value: value });
    } else if (commandSelect.value === 'delete') {
        url = `/delete/${key}`;
        method = 'DELETE';
    } else if (commandSelect.value === 'append') {
        url = '/append';
        method = 'POST';
        body = JSON.stringify({ key: key, value: value });
    }

    console.log(`Sending ${method} request to ${url} with body: ${body}`);

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: method !== 'GET' ? body : null
    })
    .then(response => response.json())
    .then(response => {
        loadingSpinner.style.display = 'none';  // Hide spinner on success
        resultOutput.innerText = JSON.stringify(response, null, 1);
        serverOutput.innerText = `${response.server_ip}:${response.server_port}`;
        commandOutput.innerText = build_command_output(commandSelect.value, key.value, value.value);
    })
    .catch(error => {
        loadingSpinner.style.display = 'none';  // Hide spinner on error
        resultOutput.innerText = `Error: ${error}`;
        serverOutput.innerText = '';
        commandOutput.innerText = build_command_output(commandSelect.value, key.value, value.value);
    });
}

function build_command_output(command, key=null, value=null) {
    let output = command;
    if (key) {
        output += ` ${key}`;
    }
    if (value) {
        output += ` ${value}`;
    }
    return output;

}

document.addEventListener('DOMContentLoaded', function() {
    
    commandSelect.addEventListener('change', function() {
        if (this.value === 'ping') {
            keyGroup.style.display = 'none';
            valueGroup.style.display = 'none';
        } else if (this.value === 'get' || this.value === 'delete') {
            keyGroup.style.display = 'block';
            valueGroup.style.display = 'none';
        } else {
            keyGroup.style.display = 'block';
            valueGroup.style.display = 'block';
        }

        if (this.value === 'ping' || this.value === 'get' || this.value === 'delete') {
            valueGroup.style.display = 'none';
        } else {
            valueGroup.style.display = 'block';
        }
    });

    commandSelect.dispatchEvent(new Event('change'));  // Trigger change event to set initial state
});
