SERVER_PATH = src/server.py

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
