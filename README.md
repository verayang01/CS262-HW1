# Simple Chat Application

This is a simple client-server chat application implemented in Python. The application allows users to sign up, log in, send and receive messages, delete messages, search for other users, and manage their accounts. The client is built with a graphical interface using `tkinter`, and the server supports multiple clients via multithreading. We have 2 implementations each with a different `wire protocol`:

1. **Custom Byte String Protocol**: Uses a structured byte format for efficient communication.
2. **JSON Protocol**: Uses JSON-encoded messages for easier readability and debugging.


# Implementation 1: Custom Byte String Protocol

The communication between the client and the server follows a custom byte string protocol:

1. Each message starts with a **fixed-size header** (64 bytes) indicating the length of the upcoming message.
2. The message body consists of:
   - **Protocol version** (1 byte)
   - **Operation code** (2 bytes)
   - **Message content** (variable length)

## Running the Custom Protocol Version

To run the chat application with our custom wire protocol, first direct into the `wire_protocol` folder. 

### 1. Server Configurations
In the `config.ini` file, set the `host` to your desired server IP and `port` to your desired port. For example, 

```sh
[server]
host = 127.0.0.1
port = 5555
```

### 2. Setting Up the Server

To start the server, in your terminal, run:

```sh
python server.py
```

### 3. Setting Up the Client

To start the client, in another terminal, run:

```sh
python client.py
```
This will launch the graphical interface for users to interact with the chat application. 

## File Structure

```sh
.
├── client.py
├── server.py
├── protocol.py
├── operation.py
├── config.ini
├── test.py
```

### `client.py`
- Implements the **Client** class, which connects to the server and facilitates communication.
- Provides methods for logging in, creating new accounts, managing user authentication, sending messages, reading messages, deleting messages, searching for existing accounts, and deleting accounts. 
- Implements the **ChatApp** class, which provides a `tkinter` GUI and defines the logic for user interaction.

### `server.py`
- Implements the **Server** class, which handles multiple clients using threading.
- Manages requests for user operations, including account creation, user authentication, account retrieval, message delivery, message retrieval, message deletion, and account deletion.
- Stores user data in a JSON file (`accounts.json`).

### `protocol.py`
Defines methods for serializing and deserializing messages to conform to the custom wire protocol. 

Before sending data, serialization first converts the data dictionary into a structured byte string by encoding the dictionary values (`version`, `operation`, `info`) into a continuous byte string.

When receiving data, the deserialization function decodes the byte string back into a dictionary by extracting the protocol version (1st byte), operation code (next 2 bytes), and message content from the received byte string.


### `operation.py`
Defines the 2-digit operation codes used in the protocol for different actions.

### `config.ini`
Stores server configuration.

### `test.py`
- Contains **unit tests** for the client-server interaction using Python’s unittest module.
- Tests server creation, client creation, client-server communication, user account creation and authentication, account search, message view and delivery, and account deletion.

# Implementation 2: JSON Wire Protol 
We provide a second version of the simple chat application with the wire protocol implemeneted by `JSON`. This implementation provides the same functionalities and user interface. 

## Running the Custom Protocol Version

To run the chat application with JSON wire protocol, first direct into the `json_protocol` folder. 

### 1. Server Configurations
In the `config.ini` file, set the `host` to your desired server IP and `port` to your desired port. For example, 

```sh
[server]
host = 127.0.0.1
port = 5555
```

### 2. Setting Up the Server

To start the server, in your terminal, run:

```sh
python server.py
```

### 3. Setting Up the Client

To start the client, in another terminal, run:

```sh
python client.py
```
This will launch the graphical interface for users to interact with the chat application. 

## File Structure

```sh
.
├── client.py
├── server.py
├── config.ini
├── test.py
```

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
