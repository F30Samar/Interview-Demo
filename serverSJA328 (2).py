#!/usr/bin/env python3

# Name: Anesu Mudzingwa
# Student ID: 002224572
# Date: 28 Nov 2024
# Assignment: Server in Python (Group Project)
# Class: CPSC 328

import os
import signal
import socket
import time
from Utility import *


root_directory = None  
current_directory = None  

connected_clients = []  # List of active client connections
TIMEOUT = 10  
shutdownflag = False  

#################################################
# Function name: est_socket
# Description:  Establishes and returns a server socket.
# Parameters: port - The port number to bind the server socket.
# Return Value: serverSocket - The created server socket object.
##################################################
def est_socket(port):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(('', int(port)))  # Bind to all available network interfaces
    serverSocket.listen(5)  # Listen for up to 5 simultaneous connections
    print(f"Server listening on port {port}...")
    return serverSocket

def server_business(connectionSocket):
    pui: PUI = PUI()
    pui = receive_message(connectionSocket, pui.de_encapsulate)

    action: str = pui.action
    path: str =  str(pui.path)
    recursive_flag: bool = pui.recursion
    response: list|dict = pui.response

    response_pui = handle_command(action, path, recursive_flag, response)
    
    send_message(connectionSocket, response_pui.encapsulate)


#################################################
# Function name: handle_command
# Description:  Processes client commands and generates appropriate responses.
# Parameters: 
#   command - The action requested by the client (e.g., CD, LS, etc.).
#   path - The target path for the command.
#   recursion - Whether the command should operate recursively.
#   response - Additional data associated with the command.
# Return Value: A PUI object containing the response to the client.
##################################################
def handle_command(command: str, path: str = None, recursion: bool = False, response: list | dict = None, root_directory: str = None) -> PUI:
    global current_directory

    try:

        if command != 'START':
            path = absolute_path(str(root_directory), path)
            if Path(path).name == 'None':
                    path = None

        match command:
            case 'START':
                current_directory = get_dir()
                return PUI(action='DIR_CHANGED', response=current_directory)
            case 'EXIT':
                return PUI(action='CLOSE')
            case 'CD':
                current_directory = change_dir(path, str(root_directory))
                return PUI(action='DIR_CHANGED', response=current_directory)
            case 'GET':
                files = upload_file(path, recursion)
                return PUI(action='OK_GET' , response=files)
            case 'PUT':                    
                download_file(path, response)
                return PUI(action='OK_PUT')
            case 'LS':
                contents = directory_listing(path, str(current_directory))
                return PUI(action='OK_LS', response=contents)
            case 'MAKE_DIR':
                create_dir(path)
                return PUI(action='DIR_CHANGED')
            case _:
                raise InvalidAction(f"Action not recognized")

    except ValueError:
        return PUI(action='ACCESS_DENIED', response="Access denied")
    except (FileNotFoundError, PermissionError):
        return PUI(action='DIR_NOT_FOUND', response=f"Error: Directory {path} not found")
    except FileExistsError:
        return PUI(action='DIR_EXIST', response=f"Error: Cannot create directory {path}.")
    except InvalidAction as e:
        return PUI(action='NO_COMMAND', response=str(e))
    except PacketIncomplete as e:
        return PUI(action='SEND_ERROR', response=f"Error: {e}")

#################################################
# Function name: parent_business
# Description:  Handles tasks in the parent process after forking.
# Parameters: 
#   pid - The process ID of the child.
#   child - Child process status.
#   connectionSocket - The socket connected to the client.
# Return Value: None
##################################################
def parent_business(pid, child):
    os.waitpid(pid, child)  # Wait for the child process to finish
    global shutdownflag 
    shutdownflag = True
    # Notify all connected clients of the impending shutdown
    for client in connected_clients:
        try:
            client.sendall(b"Server will be shutting down in 10 seconds.")
            signal.alarm(TIMEOUT)
        except Exception as e:
            print(f"Notification Error: {e}")

    # Close client sockets
    for client in connected_clients:
        try:
            client.close()
            print(f"Closed connection to client: {client}")
        except Exception as e:
            print(f"Error closing client socket: {e}")

