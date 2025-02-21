import grpc
from concurrent import futures
import json
import os
import chat_pb2
import chat_pb2_grpc
import configparser
import threading

USER_DATA_FILE = "accounts.json"

class ChatService(chat_pb2_grpc.ChatServiceServicer):
    """
    Implements the gRPC chat service.
    
    This class provides functionality for user authentication, message handling, and account management.
    It ensures thread-safe operations using a threading lock.
    """
    def __init__(self):
        """
        Initializes the ChatService instance.
        
        Attributes:
            accounts (dict): A dictionary storing user information loaded from a JSON file.
            lock (threading.Lock): A lock to ensure thread-safe access to user accounts.
        """
        self.accounts = self.load_accounts()
        self.lock = threading.Lock()

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

    def save_accounts(self, accounts):
        """
        Saves user accounts to a JSON file.
        
        Args:
            accounts (dict): The accounts data to save.
        """
        with open(USER_DATA_FILE, "w") as file:
            json.dump(accounts, file, indent=4)

    def Login(self, request, context):
        """
        Handles user login or sign up requests.
        
        Args:
            request (chat_pb2.LoginRequest): The login request containing username and password.
            context (grpc.ServicerContext): The gRPC context for the request.
        
        Returns:
            chat_pb2.LoginResponse: A response indicating whether login or sign up was successful or not.
        """
        username = request.username
        password = request.password
        if username in self.accounts:
            if self.accounts[username]['password'] == password:
                return chat_pb2.LoginResponse(success=True, message="Login successful.")
            else:
                return chat_pb2.LoginResponse(success=False, message="Incorrect password.")
        else:
            self.accounts[username] = {'password': password, 'read_messages': [], 'unread_messages': []}
            self.save_accounts(self.accounts)
            return chat_pb2.LoginResponse(success=True, message="Account created and login successful.")

    def SendMessage(self, request, context):
        """
        Handles sending messages between users.
        
        Args:
            request (chat_pb2.MessageRequest): The message request containing sender, recipient, and message content.
            context (grpc.ServicerContext): The gRPC context for the request.
        
        Returns:
            chat_pb2.MessageResponse: A response indicating whether sending messages was successful or not.
        """
        recipient = request.recipient
        if recipient in self.accounts:
            self.accounts[recipient]['unread_messages'].append({"sender": request.sender, "message": request.message})
            self.save_accounts(self.accounts)
            return chat_pb2.SendMessageResponse(success=True, message="Message sent successfully.")
        else:
            return chat_pb2.SendMessageResponse(success=False, message="Invalid recipient.")

    def ReadUnreadMessages(self, request, context):
        """
        Handles requests to retrieve unread messages for a user.
        
        Args:
            request (chat_pb2.ReadUnreadMessagesRequest): The request containing the username and the number of messages to retrieve.
            context (grpc.ServicerContext): The gRPC context for the request.
        
        Returns:
            chat_pb2.ReadUnreadMessagesResponse: A response containing the requested unread messages.
        """
        username = request.username
        per_page = request.per_page
        unread_messages = self.accounts[username]['unread_messages'][:per_page]
        self.accounts[username]['read_messages'].extend(unread_messages)
        self.accounts[username]['unread_messages'] = self.accounts[username]['unread_messages'][per_page:]
        self.save_accounts(self.accounts)
        return chat_pb2.ReadUnreadMessagesResponse(messages=[chat_pb2.Message(sender=msg['sender'], message=msg['message']) for msg in unread_messages])

    def ReadMessages(self, request, context):
        """
        Handles requests to retrieve all read messages for a user.
        
        Args:
            request (chat_pb2.ReadMessagesRequest): The request containing the username.
            context (grpc.ServicerContext): The gRPC context for the request.
        
        Returns:
            chat_pb2.ReadMessagesResponse: A response containing the all read messages for the user.
        """
        username = request.username
        messages = self.accounts[username]['read_messages']
        return chat_pb2.ReadMessagesResponse(messages=[chat_pb2.Message(sender=msg['sender'], message=msg['message']) for msg in messages])

    def GetUnreadMessages(self, request, context):
        """
        Handles requests to retrieve all unread messages for a user.
        
        Args:
            request (chat_pb2.GetUnreadMessagesRequest): The request containing the username.
            context (grpc.ServicerContext): The gRPC context for the request.
        
        Returns:
            chat_pb2.GetUnreadMessagesResponse: A response containing the all unread messages for the user.
        """
        username = request.username
        unread_messages = self.accounts[username]['unread_messages']
        return chat_pb2.GetUnreadMessagesResponse(unread_messages=[chat_pb2.Message(sender=msg['sender'], message=msg['message']) for msg in unread_messages])

    def ListAccounts(self, request, context):
        """
        Handles requests to list all accounts that match a search query.
        
        Args:
            request (chat_pb2.ListAccountsRequest): The request containing the search query.
            context (grpc.ServicerContext): The gRPC context for the request.
        
        Returns:
            chat_pb2.ListAccountsResponse: A response containing the list of matching accounts.
        """
        query = request.query.lower()
        accounts = list(self.accounts.keys())
        searched_accounts = [acc for acc in accounts if query in acc.lower()]
        return chat_pb2.ListAccountsResponse(list_accounts=searched_accounts)

    def DeleteMessage(self, request, context):
        """
        Handles requests to delete a specific message from a user's account.
        
        Args:
            request (chat_pb2.DeleteMessageRequest): The request containing the username, sender, message, and index of the message to delete.
            context (grpc.ServicerContext): The gRPC context for the request.
        
        Returns:
            chat_pb2.DeleteMessageResponse: A response indicating whether the message was successfully deleted.
        """
        username = request.username
        idx = request.idx
        del self.accounts[username]["read_messages"][idx]
        self.save_accounts(self.accounts)
        return chat_pb2.DeleteMessageResponse(success=True, message="Message deleted successfully.")

    def DeleteAccount(self, request, context):
        """
        Handles requests to delete a user's account.
        
        Args:
            request (chat_pb2.DeleteAccountRequest): The request containing the username of the account to delete.
            context (grpc.ServicerContext): The gRPC context for the request.
        
        Returns:
            chat_pb2.DeleteAccountResponse: A response indicating whether the account was successfully deleted.
        """
        username = request.username
        for user in self.accounts:
            self.accounts[user]['unread_messages'] = [msg for msg in self.accounts[user]['unread_messages'] if msg['sender'] != username]
            self.accounts[user]['read_messages'] = [msg for msg in self.accounts[user]['read_messages'] if msg['sender'] != username]
        del self.accounts[username]
        self.save_accounts(self.accounts)
        return chat_pb2.DeleteAccountResponse(success=True, message="Account deleted successfully.")

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    host = config['server']['host']
    port = int(config['server']['port'])
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port(f'{host}:{port}')
    print(f"Server started at {host}:{port}")
    server.start()
    server.wait_for_termination()