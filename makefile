SERVER_PATH = src/server.py
CLIENT_PATH = src/client.py
CLIENT_CLI_PATH = client/cli/client.py
CLIENT_WEB_PATH = client/web/client.py

run:
	@echo "Running the program"
	run.bat $(MODE)

add-node:
	@echo "Adding a new node"
	python $(SERVER_PATH) $(IP) $(PORT) $(CONTACT_IP) $(CONTACT_PORT)

run-server:
	@echo "Running the server"
	python $(SERVER_PATH) $(IP) $(PORT)

run-client:
	@echo "Running the client"
	python $(CLIENT_PATH) $(IP) $(PORT)

run-client-cli:
	@echo "Running the client"
	python $(CLIENT_CLI_PATH) $(IP) $(PORT)

run-client-web:
	@echo "Running the client"
	python $(CLIENT_WEB_PATH) $(IP) $(PORT)
