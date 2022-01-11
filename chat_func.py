import paho.mqtt.client as paho
import random
import threading
import queue


CLIENT_ID = f'kyh-mqtt-{random.randint(0, 1000)}'
USERNAME = 'kyh_joakim'
PASSWORD = 's3cr37'
BROKER = 't1d6b060.eu-central-1.emqx.cloud'
PORT = 15779

CHAT_ROOMS = {
    'cooking': 'chat/cooking',
    'stamps': 'chat/stamps',
    'vegan': 'chat/cooking/vegan'
}


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print('Connected to Chat Server')
    else:
        print(f'Failed to connect to Chat Server. Error code {rc}')


def on_message(client, userdata, msg):
    # Convert message from bytes to string
    chat_message = msg.payload.decode()
    # Check if this was a message from someone else
    if not chat_message.startswith(userdata):
        # if so, print it
        print(chat_message)


def connect_mqtt(username):
    # Create a MQTT client object.
    # Every client has an id
    client = paho.Client(CLIENT_ID, userdata=username)
    # Set username and password to connect to broker
    client.username_pw_set(USERNAME, PASSWORD)

    # When connection response is received from broker
    # call the function on_connect
    client.on_connect = on_connect

    # Connect to broker
    client.connect(BROKER, PORT)

    return client


def main():
    # Init application. Ask for username and chat room
    username = input("Enter your username: ")

    print("Pick a room:")
    for room in CHAT_ROOMS:
        print(f"\t{room}")
    room = input("> ")

    # Use the room to set MQTT topic
    topic = CHAT_ROOMS[room]

    # Connect client
    client = connect_mqtt(username)

    # Subscribe to selected topic
    client.subscribe(topic)
    # Set the on_message callback function
    client.on_message = on_message

    # Create a queue that can be used for our input thread
    input_queue = queue.Queue()
    # This variable is used to exit the thread when the
    # user exits the application
    running = True

    def get_input():
        """
        Function used by the input thread
        :return: None
        """
        while running:
            # Get user input and place it in the input_queue
            input_queue.put(input())

    # Create input thread
    input_thread = threading.Thread(target=get_input)
    # and start it
    input_thread.start()

    # Start the paho client loop
    client.loop_start()

    # Publish a message to the chat room that the user has joined
    client.publish(topic, f"{username} has joined the chat")
    while True:
        try:
            # Check if there is an input from the user
            # If not we will get a queue.Empty exception
            msg_to_send = input_queue.get_nowait()
            # If we reach this point we have a message

            # Check if the user wants to exit the application
            if msg_to_send.lower() == "quit":
                # Publish a message that this user leaves the chat
                client.publish(topic, f"{username} has left the chat")
                # Indicate to the input thread that it can exit
                running = False
                break
            # Attaching the username to the message
            msg_to_send = f"{username}> {msg_to_send}"
            # and publish it
            client.publish(topic, msg_to_send)
        except queue.Empty:  # We will end up here if there was no user input
            pass  # No user input, do nothing

    # Stop the paho loop
    client.loop_stop()
    # The user needs to press ENTER to exit the while loop in the thread
    print("You have left the chat. Press [ENTER] to exit application.")


if __name__ == '__main__':
    main()
