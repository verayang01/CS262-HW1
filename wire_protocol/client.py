import socket
import tkinter as tk
from tkinter import messagebox
import hashlib
from protocol import serialize, deserialize
from operation import Operations

class Client:
    """
    A client for a chat application, handling communication with the server.
    """
    HEADER = 64 # size of message that indicates the next message size
    VERSION = "1" # protocal version number

    def __init__(self, host='127.0.0.1', port=5555):
        """
        Initializes the Client instance and establishes a connection to the server.
        
        Args:
            host (str): The server's hostname or IP address.
            port (int): The port number to connect to.
        """
        self.host = host
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))
        self.username = None

    def send_recv(self, operation, msg):
        """
        Sends a serialized request to the server and receives a response.
        
        Args:
            operation (str): A two-character operation code.
            msg (str): The message to be sent.
        
        Returns:
            dict: The deserialized response from the server.
        """
        serialized_data = serialize({"version": self.VERSION, "operation": operation, "info": msg}) # the message to be sent
        msg_len = len(serialized_data)
        
        send_len = str(msg_len).encode('utf-8') # length of message to be sent
        send_len += b" " * (self.HEADER - len(send_len)) # padding of message size

        self.client.send(send_len) # send message length
        self.client.send(serialized_data) # send message

        msg_len = self.client.recv(self.HEADER).decode('utf-8') 
        connection_flag = True
        while connection_flag: 
            if msg_len:
                msg_len = int(msg_len)
            else:
                msg_len = 1
            returned_data = self.client.recv(msg_len) # receive message with length=msg_len
            if len(returned_data): # if there is message
                deserialized_data = deserialize(returned_data) # deserialize data
                if deserialized_data["version"] == self.VERSION: # check version
                    return deserialized_data
                else:
                    print("Incorrect version.")
                    connection_flag = False
            else:
                print("No returned message from server.")
                return

    def send_message(self, recipient, message):
        """
        Sends a send message request to server and get response.
        
        Args:
            recipient (str): The recipient's username.
            message (str): The message content to be sent. 
        
        Returns:
            tuple: A boolean indicating success, and the server's response message.
        """
        info = self.username + '\n' + recipient + '\n' + message # encode info sent to server
        response = self.send_recv(Operations.SEND_MESSAGE, info)
        if response['operation'] == Operations.SUCCESS:
            return True, response['info']
        else:
            return False, response['info']

    def read_unread_messages(self, per_page):
        """
        Send a retrieve unread (undelivered) messages to server and get response.
        
        Args:
            per_page (int): The number of messages to retrieve.
        
        Returns:
            list: A list of unread messages, each represented as a dictionary.
        """
        info = self.username + '\n' + str(per_page) # encode info sent to server
        response = self.send_recv(Operations.READ_UNREAD, info) 
        if response['operation'] == Operations.SUCCESS:
            unread_messages = []
            if response['info'] == '':
                return unread_messages
            for line in response['info'].split("\n\t\n"): # split each unread message, each in the format "sender message"
                sender, message = line.split(" ", 1) # separate sender and message
                unread_messages.append({"from": sender, "message": message})
            return unread_messages
        else:
            messagebox.showerror("Error", "Failed to read messages.")
            return []
    
    def read_messages(self):
        """
        Send a retrieve read (delivered) messages to server and get response.
        
        Returns:
            list: A list of read messages, each represented as a dictionary.
        """
        info = self.username
        response = self.send_recv(Operations.READ_ALL, info)
        if response['operation'] == Operations.SUCCESS:
            read_messages = []
            if response['info'] == '':
                return read_messages
            for line in response['info'].split("\n\t\n"): # split each unread message, each in the format "sender message"
                sender, message = line.split(" ", 1) # separate sender and message
                read_messages.append({"from": sender, "message": message})
            return read_messages
        else:
            messagebox.showerror("Error", "Failed to read messages.")
            return []

    def get_unread(self):
        """
        Reqeust to retrieve a list of unread messages for the current user from server and get response. 
        
        Returns:
            list: A list of unread messages, each represented as a dictionary.
        """
        info = self.username
        response = self.send_recv(Operations.COUNT_UNREAD, info)
        if response['operation'] == Operations.SUCCESS:
            unread_messages = []
            if response['info'] == '':
                return unread_messages
            for line in response['info'].split("\n\t\n"): # split each unread message, each in the format "sender message"
                sender, message = line.split(" ", 1) # separate sender and message
                unread_messages.append({"from": sender, "message": message})
            return unread_messages
        else:
            messagebox.showerror("Error", "Failed to get unread messages.")
            return []
        
    def login(self, username, password):
        """
        Request to authenticate the user with the provided credentials and get response from server.
        
        Args:
            username (str): The username of the account.
            password (str): The password for authentication.
        
        Returns:
            bool: True if login was successful, False otherwise.
        """
        info = username + '\n' + password # encode info sent to server
        response = self.send_recv(Operations.LOGIN, info)
        if response['operation'] == Operations.SUCCESS:
            self.username = username
            return True
        else:
            return False
    
    def list_accounts(self, query):
        """
        Request to retrieve a list of accounts that match the query from server and get response. 
        
        Args:
            query (str): The search query to filter accounts.
        
        Returns:
            list: A list of usernames matching the query, or an error message if the operation fails.
        """
        info = self.username + '\n' + query # encode info sent to server
        response = self.send_recv(Operations.LIST_ACCOUNTS, info)
        if response['operation'] == Operations.SUCCESS:
            return response['info'].split('\n')
        else:
            return 'Fail to get accounts list.'
    
    def delete_message(self, sender, message, idx):
        """
        Request to deletes a specific message from the user's account and get response. 
        
        Args:
            sender (str): The sender of the message.
            message (str): The content of the message.
            idx (int): The index of the message in the list.
        
        Returns:
            str: A success or failure message.
        """
        info = self.username + '\n' + str(idx) # encode info sent to server
        response = self.send_recv(Operations.DELETE_MESSAGE, info)
        if response['operation'] == Operations.SUCCESS:
            return 'Delete message successfully.'
        else:
            return 'Fail to delete message.'
        
    def delete_account(self):
        """
        Request to delete the current user's account from the server and get response. 
        
        Returns:
            str: A success or failure message.
        """
        info = self.username
        response = self.send_recv(Operations.DELETE_ACCOUNT, info)
        if response['operation'] == Operations.SUCCESS:
            return 'Delete account successfully.'
        else:
            return 'Fail to delete account.'

