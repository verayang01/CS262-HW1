import socket
import threading
import json
import os

USER_DATA_FILE = "accounts.json"


class Server:
    """
    A multi-client chat server using a custom wire protocol over sockets.
    """
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

    def handle_client(self, client):
        """
        Handles communication with a connected client.
        
        Args:
            client (socket): The client socket.
        """
        while True:
            message = client.recv(1024).decode('utf-8')
            if not message: # check if there is message
                break
            data = json.loads(message)

            # Handle different operations
            # Login
            if data['action'] == 'login':
                username = data['username']
                password = data['password']
                if username in self.accounts: # check if account  exists
                    if self.accounts[username]['password'] == password: # check if password correct
                        client.send(json.dumps({'status': 'success'}).encode('utf-8'))
                    else:
                        client.send(json.dumps({'status': 'failure'}).encode('utf-8'))
                else: # if account does not exist, create new account
                    self.accounts[username] = {'password': password, 'read_messages': [], 'unread_messages': []}
                    self.save_accounts(self.accounts)
                    client.send(json.dumps({'status': 'success', 'unread_messages': []}).encode('utf-8'))

            # Send a message
            elif data['action'] == 'send':
                recipient = data['recipient']
                if recipient in self.accounts: # check if recipient is a valid account
                    # save message to recipient's undelivered messages
                    self.accounts[recipient]['unread_messages'].append({"from": data['sender'], "message": data['message']})
                    self.save_accounts(self.accounts)
                    client.send(json.dumps({'status': 'success', 'message': 'Send message successfully.'}).encode('utf-8'))
                else:
                    client.send(json.dumps({'status': 'failure', 'message': 'Invalid recipient. Please enter a valid username.'}).encode('utf-8'))
            
            # Read unread (undelivered) messaages
            elif data['action'] == 'read_unread':
                username = data['username']
                per_page = data['per_page'] # the number of messages user wants to read
                unread_messages = self.accounts[username]['unread_messages'][:per_page]

                # move messages from unread messages to read messages
                self.accounts[username]['read_messages'].extend(unread_messages)
                self.accounts[username]['unread_messages'] = self.accounts[username]['unread_messages'][per_page:]
                self.save_accounts(self.accounts)

                client.send(json.dumps({'status': 'success', 'messages': unread_messages}).encode('utf-8'))

            # Read all (delivered) messages
            elif data['action'] == 'read_all':
                username = data['username']
                messages = self.accounts[username]['read_messages']

                client.send(json.dumps({'status': 'success', 'messages': messages}).encode('utf-8'))

            # Count unread messages
            elif data['action'] == "count_unread":
                username = data['username']

                client.send(json.dumps({'status': 'success', 'unread_messages': self.accounts[username]['unread_messages']}).encode('utf-8'))
            
            # List accounts
            elif data['action'] == "list":
                query = data['query'].lower() # query for searching accounts
                accounts = list(self.accounts.keys())
                searched_accounts = [acc for acc in accounts if query in acc.lower()] # accounts that contain query

                client.send(json.dumps({'status': 'success', 'list_accounts': searched_accounts}).encode('utf-8'))
            
            # Delete message
            elif data['action'] == "delete_message":
                username = data['username']
                idx = data['idx'] # index of message the user wants to delete
                del self.accounts[username]["read_messages"][idx] # delete message
                self.save_accounts(self.accounts)

                client.send(json.dumps({'status': 'success'}).encode('utf-8'))
            
            # Delete account
            elif data['action'] == "delete_account":
                username = data['username']

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

                client.send(json.dumps({'status': 'success'}).encode('utf-8'))

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
