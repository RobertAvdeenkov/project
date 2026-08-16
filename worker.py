import pika
from database import LocalSession
from models import Message
import time

time.sleep(10)

def callback(ch,method,properties,body):
    data=body.decode().split('@$')
    print(data)
    with LocalSession() as db:
        target=Message(name=data[0], category=data[1], text=data[2])
        db.add(target)
        db.commit()

connection=pika.BlockingConnection(pika.ConnectionParameters('rabbitmq',port=5672))
channel=connection.channel()
channel.queue_declare('messages', durable=True)

channel.basic_consume(queue='messages', on_message_callback=callback,auto_ack=True)
print('Started')
channel.start_consuming()