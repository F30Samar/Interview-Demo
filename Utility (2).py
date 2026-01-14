# Name: Justin Nunez
# Professor: Dr.Schwesinger
# Date: 12 Dec 2024
# Assignments: Utility in Python(Group Project)
# Class: CPSC 328

import pickle
import argparse 
import os
import socket
from pathlib import Path 

MAX_BUFFER_SIZE = 1024
MAX_4_BYTES = 2**32 - 1

# Const that contains all the possibles status codes
STATUS_CODES = ('START',
                'CD', 'DIR_CHANGED', 'DIR_NOT_FOUND',
                'LS', 'OK_LS', 'DIR_NOT_FOUND',
                'MAKE_DIR', 'DIR_EXIST',
                'GET', 'OK_GET', 'DIR_NOT_FOUND', 
                'PUT', 'OK_PUT', 'NOT_PATH', 'DIR_EXIST')

# Custom Exception to be used only for the PUI class
class InvalidAction(Exception):
    pass

class PacketIncomplete(Exception):
    pass


class PUI():
    #################################################
    # Function name: PUI.__init__
    # Description: Initializes the PUI (Protocol Unit Information) class with action, path, recursion, and response attributes.
    # Parameters: 
    #   - action (str): Action to be performed.
    #   - path (str): File or directory path.
    #   - recursion (bool): Flag to indicate recursion for file operations.
    #   - response (list|dict): The response from the server/client.
    # Return Value: None
    ##################################################
    def __init__(self, action: str = None, path: str = None, recursion: bool = False, response: list|dict = None):
        self.action = action
        self.path = path
        self.recursion = recursion
        self.response = response
    
    #################################################
    # Function name: PUI.serialize
    # Description: Serializes the PUI instance to a byte stream using pickle.
    # Parameters: None
    # Return Value: bytes (Serialized PUI object)
    ##################################################
    def serialize(self) -> bytes: 
        return pickle.dumps(self)
    
    #################################################
    # Function name: PUI.serialize_length
    # Description: Returns the length of the serialized message, including the protocol closing characters.
    # Parameters: 
    #   - message (bytes): The serialized message to compute the length.
    # Return Value: int (Length of the serialized message with closing characters)
    ##################################################
    def serialize_length(self, message: bytes) -> int:
        return (len(message) + 2)
    
    #################################################
    # Function name: PUI.create_packet
    # Description: Creates a packet with a message length (4 bytes) and a serialized message, followed by protocol closing characters.
    # Parameters:
    #   - message_length (int): Length of the serialized message.
    #   - message (bytes): The serialized message.
    # Return Value: bytes (The packet ready to be sent)
    ##################################################   
    def create_packet(self) -> bytes:
        message = self.serialize()
        message_length = self.serialize_length(message)
        message_length = message_length.to_bytes(length=4, byteorder='big')
        return (message_length + message) + '\r\n'.encode()
    
    #################################################
    # Function name: PUI.encapsulate
    # Description: Encapsulates the PUI instance into a series of packets, ensuring the message length does not exceed the maximum allowed.
    # Parameters: None
    # Return Value: list (List of byte packets)
    ##################################################  
    def encapsulate(self):
        if self.action not in STATUS_CODES:
            raise InvalidAction(f'Action not recognized')
        
        return self.create_packet() 

    #################################################
    # Function name: PUI.de_encapsulate
    # Description: Decapsulates a list of byte packets into a PUI instance by checking packet integrity and reconstructing the message.
    # Parameters:
    #   - packets (list): List of packets to be decoded into a PUI instance.
    # Return Value: PUI (A PUI instance with the reconstructed data)
    ##################################################  
    def de_encapsulate(self, packet: bytes):
        # Check the packet integrity (to see if its complete) 
        def check_ending(byte_stream: bytes):
            if byte_stream[-2:] != b'\r\n' and length == self.serialize_length(packet[:-2]):
                raise PacketIncomplete('Packet is not complete')
            return byte_stream[:-2]

        message = b''
        length = int.from_bytes(packet[:4], byteorder='big') 
        message += check_ending(packet[4:])
            
        return pickle.loads(message)

#################################################
# Function name: receive_message
# Description: Receives a message from the connection socket, decapsulates it, and returns a PUI instance with the server/client response.
# Parameters: 
#   - connection_socket (socket): The socket connection to receive data from.
#   - length (int): The expected length of the message.
#   - de_encapsulate (function): The de-encapsulation function from the PUI class to convert the byte stream into a PUI instance.
# Return Value: PUI (The PUI instance with the server/client response)
##################################################
def receive_message(connection_socket: socket, de_encapsulate: PUI.de_encapsulate) -> PUI:
    length_data = connection_socket.recv(4)
    length = int.from_bytes(length_data, byteorder='big')

    buffer = b''
    while len(buffer) < length:
        chunk = connection_socket.recv(length - len(buffer))
        if not chunk:
            break 
        buffer += chunk

    buffer = length_data + buffer

    return de_encapsulate(buffer)


#################################################
# Function name: send_message
# Description: Sends a list of encapsulated PUI packets over the given connection socket.
# Parameters: 
#   - connection_socket (socket): The socket connection to send the data through.
#   - encapsulate (function): The encapsulate function from the PUI class to convert a PUI instance into byte packets.
# Return Value: None
##################################################
def send_message(connection_socket: socket, encapsulate : PUI.encapsulate) -> None:
    packets = encapsulate()
    connection_socket.sendall(packets)

