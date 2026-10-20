import pika
import json

class RabbitPublisher:
    def __init__(self, host='localhost', user='user', password='password'):
        self.credentials = pika.PlainCredentials(user, password)
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host, credentials=self.credentials)
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='events', durable=True)

    def publish(self, event_type: str, payload: dict, message_id: str = None):
        message = {"type": event_type, "payload": payload, "id": message_id}
        self.channel.basic_publish(
            exchange='',
            routing_key='events',
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2) # persistent
        )