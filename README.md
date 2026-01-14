# 328-Final-Project
# Name: Samar Gill
# Name: Anesu Mudzingwa
# Name: Justin Ariel Nunes
# Professor: Dr.Schwesinger
# Date: 28 Nov 2024
# Assignments: Client, Server, Utility in Python(Group Project)
# Class: CPSC 328


# How to Build and run the client/server
Build - Makefiles for the server and client are included
Client - ./exec -h host -p port#
Server - ./exec -p port# -d root_directory(string path)

Dependencies:
(1) Python version - v3.10(specifically for the match command)
(2) Pickle, instill into the PUI class, for serializing and deserializing messages between the server and the clients

File/Folder Manifest:
Final-Project: Folder including all files nesscesary to run project
1. Utility.py - List of functionalities that will be common to both client and server also Protocol is handled in here.
2. ClientSJA328.py - Client code using the protocol to communicate with server
3. serverSJA328.py -  Server code using the protocol to respond to client
4. Makefile - file to build and run the project

Responsibility List:
Justin: Utility - List of functionalities that will be common to both client and server. The Protocol that will be implemented with the client and server. 

Anesu: Server -
This project implements a simple server in Python that handles client requests using parent-child processes. The server supports various file operations like CD, GET, PUT, LS, MKDIR, and PWD based on commands received from connected clients

Features
  Parent-Child Process Model: The server spawns child processes for each incoming client connection, allowing parallel handling of multiple requests.
  Request Handling: The server performs file operations (like reading, writing, changing directories, listing files, creating directories) based on client commands using a    structured protocol.
  Graceful Shutdown: The server listens for SIGINT and SIGALRM signals to handle shutdown and timeout scenarios.
  File Safety Check: Before processing file-related requests, the server checks if the requested file or directory is safe (i.e., inside the allowed directory).

While this implementation uses parent-child processes for handling client requests, using threads could be more efficient in certain scenarios:
  Better Resource Utilization: Threads are generally lighter-weight than processes and allow sharing of the same address space, leading to reduced overhead.
  Faster Context Switching: Threads avoid the need to create separate processes for each client. This results in faster context switching between different client requests    and lower latency
  Scalability: if the server expecyts a large number of connected clients using thrad would have been much better, avoiding constantly creating resource demanding processes

Input:

  Client:
  (1) Host 
  (2) Port Number

  Client:
  (1) Port Number
  (2) Root Directory
    
Samar: Client - Implementing a simple client in python that communicates with the server to manage files and directories on a remote machine using a simple protocol over a TCP socket.

Features:
Implemented the main structure of the REPL loop in run_repl, processing commands from the user and calling the handler function accordingly.
Developed the connect_to_server function to establish a TCP connection with the server, handling host and port as command line arguments.
Implemented the handler function, which processes different commands (exit, cd, get, ls, mkdir, put, etc.) and interacts with the server.
Developed the handler_helper function to send and receive messages from the server, encapsulating the data and managing timeouts during communication.
Implemented the show_help function to display the required help text listing all available commands.
Implemented error handling for different cases like FileNotFoundError, FileExistsError, and server timeouts within the handler function.

Protocol: Protocol.pdf
PUI Format:

  Action Type: 
    Specifies the command (e.g., CD, LS, PUT, etc.).
  Path: 
    The target file or directory for the operation.
  Recursion Flag: 
    A boolean indicating if the operation should be recursive (e.g., -R for get or put).
  Response (Optional): 
    Additional data needed for the operation (e.g., file content, directory listing).

The client sends commands to the server, each of which triggers a corresponding action.

  start: Initiates the session and retrieves the root directory.
  cd <path>: 
    Change directory on the server side.
  ls <path>: 
    List the contents of the directory.
  mkdir <path>: 
    Create a directory on the server.
  put <local-path> <remote-path>: 
    Upload a file to the server.
  get <remote-path> <local-path>: 
    Download a file from the server.
  pwd: 
    Show the current remote directory.
  lcd <path>: 
    Change the local directory for file operations.
  lls: 
    List contents of the local directory.
  lmkdir <path>: 
    Create a directory in the local system.

  FileNotFoundError: If the specified file or directory does not exist.
  FileExistsError: If the operation would overwrite existing directories/files.
  PermissionError: If there are access restrictions on the path.
  Timeouts: If the server or client fails to respond within a given timeframe.

Assumptions:
  Command Structure: 
    The client sends commands in the form of serialized objects using PICKLE protocol.
    
  Supported Commands:
    CD (Change Directory)
    GET (Retrieve File)
    PUT (Upload File)
    LS (List Directory Contents)
    MKDIR (Create Directory)
    PWD (Print Working Directory)
  File Path Validation:
    The server ensures that all paths are safe and inside the specified root directory.
    
  Timeout and Graceful Shutdown: 
    The server uses SIGINT and SIGALRM to handle shutdown and timeout gracefully.

Discussion:
1. Utility Problems/Solutions
   pathlib, handling PUT and GET functions with recursion.
3. Client Problems/Solutions
   The client was not receiving the server's responses:
     Server and Client were connecting and responding but when server sent a response back, the Client would not respond to it.
   Repl Loop:
     Handling error exceptions and making sure every command was getting called without a problem.   

5. Server Problems/Solutions
  (1) SIGINT -
      intially was having problems as ctrl + c was not working and starting a 10 second program shutdown
  (2) SIGALRM -
      initially was having difficulties intoducing a 10 second count down
      Solution: alm_handler(SIGALRM) and signal_handler(SIGINT)
     implementing both with corresponding signal handlers to ensure the countdown occurs, shutdownflag is loaded and making sure the shutdown is triggered and the manage the timeout
  (3) safe_path vs absolutepath -
      The use of absolute_path was insufficient, as it only checked if the path starts with the base directory, while some directory operations required a broader view (like safe_path ensuring the specificied root         directory works and getting it absolute path, if the root directory does not exist the server exits      
      
Status:
  The current implementation is functional but can be optimized by using threads instead of processes. This would enhance performance, especially for I/O-bound operations, by reducing process overhead and improving    concurrency. 
  All the commands interactively work between the client and the server
  