#################################################
# Function name: parse
# Description: Parses command-line arguments for either the server or client application based on the mode.
# Parameters:
#   - mode (bool): True for server mode, False for client mode.
# Return Value: argparse.Namespace (Parsed command-line arguments)
##################################################
def parse(mode: bool = True) -> argparse.Namespace:

    args = None

    def client():
        nonlocal args
        parser = argparse.ArgumentParser(description='File client application', add_help=False)
        parser.add_argument('-h', '--host', required=True, help='Host address of the server')
        parser.add_argument('-p', '--port', required=True, help='Port number of the server')
        args = parser.parse_args()
    
    def server():
        nonlocal args
        parser = argparse.ArgumentParser(description="File server application")
        parser.add_argument('-p', '--port', required=True, help="Port number for the server")
        parser.add_argument('-d', '--directory', required=True, help="Directory to serve files from")
        args = parser.parse_args()

    if mode:
        server()
    else:
        client()
    return args

#################################################
# Function name: absolute_path
# Description: Resolves the absolute path of a given relative or absolute path and ensures it lies within a specified root directory.
# Parameters:
#   - root_path (str): The root directory path.
#   - path (str): The relative or absolute path to resolve.
# Return Value: str (Absolute path of the given path if it lies within the root path; raises FileNotFoundError otherwise)
##################################################
def absolute_path(root_path: str, path: str) -> str: #May raise InvalidPath
    client_path = os.path.abspath(path)
    if client_path.startswith(root_path):
        return client_path
    else:
        raise FileNotFoundError

#################################################
# Function name: get_dir
# Description: Returns the current working directory.
# Parameters: None
# Return Value: Path (Current working directory)
##################################################
def get_dir() -> Path:
    return Path.cwd()

#################################################
# Function name: change_dir
# Description: Changes the current directory to the specified path, or to the root path if no path is specified.
# Parameters:
#   - path (str): The path to change the current directory to.
#   - root_path (str): The root directory path to use if no path is specified.
# Return Value: Path (The new current working directory)
##################################################
def change_dir(path: str, root_path: str) -> Path:
    if path == None:
        path = root_path
    os.chdir(path)
    return get_dir()

#################################################
# Function name: directory_listing
# Description: Lists all elements (files and directories) inside a given path, or in the current directory if no path is specified.
# Parameters:
#   - path (str): The path to list the contents of.
#   - current_path (str): The current directory path if no path is specified.
# Return Value: list (List of files and directories in the specified path)
##################################################
def directory_listing(path: str, current_path: str) -> list:
    if path == None:
            path = current_path
    return os.listdir(path)

#################################################
# Function name: create_dir
# Description: Creates a directory at the specified path and returns a string indicating if the directory was created or not.
# Parameters:
#   - path (str): The path to create the directory at.
#   - recursion (bool): Whether to create parent directories if they don't exist.
# Return Value: str (A message indicating whether the directory was created or not)
##################################################
def create_dir(path: str, recursion: bool = False) -> str:
    if path == None:
        return('lmkdir: missing operand')
    path: Path = Path(path)
    path.mkdir(parents = recursion, exist_ok = recursion)
    return(f'{path}: created')

#################################################
# Function name: upload_file
# Description: Uploads files and directories from the given absolute path, optionally including subdirectories if recursion is enabled.
# Parameters:
#   - absolute_upload_path (str): The absolute path to the files and directories to upload.
#   - recursion (bool): Whether to include subdirectories in the upload.
# Return Value: dict (A dictionary containing lists of directories, file names, and their byte streams)
##################################################
def upload_file(absolute_upload_path: str, recursion: bool) -> dict:
    def check_path(path):
        if path.is_dir():
                upload_stream['directories'].append(path.relative_to(absolute_upload_path))
        elif path.is_file():
                file_name = path.relative_to(absolute_upload_path) 
                if file_name == Path('.'):
                    file_name = path.name
                upload_stream['file_names'].append(file_name)
                upload_stream['file_byte_stream'].append(read_file(path))

    upload_stream: dict = {'directories':[], 'file_names':[], 'file_byte_stream':[]}
    path_to_upload: Path = Path(absolute_upload_path)

    if recursion:
        path_to_upload = path_to_upload.rglob('**')
        for item in path_to_upload:
            check_path(item)
    else:
        check_path(path_to_upload)

    return upload_stream

#################################################
# Function name: download_file
# Description: Downloads files and directories to the specified absolute path based on the provided contents dictionary.
# Parameters:
#   - absolute_download_path (str): The path to download the files to.
#   - contents (dict): A dictionary containing lists of directories, file names, and their byte streams to download.
# Return Value: None
################################################
def download_file(absolute_download_path: str, contents: dict) -> None:
    path_to_download = Path(absolute_download_path)
    for key in contents.keys():
        if key == 'directories':
            for dir in contents[key]:
                create_dir(path_to_download/dir, True) 
        elif key == 'file_names':
            for file, byte_stream in zip(contents[key],contents['file_byte_stream']):
                write_file(path_to_download/file, byte_stream)

#################################################
# Function name: read_file
# Description: Reads a file from the specified path and returns its byte stream.
# Parameters:
#   - file_path (str): The path to the file to read.
# Return Value: bytes (The byte stream of the file contents)
##################################################
def read_file(file_path: str) -> bytes:
    with open(file_path, 'rb') as file:
        byte_stream = file.read()
    return byte_stream

#################################################
# Function name: write_file
# Description: Writes the given byte stream to a file at the specified path.
# Parameters:
#   - file_path (str): The path to the file to write to.
#   - content (bytes): The byte stream to write to the file.
# Return Value: None
##################################################
def write_file(file_path: str, content: bytes) -> None:
    with open(file_path, 'wb') as file:
        file.write(content)