#################################################
# Function name: signal_handler
# Description:  Handles the SIGINT signal (Ctrl+C) for graceful shutdown.
# Parameters: 
#   signum - The signal number.
#   frame - The current stack frame.
# Return Value: None
##################################################
def signal_handler(signum, frame):
    global shutdownflag
    print("Received SIGINT (Ctrl+C). Initiating shutdown...")
    shutdownflag = True
    for client in connected_clients:
        try:
            client.sendall(b"Server will be shutting down in 10 seconds.")
        except Exception as e:
            print(f"Error sending shutdown message: {e}")
    time.sleep(TIMEOUT)
    os._exit(0)

#################################################
# Function name: alm_handler
# Description:  Handles the SIGALRM signal for timeout-based shutdown.
# Parameters: 
#   signum - The signal number.
#   frame - The current stack frame.
# Return Value: None
##################################################
def alm_handler(signum, frame):
    print("SIGALRM received: Timeout expired for shutdown warning.")

#################################################
# Function name: main
# Description:  Main function to start the server and handle connections.
# Parameters: None
# Return Value: None
##################################################
def main():
    args = parse(True)  # Parse command-line arguments
    serverSocket = est_socket(args.port)  # Establish server socket

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGALRM, alm_handler)

    try:
        while True:
            while not shutdownflag:
                # Accept a new client connection
                connectionSocket, address = serverSocket.accept()
                connected_clients.append(connectionSocket)
                print(f"Connection established with {address}")

                pid = os.fork()  # Create a new process for each client
                if pid == 0:
                    # Child process handles client communication
                    server_business(connectionSocket,args.directory)
                    os._exit(0)
                elif pid > 0:
                    # Parent process continues to listen for new connections
                    parent_business(pid, 0, connectionSocket)
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Shutting down...")
        exit(0)
    finally:
        # Close the server socket when shutting down
        serverSocket.close()

#################################################
# Function name: parent_business
# Description: Handles tasks in the parent process, including managing child processes and notifying clients of shutdown.
# Parameters: 
#   - pid (int): Process ID of the child process.
#   - child (int): Options for waiting on child processes (e.g., 0 for immediate return).
#   - connectionSocket (socket): Socket connection to the client.
# Return Value: None
#################################################
def parent_business(pid, child, connectionSocket):
    os.waitpid(pid, child)# Parent process: Wait for the child process to finish
    global shutdownflag 
    shutdownflag = True
    for client in connected_clients:
        try:
            connectionSocket.sendall("Server will be shutting down in 10 seconds.".encode())#Announcement to every client
            signal.alarm(TIMEOUT)
        except:
            pass

    for client in connected_clients:
        try:
            connectionSocket.close()
            print(f'{str(client)} socket closed\n')
        except:
            pass

#################################################
# Function name: signal_handler
# Description: Handles the SIGINT signal (Ctrl+C) to initiate server shutdown and notify all connected clients.
# Parameters: 
#   - signum (int): Signal number (e.g., SIGINT).
#   - frame (frame): Current stack frame (not used in this function).
# Return Value: None
#################################################
def signal_handler(signum, frame):
    # Handle SIGINT (Ctrl+C) for hutdown
    global shutdownflag
    print('Received CTRL+C Signal. Initiating shutdown...')
    shutdownflag = True
    # Broadcast shutdown message to all clients
    for client in connected_clients:
        try:
            client.sendall("Server will be shutting down in 10 seconds.".encode())
        except Exception as e:
            print(f"Error sending shutdown message: {e}")
    time.sleep(TIMEOUT)

#################################################
# Function name: alm_handler
# Description: Handles the SIGALRM signal to send shutdown warnings to all connected clients.
# Parameters: 
#   - signum (int): Signal number (e.g., SIGALRM).
#   - frame (frame): Current stack frame (not used in this function).
# Return Value: None
#################################################
def alm_handler(signum, frame):
    # Handle SIGALRM for sending shutdown warning to clients
    global shutdownflag
    print('SIGALRM received: Sending shutdown warning to all clients...')
    shutdownflag = True
    for client in connected_clients:
        try:
            client.sendall("Server will be shutting down in 10 seconds.".encode())
        except Exception as e:
            print(f"Error sending alarm message: {e}")


if __name__ == '__main__':
    main()