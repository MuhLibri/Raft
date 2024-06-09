# if3230-tubes-mineraft
if3230-tubes-mineraft created by GitHub Classroom

## Table of Contents
- [if3230-tubes-mineraft](#if3230-tubes-mineraft)
  - [Table of Contents](#table-of-contents)
  - [Description](#description)
  - [Features](#features)
  - [How to Run](#how-to-run)
  - [Contributors](#contributors)

## Description
Raft is a consensus algorithm designed as an alternative to Paxos. It was meant to be more understandable than Paxos by means of separation of logic, but it is also formally proven safe and offers some additional features. Raft offers a generic way to distribute a state machine across a cluster of computing systems, ensuring that each node in the cluster agrees upon the same series of state transitions. This project is an implementation of Raft consensus algorithm in Python.

## Features
- Leader Election
- Log Replication
- Membership Change
- Client Request
- Execute Function
- Dashboard Management

## How to Run
1. Clone this repository
2. Run the following command to run the server
    ```bash
    make run
    ```
3. Run the following command to run the client
   
   You can run the client in two ways:
    - Run the client in CLI mode
        ```bash
        make run-client
        ```
    - Run the client in Web mode
        ```bash
        make run-client-web
        ```
        
4. The Client and Server are now running. You can input your command to the client terminal


## Contributors

| NIM      | Nama                           | Contributions                                                        |
| -------- | ------------------------------ | -------------------------------------------------------------------- |
| 13521043 | Nigel Sahl                     | Base Functionality, Heartbeat, Leader Election, makefile and bat     |
| 13521047 | Muhammad Equilibrie Fajria     | Membership change                                                    |
| 13521048 | M Farrel Danendra Rachim       | Log Replication                                                      |
| 13521058 | Ghazi Akmal Fauzan             | Management Dashboard, CLI format, Execute, Client                    |
| 13521070 | Akmal Mahardika Nurwahyu P     | Client-Cli, Client-Web, Management Dashboard                         |

