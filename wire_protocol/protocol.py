def serialize(data):
  """
  Serializes a dictionary containing protocol data into a byte string.

  Args:
      data (dict): A dictionary with the following keys:
          - 'version' (str): The protocol version.
          - 'operation' (str): A two-character operation code.
          - 'info' (str): The message to be sent.

  Returns:
      bytes: A serialized byte string containing the encoded data.
  """
  encode_data = data["version"].encode("utf-8")
  encode_data += data["operation"].encode("utf-8")
  encode_data += data["info"].encode("utf-8")
  return encode_data

def deserialize(data):
  """
  Deserializes a byte string back into a dictionary containing protocol data.

  Args:
      data (bytes): The serialized byte string to be decoded.

  Returns:
      dict: A dictionary with the following keys:
          - 'version' (str): The protocol version.
          - 'operation' (str): A two-character operation code.
          - 'info' (str): The message to be sent.
  """
  data = data.decode("utf-8")
  decod_data = {}
  decod_data["version"] = data[0]
  decod_data["operation"] = data[1:3]
  decod_data["info"] = data[3:]

  return decod_data
