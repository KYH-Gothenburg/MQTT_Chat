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


class Chat:
    def __init__(self, username, room):
        self.username = username
        self.room = room
        self.topic = CHAT_ROOMS[room]
        self.client = None
        self.connect_mqtt()
        self.input_queue = queue.Queue()
        # This variable is used to exit the thread when the
        # user exits the application
        self.running = True

    def connect_mqtt(self):
        # Create a MQTT client object.
        # Every client has an id
        self.client = paho.Client(CLIENT_ID)
        # Set username and password to connect to broker
        self.client.username_pw_set(USERNAME, PASSWORD)

        # When connection response is received from broker
        # call the function on_connect
        self.client.on_connect = lambda client, userdata, flags, rc: \
            print('Connected to Chat Server' if rc == 0 else f'Error connecting to Chat Server. Error code {rc}')

        # Connect to broker
        self.client.connect(BROKER, PORT)

    def on_message(self, client, userdata, msg):
        # Convert message from bytes to string
        chat_message = msg.payload.decode()
        # Check if this was a message from someone else
        if not chat_message.startswith(self.username):
            # if so, print it
            print(chat_message)

    def init_client(self):
        # Subscribe to selected topic
        self.client.subscribe(self.topic)
        # Set the on_message callback function
        self.client.on_message = self.on_message

        def get_input():
            """
            Function used by the input thread
            :return: None
            """
            while self.running:
                # Get user input and place it in the input_queue
                self.input_queue.put(input())

        # Create input thread
        input_thread = threading.Thread(target=get_input)
        # and start it
        input_thread.start()

        # Start the paho client loop
        self.client.loop_start()

        # Publish a message to the chat room that the user has joined
        self.client.publish(self.topic, f"{self.username} has joined the chat")

    def run(self):
        self.init_client()

        while True:
            try:
                # Check if there is an input from the user
                # If not we will get a queue.Empty exception
                msg_to_send = self.input_queue.get_nowait()
                # If we reach this point we have a message

                # Check if the user wants to exit the application
                if msg_to_send.lower() == "quit":
                    # Publish a message that this user leaves the chat

                    self.client.publish(self.topic, f"{self.username} has left the chat")
                    # Indicate to the input thread that it can exit
                    self.running = False
                    break
                # Attaching the username to the message
                msg_to_send = f"{self.username}> {msg_to_send}"
                # and publish it
                self.client.publish(self.topic, msg_to_send)
            except queue.Empty:  # We will end up here if there was no user input
                pass  # No user input, do nothing

        # Stop the paho loop
        self.client.loop_stop()
        # The user needs to press ENTER to exit the while loop in the thread
        print("You have left the chat. Press [ENTER] to exit application.")


def main():
    # Init application. Ask for username and chat room
    username = input("Enter your username: ")

    print("Pick a room:")
    for room in CHAT_ROOMS:
        print(f"\t{room}")
    room = input("> ")

    chat = Chat(username, room)
    chat.run()


if __name__ == '__main__':
    main()
