import json
import boto3
import time
from queue import *
from Threads import *
from Charts import *

def create_queues(queues):
    asadaQueue = Queue()  # Suborders of meat asada
    adobadaQueue = Queue()  # Suborders of meat adobada
    othersQueue = Queue()  # Suborders of meat suadero, tripa, cabeza, and lengua
    queues.append(asadaQueue)
    queues.append(adobadaQueue)
    queues.append(othersQueue)

def assign_queues(queues, answersList):
    for answer in answersList:
        for suborder in answer.order.subordersList:  # Each suborder will be assigned to its respective queue according to the type of meat
            if suborder.meat == 'Asada':
                with lock:
                    if queues[0].empty():
                        threadPermits[0] = 1
                    queues[0].put(suborder)
            elif suborder.meat == 'Adobada':
                with lock:
                    if queues[1].empty():
                        threadPermits[1] = 1
                    queues[1].put(suborder)
            else:
                with lock:
                    if queues[2].empty():
                        threadPermits[2] = 1
                    queues[2].put(suborder)


def classify_data(data, answersList, receipt):
    # Assignment of data for each order and suborder
    order = Order(data['request_id'], data['datetime'], receipt)
    for suborder in data['orden']:
        order.totalSubs += 1
        taco = Suborder(suborder['part_id'], suborder['type'], suborder['meat'], suborder['quantity'],
                        suborder['ingredients'])
        order.subordersList.append(taco)
    answer = Answer(order)
    answersList.append(answer)

threadPermits = [0,0,0] # if 0 the thread shouldn't be thrown, if 1 it should be thrown
answersList = []
queues = []
received = []
def readSQS():
    StatsDict = {'Steps_Asada' : 0, 'Total_Asada' : 0, 'Time_Asada' : 0, 'Total_AsOrders' : 0, 'Steps_Adobada' : 0, 'Total_Adobada' : 0,'Time_Adobada' : 0,  'Total_AdOrders' : 0, 'Steps_Others' : 0, 'Total_Others' : 0, 'Time_Others' : 0, 'Total_OtOrders' : 0, 'Counter' : 0}
    sqs = boto3.client('sqs')
    asadaIngr = {'Guacamole': 500, 'Cilantro': 500, 'Salsa': 500, 'Cebolla': 500, 'Frijoles': 500, 'tortillas': 500}
    adobadaIngr = {'Guacamole': 500, 'Cilantro': 500, 'Salsa': 500, 'Cebolla': 500, 'Frijoles': 500, 'tortillas': 500}
    othersIngr = {'Guacamole': 500, 'Cilantro': 500, 'Salsa': 500, 'Cebolla': 500, 'Frijoles': 500, 'tortillas': 500}
    ingrQty = [asadaIngr, adobadaIngr, othersIngr]
    create_queues(queues)
    while True:
        try:
            response = sqs.receive_message(QueueUrl='https://sqs.us-east-1.amazonaws.com/292274580527/cc406_team6', MaxNumberOfMessages=10, WaitTimeSeconds=20)
            for message in response['Messages']:
                received.append(message['ReceiptHandle'])
                data = json.loads(message['Body'])
                print(data)
                classify_data(data, answersList,message['ReceiptHandle'])
            assign_queues(queues, answersList)
            threads(queues, answersList, ingrQty,threadPermits,StatsDict, received)
            time.sleep(10)
        except KeyboardInterrupt:
            raise
readSQS()


#diccionario que se vaya actualizando con calculos entre valores anteriores y nuevos (suma para no perder valores anteriores )
