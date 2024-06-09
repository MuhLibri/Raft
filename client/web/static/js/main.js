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
        url = `/get/${key.value}`;
    } else if (commandSelect.value === 'set') {
        url = '/set';
        method = 'POST';
        body = JSON.stringify({ key: key.value, value: value.value });
    } else if (commandSelect.value === 'delete') {
        url = `/delete/${key.value}`;
        method = 'DELETE';
    } else if (commandSelect.value === 'append') {
        url = '/append';
        method = 'POST';
        body = JSON.stringify({ key: key.value, value: value.value });
    } else if (commandSelect.value === 'strln') {
        url = `/strln/${key.value}`;
    }
    

    console.log(`Sending ${method} request to ${url} with body: ${body}`);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);  // 10 sec

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: method !== 'GET' ? body : null,
        signal: controller.signal
    })
    .then(response => {
        clearTimeout(timeoutId); 
        return response.json();
    })
    .then(response => {
        loadingSpinner.style.display = 'none'; 
        resultOutput.innerText = JSON.stringify(response, null, 2);
        serverOutput.innerText = `${response.server_ip?? ''}:${response.server_port?? ''}`;
        commandOutput.innerText = build_command_output(commandSelect.value, key.value, value.value);
    })
    .catch(error => {
        loadingSpinner.style.display = 'none'; 
        if (error.name === 'AbortError') {
            resultOutput.innerText = 'Error: Request timed out';
        } else {
            resultOutput.innerText = `Error: ${error}`;
        }
        serverOutput.innerText = '';
    });
}

function build_command_output(command, key = null, value = null) {
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
        } else if (this.value === 'get' || this.value === 'delete' || this.value === 'strln') {
            keyGroup.style.display = 'block';
            valueGroup.style.display = 'none';
        } else {
            keyGroup.style.display = 'block';
            valueGroup.style.display = 'block';
        }
    });

    commandSelect.dispatchEvent(new Event('change'));  // Trigger change event to set initial state
});
