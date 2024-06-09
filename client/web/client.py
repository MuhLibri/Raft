from flask import Flask, request, jsonify, render_template
import json
import xmlrpc.client
from lib.app import App
from lib.struct import Address
import sys

app = Flask(__name__)

if len(sys.argv) < 3:
        print("Usage: client.py ip port")
        print("ip: server ip address")
        print("port: server port number")
        exit()

server_addr = Address(sys.argv[1], int(sys.argv[2]))
server = xmlrpc.client.ServerProxy(f"http://{server_addr.ip}:{server_addr.port}")
address_list : list[Address] = []

try:
    response = json.loads(server.connect())
    for addr in response["list"]:
        address_list.append(Address(addr["ip"], addr["port"]))
except Exception as e:
    print(f"Error connecting to server: please input an active server address\n")
    exit()

rpc_app = App(server, server_addr)
rpc_app.server_addr_list = address_list

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ping', methods=['GET'])
def ping():
    response = rpc_app.ping()
    print("Ping response:", response)
    return jsonify(response)

@app.route('/get/<key>', methods=['GET'])
def get_value(key):
    response = rpc_app.get(key)
    return jsonify(response)

@app.route('/set', methods=['POST'])
def set_value():
    data = request.json
    key = data.get('key')
    value = data.get('value')
    response = rpc_app.set(key, value)
    return jsonify(response)

@app.route('/delete/<key>', methods=['DELETE'])
def delete_value(key):
    response = rpc_app.delete(key)
    return jsonify(response)

@app.route('/append', methods=['POST'])
def append_value():
    data = request.json
    print("data", data)
    key = data.get('key')
    value = data.get('value')
    response = rpc_app.append(key, value)
    return jsonify(response)

@app.route('/strln/<key>', methods=['GET'])
def strln(key):
    response = rpc_app.strln(key)
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
