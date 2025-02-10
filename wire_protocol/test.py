import unittest
import threading
import time
import socket
import json
import client
import server

class TestClientServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Start the server in a separate thread before running any tests."""
        # Establish server connection
        cls.server = server.Server(host='127.0.0.1', port=5555)
        cls.server_thread = threading.Thread(target=cls.server.start)
        cls.server_thread.daemon = True  
        cls.server_thread.start()

        # Wait for the server to start
        time.sleep(1)  

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests are done."""
        # Close the server socket (if needed)
        cls.server.server.close()

    def setUp(self):
        """Initialize the client for each test."""
        self.client = client.Client(host='127.0.0.1', port=5555)
    
    def test_server_creation(self):
        """Test that the server is created correctly."""
        self.assertIsInstance(self.server, server.Server)
        self.assertEqual(self.server.host, '127.0.0.1')
        self.assertEqual(self.server.port, 5555)
        self.assertIsNotNone(self.server.server)

    def test_server_listening(self):
        """Test that the server is appropriately listening for connections."""
        # Check if the server socket is in listening state
        self.assertTrue(self.server.server.fileno() > 0) 
        self.assertEqual(self.server.server.getsockname(), ('127.0.0.1', 5555))

    def test_client_creation(self):
        """Test that the client is created correctly."""
        test_client = client.Client(host='127.0.0.1', port=5555)
        self.assertIsInstance(test_client, client.Client)
        self.assertEqual(test_client.host, '127.0.0.1')
        self.assertEqual(test_client.port, 5555)
        self.assertIsNotNone(test_client.client)

    def test_client_connection(self):
        """Test that the client can connect to the server."""
        test_client = client.Client(host='127.0.0.1', port=5555)
        self.assertIsNotNone(test_client.client)
        self.assertEqual(test_client.client.getpeername(), ('127.0.0.1', 5555))  

    def test_login_existing_user(self):
        """Test logging in with an existing user."""
        # Add a user to the server's accounts
        self.server.accounts = {'existing_user': {'password': 'hashed_password', 'read_messages': [], 'unread_messages': []}}
        result = self.client.login('existing_user', 'hashed_password')
        self.assertTrue(result)

    def test_login_new_user(self):
        """Test signing up a new user."""
        # Ensure the server's accounts are empty
        self.server.accounts = {}
        result = self.client.login('new_user', 'hashed_password')
        self.assertTrue(result)
        self.assertIn('new_user', self.server.accounts)

    def test_login_wrong_password(self):
        """Test logging in with a wrong password for an existing user."""
        # Add a user to the server's accounts
        self.server.accounts = {'existing_user': {'password': 'hashed_password', 'read_messages': [], 'unread_messages': []}}

        # Test log in with the wrong password
        result = self.client.login('existing_user', 'wrong_password')
        self.assertFalse(result)

    def test_list_accounts(self):
        """Test listing all accounts."""
        self.server.accounts = {'user1': {'password': 'hashed_password', 'read_messages': [], 'unread_messages': []}, 
                                'user2': {'password': 'hashed_password', 'read_messages': [], 'unread_messages': []}, 
                                'user3': {'password': 'hashed_password', 'read_messages': [], 'unread_messages': []}}
        self.client.username = 'sender'
        result = self.client.list_accounts('')
        self.assertEqual(result, ['user1', 'user2', 'user3'])

    def test_list_accounts_with_query(self):
        """Test listing accounts with a search query."""
        self.server.accounts = {'user1': {'password': 'hashed_password', 'read_messages': [], 'unread_messages': []}, 
                                'user2': {'password': 'hashed_password', 'read_messages': [], 'unread_messages': []}, 
                                'user3': {'password': 'hashed_password', 'read_messages': [], 'unread_messages': []}}
        self.client.username = 'sender'
        result = self.client.list_accounts('user2')
        self.assertEqual(result, ['user2'])

    def test_send_message_valid_recipient(self):
        """Test sending a message to a valid recipient."""
        self.server.accounts = {'sender': {'password': 'hashed_password', 'read_messages': [], 'unread_messages': []}, 
                                'recipient': {'password': 'hashed_password', 'read_messages': [], 'unread_messages': []}}
        self.client.username = 'sender'
        status, result = self.client.send_message('recipient', 'Hello')
        self.assertEqual(status, True)
        self.assertEqual(result, 'Send message successfully.')

    def test_send_message_invalid_recipient(self):
        """Test sending a message to an invalid recipient."""
        self.server.accounts = {'sender': {'password': 'hashed_password', 'read_messages': [], 'unread_messages': []}}
        self.client.username = 'sender'
        status, result = self.client.send_message('invalid_recipient', 'Hello')
        self.assertEqual(status, False)
        self.assertEqual(result, 'Invalid recipient. Please enter a valid username.')

    def test_read_unread_messages(self):
        """Test reading unread messages."""
        self.server.accounts = {'user': {'password':'123','unread_messages': [{'from': 'sender', 'message': 'Hello'}],
                                         'read_messages':[]}}
        self.client.username = 'user'
        result = self.client.read_unread_messages(1)
        self.assertEqual(result, [{'from': 'sender', 'message': 'Hello'}])

    def test_read_all_messages(self):
        """Test reading all messages."""
        self.server.accounts = {'user': {'password':'123', 'unread_messages': [],
                                         'read_messages': [{'from': 'sender', 'message': 'Hello'}]}}
        self.client.username = 'user'
        result = self.client.read_messages()
        self.assertEqual(result, [{'from': 'sender', 'message': 'Hello'}])

    def test_delete_message(self):
        """Test deleting a message."""
        self.server.accounts = {'user': {'password':'123', 'unread_messages': [],
                                         'read_messages': [{'from': 'sender', 'message': 'Hello'}]}}
        self.client.username = 'user'
        result = self.client.delete_message('sender', 'Hello', 0)
        self.assertEqual(result, 'Delete message successfully.')
    
    def test_delete_account(self):
        """Test deleting an account."""
        self.server.accounts = {'user': {'password':'123', 'unread_messages': [], 'read_messages':[]}, 
                                'other_user': {'password':'123', 'read_messages': [], 
                                               'unread_messages': [{'from': 'user', 'message': 'Hello'}]}}
        self.client.username = 'user'
        result = self.client.delete_account()
        self.assertEqual(result, 'Delete account successfully.')
        self.assertNotIn('user', self.server.accounts)
        self.assertEqual(self.server.accounts['other_user']['unread_messages'], [])

if __name__ == '__main__':
    unittest.main()