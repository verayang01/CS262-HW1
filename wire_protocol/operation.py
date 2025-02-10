class Operations:
  """
    Defines operation codes used in the communication protocol.

  """
  
  SUCCESS = "00"
  FAILURE = "01"

  SEND_MESSAGE = "10"
  READ_UNREAD = "11"
  READ_ALL = "12"
  COUNT_UNREAD = "13" 
  LOGIN = "14"
  READ_ALL = "15"
  LIST_ACCOUNTS = "16"
  DELETE_MESSAGE = "17"
  DELETE_ACCOUNT = "18"
