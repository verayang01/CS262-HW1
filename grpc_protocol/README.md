# Simple Chat Application - gRPC Implementation

We added a third implementation using Python with gRPC as the communication protocol. The functiionalities remain the same. The application allows users to sign up, log in, send and receive messages, delete messages, search for other users, and manage their accounts. The client is built with a graphical interface using `tkinter`, and the server supports multiple clients via multithreading. 

## Running the Custom Protocol Version

### 1. Requirements

To run this gRPC implementation, you need to have the `grpcio` and `grpcio-tools` packages:

   ```sh
   pip install grpcio grpcio-tools
   ```

### 2. Server Configurations
In the `config.ini` file, set the `host` to your desired server IP and `port` to your desired port. For example, 

```sh
[server]
host = 127.0.0.1
port = 5555
```

### 3. Setting Up the Server

To start the server, in your terminal, run:

```sh
python server.py
```

### 4. Setting Up the Client

To start the client, in another terminal, run:

```sh
python client.py
```
This will launch the graphical interface for users to interact with the chat application. 

## File Structure

```sh
.
├── chat.proto                
├── chat_pb2.py               
├── chat_pb2_grpc.py          
├── client.py               
├── server.py                 
├── config.ini                           
├── test.py                   
```

### `chat.proto`
This file defines the **Protocol Buffers** schema for the gRPC service. It specifies:

- The service (ChatService) and its methods (e.g., Login, SendMessage, etc.).

- The message types (e.g., LoginRequest, LoginResponse, Message, etc.) used for communication between the client and server.

- The data structure for requests and responses.

This file is used by the protoc compiler to generate the Python code for the gRPC service and messages.

### `chat_pb2.py`
This file is *auto-generated* by the protoc compiler from the chat.proto file. It contains:

- Python classes for the message types defined in chat.proto (e.g., LoginRequest, LoginResponse, Message, etc.).

- Serialization and deserialization logic for these messages.

This file is used by both the client and server to create and parse gRPC messages.

### `chat_pb2_grpc.py`
This file is also *auto-generated* by the protoc compiler from the chat.proto file. It contains:

- The gRPC service stubs for the client (ChatServiceStub).

- The service base class for the server (ChatServiceServicer).

The client uses the stub to call the server's methods, while the server implements the service by subclassing the base class.

### `client.py`
- Implements the **Client** class, which connects to the server and facilitates communication.
- Provides methods for logging in, creating new accounts, managing user authentication, sending messages, reading messages, deleting messages, searching for existing accounts, and deleting accounts. 
- Implements the **ChatApp** class, which provides a `tkinter` GUI and defines the logic for user interactions.

### `server.py`
- Implements the **Server** class, which handles multiple clients using threading.
- Manages requests for user operations, including account creation, user authentication, account retrieval, message delivery, message retrieval, message deletion, and account deletion.
- Stores user data in a JSON file (`accounts.json`).

### `config.ini`
Stores server configuration.

### `test.py`
- Contains **unit tests** for the client-server interaction using Python’s unittest module.
- Tests server creation, client creation, client-server communication, user account creation and authentication, account search, message view and delivery, and account deletion.
