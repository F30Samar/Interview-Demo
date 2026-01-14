# Name: Samar Gill
# Professor: Dr.Schwesinger
# Date: 12 Dec 2024
# Assignments: Client in Python(Group Project)
# Class: CPSC 328

from Utility import *
import time

# Global Variables
local_directory = get_dir()
remote_directory = None

##########################################################
# Function name: connect_to_server
# Description:  creates TCP socket to connect to server 
# Parameters: host (str) - host to connect to
#             port (int) - Port # to connect to
# Return Value: client_socket - connected Tcp socket
###########################################################
def connect_to_server(host, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, int(port)))
    except socket.error as e:
        print(f'Error connecting to server: {e}')
        exit(1)
    return client_socket

####################################################
# Function name: show-help()
# Description: Help text to run program commands
# Parameters: none
# Return Value: none
#####################################################
def show_help():
    help_text = '''
    Commands:
    exit            - Quit the application
    cd [path]       - Change remote directory
    get [-R] remote-path [local-path] - Retrieve remote file
    help            - Show this help text
    lcd [path]      - Change local directory
    lls [path]      - List local directory
    lmkdir path     - Create local directory
    lpwd            - Print local working directory
    ls [path]       - List remote directory
    mkdir path      - Create remote directory
    put [-R] local-path [remote-path] - Upload file
    pwd             - Show remote working directory
    '''
    print(help_text)

##################################################################################################
# Function name: handler(client_socket, command, path = None, recursion=False, response=None)
# Description: Handler function to handle sftp commands in a switch case
# Parameters: client_socket (socket) - socket used for client-server communication
#             command (str) - SFTP command to be processed
#             path (str) - The path for commands requiring file or directory, Default = none
#             recursion (bool) - indicates if recursion is needed for GET or PUT, Default = false
#             response (any) - response used during processing
# Return Value: response_pui (object) - The encapsulated response object from the server, 
#                                       depending on the command, or None if an error occurs.
######################################################################################################
def handler(client_socket, command, path=None, recursion=False, response=None):
    def handler_helper(action):       
        pui = PUI(action, path, recursion, response)
        send_message(client_socket, pui.encapsulate)

        client_socket.settimeout(5)  # 5 seconds timeout
        
        try:
            # Receive the message from the server
            response_pui = receive_message(client_socket, MAX_BUFFER_SIZE, pui.de_encapsulate)
        except socket.timeout:
            print("Error: Server did not respond in time.")
            return None  # or handle appropriately (e.g., return an error message)
        
        return response_pui        
        
    global local_directory
    global remote_directory

    match command: 
        case 'help':
            show_help()
        case 'exit':
            response_pui = handler_helper('EXIT')
            print("Exiting...")
            exit(0)
        case 'start':
            response_pui = handler_helper('START')
            if response_pui.action == 'DIR_CHANGED':
                remote_directory = response_pui.response
            elif response_pui.action == 'DIR_NOT_FOUND':
                raise FileNotFoundError
        case 'cd':
            response_pui = handler_helper('CD')
            if response_pui.action == 'DIR_CHANGED':
                remote_directory = response_pui.response
            elif response_pui.action == 'DIR_NOT_FOUND':
                raise FileNotFoundError
        case 'cd':
            response_pui = handler_helper('CD')
            if response_pui.action == 'DIR_CHANGED':
                remote_directory = response_pui.response
            elif response_pui.action == 'DIR_NOT_FOUND':
                raise FileNotFoundError        
        case 'ls':
            if path == None:
                path = remote_directory
            response_pui = handler_helper('LS')
            if response_pui.action == 'OK_LS':
                for file in response_pui.response:
                    print(file, end='    ')
                print()  
        case 'mkdir':
            response_pui = handler_helper('MAKE_DIR')
            if response_pui.action == 'DIR_EXIST':
                raise FileExistsError
        case 'put':
            files = upload_file(path, recursion)
            if response == None:
                path = Path(remote_directory)/'.'
            else:
                path = response
            response = files
            response_pui = handler_helper('PUT')
            if response_pui.action == 'DIR_EXIST':
                print(f"Error: Cannot create directory '{path}'.")
        case 'get':
            response_pui = handler_helper('GET', path)
            if response_pui.action == 'OK_GET':
                download_file(local_directory, response_pui.response)
                print("Download successful.")
        case 'pwd':
            print(remote_directory)
        case 'lcd':
            local_directory = change_dir(path, os.path.expanduser("~"))
        case 'lls':
            contents = directory_listing(path, local_directory)
            for file in contents:
                print(file, end='   ')
            print()  
        case 'lmkdir':
            print(create_dir(path))
        case 'lpwd':
            print(local_directory)
        case _:
            print('Invalid command. Type "help" for a list of commands.')
            
###########################################################################################
# Function name: run_repl(client_socket)
# Description: Implements a REPL (Read-Eval-Print Loop) to interact with the file client.
#              The REPL continuously processes user input, parses commands, and delegates
#              their execution to the `handler` function.
# Parameters:  client_socket: The socket object used to communicate with the server.
# Return Value: None
#############################################################################################
def run_repl(client_socket):

    handler(client_socket, 'start')

    while True:
        input_line = input(f'fileclient {remote_directory} > ').strip().split()
        input_length = len(input_line)
        if input_length > 0:
            command = input_line[0]
            path = input_line[1] if input_length > 1 else None
            recursion = True if '-R' in input_line else False
            response = input_line[-1] if len(input_line) > 2 and input_line[-1] != '-R' else None

            try:
                handler(client_socket, command, path, recursion, response)
            except FileNotFoundError:
                print(f"Error: Directory '{path}' not found.")
            except FileExistsError:
                print(f"Error: Cannot create directory '{path}'.")
            except InvalidAction as e:
                print(f"Error: {e}")
            except PacketIncomplete as e:
                print(f"Error: {e}")

#################################################
# Function name: main
# Description: Entry point for the client application. 
#              Parses arguments, connects to the server, and runs the REPL (Read-Eval-Print Loop).
# Parameters: None
# Return Value: None
##################################################
def main():
    # Parse arguments
    args = parse(False)

    # Connect to the server
    client_socket = connect_to_server('localhost', 2555)

    # Run the REPL
    run_repl(client_socket)

    # Close the socket when done
    client_socket.close()

if __name__ == "__main__":
    main()