class ChatApp:
    """
    A chat application that allows users to log in, send and receive messages, 
    search for other accounts, and manage their accounts, with GUI implemented by tkinter. 
    """
    def __init__(self, root, host='127.0.0.1', port=5555):
        """
        Initializes the chat application.
        
        Args:
            root (tk.Tk): The main application window.
        """
        self.root = root
        self.root.geometry("600x350")
        self.client = Client(host, port)
        print('init')
        self.setup_login_page()

    def setup_login_page(self):
        """
        Sets up the login/signup page.
        """
        print('setup_login_page')
        self.clear_window()
        self.root.title("Log in/Sign up")
        tk.Label(self.root, text="(create a new account if the username has not been signed up)").pack()
        tk.Label(self.root, text="Username:").pack()
        self.username_entry = tk.Entry(self.root) # get username entry
        self.username_entry.pack()
        tk.Button(self.root, text="Next", command=self.validate_username).pack()

    def validate_username(self):
        """
        Validates the entered username.
        
        Displays an error message if the username is empty or contains spaces.
        """
        name = self.username_entry.get().strip() 
        if not name or " " in name:
            messagebox.showerror("Error", "Please enter a valid username. It should not be empty or contain spaces.")
        else:
            self.go_to_password_page()

    def go_to_password_page(self):
        """
        Navigates to the password entry page.
        """
        self.username = self.username_entry.get()
        self.clear_window()
        self.root.title("Log in/Sign up")
        tk.Label(self.root, text="(If the username does not exist, enter the password to sign up.)").pack()
        tk.Label(self.root, text="Password:").pack()
        self.password_entry = tk.Entry(self.root, show="*") # get password entry
        self.password_entry.pack()
        tk.Button(self.root, text="Log in/Sign up", command=self.login).pack()
        tk.Button(self.root, text="Back", command=self.setup_login_page).pack()

    def hash_password(self, password):
        """
        Hashes a password using SHA-256.
        
        Args:
            password (str): The password to hash.
        
        Returns:
            str: The hashed password.
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self):
        """
        Logs the user in or registers a new account if the username does not exist.
        """
        password = self.hash_password(self.password_entry.get())
        success = self.client.login(self.username, password)
        if success:
            self.setup_account_page()
        else:
            messagebox.showerror("Error", 'Incorrect password.')

    def setup_account_page(self):
        """
        Sets up the account dashboard after a successful login.
        """
        self.clear_window()
        self.root.title("Account - " + self.username)
        self.unread_label = tk.Label(self.root, text="Checking messages...")
        self.unread_label.pack()
        tk.Button(self.root, text="List accounts", command=self.setup_list_accounts_page).pack()
        tk.Button(self.root, text="Send messages", command=self.setup_send_message_page).pack()
        tk.Button(self.root, text="Read messages", command=self.read_messages).pack()
        tk.Button(self.root, text="Delete account", command=self.delete_account).pack()
        tk.Button(self.root, text="Log out", command=self.setup_login_page).pack()
        self.refresh_unread_messages() 

    def refresh_unread_messages(self):
        """
        Refreshes the unread messages count every second to notify logged-in users about new undelivered messages immediately. 
        """
        if hasattr(self, "unread_label") and self.unread_label.winfo_exists():
            unread_messages = self.client.get_unread() 
            self.unread_label.config(text=f"({len(unread_messages)} unread messages)")
            self.root.after(1000, self.refresh_unread_messages)

    def setup_list_accounts_page(self):
        """
        Sets up the account search page.
        """
        self.clear_window()
        self.root.title("Search accounts")
        tk.Label(self.root, text="Search for existing accounts").pack()
        self.search_entry = tk.Entry(self.root) # get query entry
        self.search_entry.pack()
        tk.Button(self.root, text="Search", command=self.list_accounts).pack()
        tk.Button(self.root, text="Back", command=self.setup_account_page).pack()

    def list_accounts(self):
        """
        Lists all accounts that match the search query. Add a scroll bar to display all accounts comfortably. 
        """
        query = self.search_entry.get()
        response = self.client.list_accounts(query)  
        self.clear_window()
        self.root.title("Accounts List")

        # add scroll bar
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(main_frame)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        account_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=account_frame, anchor="n", width=self.root.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)
        for user in response:
            user_frame = tk.Frame(account_frame)
            user_frame.pack(fill="x", expand=True)
            tk.Label(user_frame, text=user).pack(anchor="center", pady=1)
        account_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))
        tk.Button(self.root, text="Back", command=self.setup_account_page).pack()

    def setup_send_message_page(self):
        """
        Sets up the interface for sending messages.

        Ask user to enter the recipient and message. Provides buttons to send the message or 
        navigate back to the account page.
        """
        self.clear_window()
        self.root.title("Send messages")
        tk.Label(self.root, text="Recipient:").pack()
        self.recipient_entry = tk.Entry(self.root)
        self.recipient_entry.pack()
        tk.Label(self.root, text="Message:").pack()
        self.message_entry = tk.Entry(self.root)
        self.message_entry.pack()
        tk.Button(self.root, text="Send", command=self.send_message).pack()
        tk.Button(self.root, text="Back", command=self.setup_account_page).pack()

    def send_message(self):
        """
        Sends a message to a recipient.

        Retrieves the recipient and message from the input fields and 
        sends them accordingly. Displays a success or error message 
        based on the result.
        """
        recipient = self.recipient_entry.get()
        message = self.message_entry.get()
        status, result = self.client.send_message(recipient, message)
        if status:
            messagebox.showinfo("Success", result)
        else:
            messagebox.showerror("Error", result)
    
    def read_messages(self):
        """
        Checks for unread messages.

        If there are unread messages, navigates to the unread messages 
        page. Otherwise, directs the user to the read messages result page.
        """
        unread_messages = self.client.get_unread()
        num_unread = len(unread_messages)
        if num_unread > 0:
            self.setup_unread_messages_page()
        else:
            self.setup_read_messages_result_page()

    def setup_unread_messages_page(self):
        """
        Sets up the interface for reading unread messages.

        Ask users to enter the number of messages to read. 
        """
        self.clear_window()
        self.root.title("Read messages")
        tk.Label(self.root, text="How many messages would you like to read? (Please enter an integer)").pack()
        self.per_page_entry = tk.Entry(self.root)
        self.per_page_entry.pack()
        tk.Button(self.root, text="Read", command=self.setup_unread_messages_result_page).pack()
        tk.Button(self.root, text="Back", command=self.setup_account_page).pack()

    def setup_unread_messages_result_page(self):
        """
        Displays unread messages based on the number of messages the user wants to read. 
        """
        per_page = self.per_page_entry.get() # get number of messages the user wants to read
        if not per_page.isdigit():
            messagebox.showerror("Error", "Invalid number. Please enter again.")
            self.setup_unread_messages_page()
        per_page = int(per_page)

        messages = self.client.read_unread_messages(per_page)
        self.clear_window()
        self.root.title("Read messages")
        for message in messages:
            tk.Label(self.root, text=f"{message['from']}: {message['message']}").pack()
        tk.Button(self.root, text="Back", command=self.setup_account_page).pack()

    def setup_read_messages_result_page(self):
        """
        Displays read messages with a delete option. Add a scroll bar to display all messages comfortably. 

        Each message is a button that allows deletion upon clicking. 
        """
        self.clear_window()
        self.root.title("Read Messages")
        tk.Label(self.root, text="(Click on a message to delete.)", fg="gray").pack()

        # add scroll bar
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(main_frame)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        message_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=message_frame, anchor="n", width=self.root.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)

        messages = self.client.read_messages()
        idx = len(messages) - 1
        for message in messages[::-1]:
            sender = message['from']
            me = message['message']

            # each message is a button that allows deletion upon clicking
            msg_button = tk.Button(message_frame, text=f"{sender}: {me}",command=lambda s=sender, m=me, i=idx: self.confirm_delete_message(s, m, i))
            msg_button.pack(fill="x", padx=10, pady=2) 
            idx -= 1
        message_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))
        tk.Button(self.root, text="Back", command=self.setup_account_page).pack()

    
    def confirm_delete_message(self, sender, message, idx):
        """
        Confirms the deletion of a message.

        Opens a confirmation window asking the user to confirm deleting 
        the selected message. If confirmed, the message is deleted and the interface is updated.

        Args:
            sender (str): The sender of the message.
            message (str): The message content.
            idx (int): The index of the message in the message list.
        """

        confirm_window = tk.Toplevel(self.root)
        confirm_window.title("Delete Message")
        tk.Label(confirm_window, text="Do you want to delete this message?").pack(pady=10)
        
        # delete message upon confirming deletion
        def delete_message():
            response = self.client.delete_message(sender, message, idx)
            confirm_window.destroy()
            messagebox.showinfo(message=response)
            self.setup_read_messages_result_page()
        
        tk.Button(confirm_window, text="Yes", command=delete_message).pack(side=tk.LEFT, padx=10)
        tk.Button(confirm_window, text="No", command=confirm_window.destroy).pack(side=tk.RIGHT, padx=10)

    
    def delete_account(self):
        """
        Confirms and deletes the user account.

        Opens a confirmation window asking the user to confirm account 
        deletion. If confirmed, the account is deleted and all messages 
        sent from this account are deleted from their recipients, 
        and the user is redirected to the login page.
        """
        confirm_window = tk.Toplevel(self.root)
        confirm_window.title("Delete Account")
        tk.Label(confirm_window, text="Do you want to delete this account? This will delete all your messages.").pack(pady=10)
        
        # delete account upon confirming deletion
        def delete_a():
            response = self.client.delete_account()
            confirm_window.destroy()
            messagebox.showinfo(message=response)
            self.setup_login_page()
        
        tk.Button(confirm_window, text="Yes", command=delete_a).pack(side=tk.LEFT, padx=10)
        tk.Button(confirm_window, text="No", command=confirm_window.destroy).pack(side=tk.RIGHT, padx=10)


    def clear_window(self):
        """
        Clears all widgets from the current window.
        """
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    import configparser
    config = configparser.ConfigParser()
    config.read('config.ini')
    host = config['server']['host']
    port = int(config['server']['port'])
    root = tk.Tk()
    app = ChatApp(root, host, port)
    root.mainloop()
