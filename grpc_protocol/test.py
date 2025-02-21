import unittest
import threading
import time
import grpc
from concurrent import futures
import client
import server
import chat_pb2
import chat_pb2_grpc

class TestClientServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Start the gRPC server in a separate thread before running any tests."""
        cls.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        chat_pb2_grpc.add_ChatServiceServicer_to_server(server.ChatService(), cls.server)
        cls.server.add_insecure_port('[::]:5555')  # Use the gRPC port
        cls.server_thread = threading.Thread(target=cls.server.start)
        cls.server_thread.daemon = True  # Daemonize thread to exit when the main program exits
        cls.server_thread.start()

        # Wait for the server to start
        time.sleep(1)  

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests are done."""
        cls.server.stop(0) 

    def setUp(self):
        """Initialize the gRPC client for each test."""
        self.client = client.Client() 

    def test_server_creation(self):
        """Test that the server is created correctly."""
        self.assertIsNotNone(self.server)

    def test_client_creation(self):
        """Test that the client is created correctly."""
        test_client = client.Client()
        self.assertIsInstance(test_client, client.Client)

    def test_login_existing_user(self):
        """Test logging in with an existing user."""
        # Add a user to the server's accounts
        server_instance = server.ChatService()
        server_instance.accounts = {'existing_user': {'password': 'hashed_password', 'read_messages': [], 'unread_messages': []}}
        result = self.client.login('existing_user', 'hashed_password')
        self.assertTrue(result)

    def test_login_new_user(self):
        """Test signing up a new user via gRPC."""
        result = self.client.login('new_user', 'hashed_password')      
        self.assertTrue(result, "User creation/login failed!")

        # Verify 'new_user' appears in the real account list
        accounts = self.client.list_accounts('')
        self.assertIn('new_user', accounts)  


    def test_login_wrong_password(self):
        """Test logging in with a wrong password for an existing user."""
        # Add a user to the server's accounts
        server_instance = server.ChatService()
        server_instance.accounts = {'existing_user': {'password': 'hashed_password', 'read_messages': [], 'unread_messages': []}}
        # Attempt to log in with the wrong password
        result = self.client.login('existing_user', 'wrong_password')
        self.assertFalse(result)


    def test_list_accounts(self):
        """Test listing all accounts via gRPC."""
        self.client.login('user1', 'hashed_password')
        self.client.login('user2', 'hashed_password')
        self.client.login('user3', 'hashed_password')

        result = self.client.list_accounts('')
        for user in ['user1', 'user2', 'user3']:
            self.assertIn(user, result, f"Expected user {user} not found in {result}")


    def test_list_accounts_with_query(self):
        """Test listing accounts with a search query."""
        server_instance = server.ChatService()
        server_instance.accounts = {
            'user1': {'password': 'hashed_password', 'read_messages': [], 'unread_messages': []},
            'user2': {'password': 'hashed_password', 'read_messages': [], 'unread_messages': []},
            'user3': {'password': 'hashed_password', 'read_messages': [], 'unread_messages': []}
        }
        result = self.client.list_accounts('user2')
        self.assertEqual(result, ['user2'])


    def test_send_message_valid_recipient(self):
        """Test sending a message to a valid recipient via gRPC."""
        self.client.login('sender', '123')  
        self.client.login('recipient', '123')  

        self.client.username = 'sender'
        status, result = self.client.send_message('recipient', 'Hello')

        # Verify success sending message
        self.assertTrue(status, f"Message sending failed! Server response: {result}")
        self.assertEqual(result, 'Message sent successfully.')


    def test_send_message_invalid_recipient(self):
        """Test sending a message to an invalid recipient."""
        server_instance = server.ChatService()
        server_instance.accounts = {
            'sender': {'password': 'hashed_password', 'read_messages': [], 'unread_messages': []}
        }
        self.client.username = 'sender'
        status, result = self.client.send_message('invalid_recipient', 'Hello')
        self.assertFalse(status)
        self.assertEqual(result, 'Invalid recipient.')


    def test_read_unread_messages(self):
        """Test reading unread messages via gRPC."""
        self.client.login('user', '123')  
        self.client.login('sender', '123')  

        self.client.username = 'sender'
        status, _ = self.client.send_message('user', 'Hello')
        self.assertTrue(status, "Message sending failed, so there's nothing to read!")

        self.client.username = 'user'
        result = self.client.read_unread_messages(1)

        # Verify the unread message was received
        self.assertEqual(result, [{'sender': 'sender', 'message': 'Hello'}])


    def test_read_all_messages(self):
        """Test reading all messages via gRPC."""
        self.client.login('user', '123')
        self.client.login('sender', '123')

        # Send a message 
        self.client.username = 'sender'
        status, _ = self.client.send_message('user', 'Hello')
        self.assertTrue(status, "Message sending failed, so there's nothing to read!")

        # Reading message
        self.client.username = 'user'
        self.client.read_unread_messages(1)

        # Check the read messages
        result = self.client.read_messages()
        self.assertEqual(result, [{'sender': 'sender', 'message': 'Hello'}])


    def test_delete_message(self):
        """Test deleting a message via gRPC."""
        self.client.login('user', '123')
        self.client.login('sender', '123')

        self.client.username = 'sender'
        status, _ = self.client.send_message('user', 'Hello')
        self.assertTrue(status, "Message sending failed, which means nothing to delete!")

        self.client.username = 'user'
        self.client.read_unread_messages(1)

        # Delete message 
        result = self.client.delete_message('sender', 'Hello', 0)
        self.assertEqual(result, 'Message deleted successfully.')


    def test_delete_account(self):
        """Test deleting an account via gRPC."""
        self.client.login('user', '123')  

        accounts = self.client.list_accounts('')
        self.assertIn('user', accounts)

        # Delete user
        result = self.client.delete_account()
        self.assertEqual(result, 'Account deleted successfully.')

        # Verify 'user' no longer exists
        accounts = self.client.list_accounts('')
        self.assertNotIn('user', accounts)



if __name__ == '__main__':
    unittest.main()