import socket
import threading
import json # only use json for data storage
import os
from protocol import serialize, deserialize
from operation import Operations

USER_DATA_FILE = "accounts.json"


class Server:
    """
    A multi-client chat server using a custom wire protocol over sockets.
    """
    HEADER = 64 # size of message that indicates the next message size
    VERSION = "1" # protocal version number

    def __init__(self, host='0.0.0.0', port=5555):
        """
        Initializes the server.
        
        Args:
            host (str): The IP address to bind the server to.
            port (int): The port to listen on.
        """
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()
        self.accounts = self.load_accounts()
        self.lock = threading.Lock()
    
    # Load accounts from JSON
    def load_accounts(self):
        """
        Loads user accounts from a JSON file.
        
        Returns:
            dict: A dictionary containing user accounts.
        """
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, "r") as file:
                return json.load(file)
        return {}

    # Save accounts to JSON
    def save_accounts(self, accounts):
        """
        Saves user accounts to a JSON file.
        
        Args:
            accounts (dict): The accounts data to save.
        """
        with open(USER_DATA_FILE, "w") as file:
            json.dump(accounts, file, indent=4)
    
    def package_send(self, send_data, client):
        """
        Serializes and sends data to the client.
        
        Args:
            send_data (dict): The data to be sent.
            client (socket): The client socket.
        """
        serialized_data = serialize(send_data)
        msg_len = len(serialized_data)
        send_len = str(msg_len).encode('utf-8')
        send_len += b" " * (self.HEADER - len(send_len))

        client.send(send_len) # first send the length of message to be sent
        client.send(serialized_data) 

    def handle_client(self, client):
        """
        Handles communication with a connected client.
        
        Args:
            client (socket): The client socket.
        """
        connection_flag = True
        while connection_flag:
            msg_len = client.recv(self.HEADER).decode('utf-8') 
            if not msg_len: # check if there is message
                break
            msg_len = int(msg_len)
            deserialized_data = deserialize(client.recv(msg_len)) 

            # Check version
            recv_version = deserialized_data["version"]
            if recv_version != self.VERSION:
                print("Incorrect version.")
                connection_flag = False
            operation = deserialized_data["operation"]
            info = deserialized_data["info"]

            # Handle different operations
            # Login
            if operation == Operations.LOGIN: 
                data = info.split('\n', 1)
                username = data[0]
                password = data[1]
                if username in self.accounts: # check if account  exists
                    if self.accounts[username]['password'] == password: # check if password correct
                        send_data = {'version': self.VERSION, 'operation': Operations.SUCCESS, 'info': ''}
                        self.package_send(send_data, client)
                    else: 
                        send_data = {'version': self.VERSION, 'operation': Operations.FAILURE, 'info': ''}
                        self.package_send(send_data, client)
                else: # if account does not exist, create new account
                    self.accounts[username] = {'password': password, 'read_messages': [], 'unread_messages': []}
                    self.save_accounts(self.accounts)
                    send_data = {'version': self.VERSION, 'operation': Operations.SUCCESS, 'info': ''}
                    self.package_send(send_data, client)

            # Send a message
            elif operation == Operations.SEND_MESSAGE:
                data = info.split('\n', 2)
                sender = data[0]
                recipient = data[1]
                send_message = data[2]
                if recipient in self.accounts: # check if recipient is a valid account
                    # save message to recipient's undelivered messages
                    self.accounts[recipient]['unread_messages'].append({"from": sender, "message": send_message})
                    self.save_accounts(self.accounts)
                    message = 'Send message successfully.'
                    send_data = {'version': self.VERSION, 'operation': Operations.SUCCESS, 'info': message}
                    self.package_send(send_data, client)
                else:
                    message = 'Invalid recipient. Please enter a valid username.'
                    send_data = {'version': self.VERSION, 'operation': Operations.FAILURE, 'info': message}
                    self.package_send(send_data, client)
         
            # Read unread (undelivered) messaages
            elif operation == Operations.READ_UNREAD:
                data = info.split('\n', 1)
                username = data[0]
                per_page = int(data[1]) # the number of messages user wants to read
                unread_messages = self.accounts[username]['unread_messages'][:per_page]

                # move messages from unread messages to read messages
                self.accounts[username]['read_messages'].extend(unread_messages)
                self.accounts[username]['unread_messages'] = self.accounts[username]['unread_messages'][per_page:]
                self.save_accounts(self.accounts)

                message = "\n\t\n".join(f"{msg['from']} {msg['message']}" for msg in unread_messages)
                send_data = {'version': self.VERSION, 'operation': Operations.SUCCESS, 'info': message}
                self.package_send(send_data, client)

            # Read all (delivered) messages
            elif operation == Operations.READ_ALL:
                username = info
                read_messages = self.accounts[username]['read_messages']

                message = "\n\t\n".join(f"{msg['from']} {msg['message']}" for msg in read_messages)
                send_data = {'version': self.VERSION, 'operation': Operations.SUCCESS, 'info': message}
                self.package_send(send_data, client)

            # Count unread messages
            elif operation == Operations.COUNT_UNREAD:
                username = info
                message = "\n\t\n".join(f"{msg['from']} {msg['message']}" for msg in self.accounts[username]['unread_messages'])
                send_data = {'version': self.VERSION, 'operation': Operations.SUCCESS, 'info': message}
                self.package_send(send_data, client)

            # List accounts
            elif operation == Operations.LIST_ACCOUNTS:
                data = info.split('\n', 1)
                query = data[1] # query for searching accounts
                accounts = list(self.accounts.keys())
                searched_accounts = [acc for acc in accounts if query in acc.lower()] # accounts that contain query

                message = "\n".join(user for user in searched_accounts)
                send_data = {'version': self.VERSION, 'operation': Operations.SUCCESS, 'info': message}
                self.package_send(send_data, client)

            # Delete message
            elif operation == Operations.DELETE_MESSAGE:
                data = info.split('\n', 1)
                username = data[0]
                idx = int(data[1]) # index of message the user wants to delete
                del self.accounts[username]["read_messages"][idx] # delete message
                self.save_accounts(self.accounts)

                send_data = {'version': self.VERSION, 'operation': Operations.SUCCESS, 'info': ''}
                self.package_send(send_data, client)

            # Delete account
            elif operation == Operations.DELETE_ACCOUNT:
                username = info

                # delete all messages sent from this accounts, so that the recipients will no longer see these messages
                for user in self.accounts:
                    i_un = len(self.accounts[user]['unread_messages'])-1
                    for un_m in self.accounts[user]['unread_messages'][::-1]:
                        if un_m['from'] == username:
                            del self.accounts[user]['unread_messages'][i_un]
                        i_un -= 1
                    i_r = len(self.accounts[user]['read_messages'])-1
                    for r_m in self.accounts[user]['read_messages'][::-1]:
                        if r_m['from'] == username:
                            del self.accounts[user]['read_messages'][i_r]
                        i_r -= 1
                del self.accounts[username] # delete account
                self.save_accounts(self.accounts)

                send_data = {'version': self.VERSION, 'operation': Operations.SUCCESS, 'info': ''}
                self.package_send(send_data, client)

    def start(self):
        """
        Starts the server and listens for incoming client connections.
        """
        while True:
            client, address = self.server.accept()
            print(f"Connected with {str(address)}")
            threading.Thread(target=self.handle_client, args=(client,)).start()

if __name__ == "__main__":
    import configparser
    config = configparser.ConfigParser()
    config.read('config.ini')
    host = config['server']['host']
    port = int(config['server']['port'])
    server = Server(host, port)
    server.start()
