#!/usr/bin/env python
import paho.mqtt
import paho.mqtt.client as mqtt
from paho.mqtt import publish
import logging
import unittest
import threading
import time
import sys
import copy
import json

__author__ = "dcpulido91@gmail.com"


class MqttHand(threading.Thread):
    def __init__(self,
                 conf=None,
                 controller=None):
        threading.Thread.__init__(self)
        if conf is not None:
            self.conf = conf
        else:
            self.conf = dict(host="localhost",
                             port=1883,
                             timeout=60,
                             subscribe=["MqttHand/#"])
        self.connected = False
        self.client = mqtt.Client()
        self.controller = controller
        self.buffer = []

    def run(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.conf["host"],
                            self.conf["port"],
                            self.conf["timeout"])
        for sub in self.conf["subscribe"]:
            logging.info("MQTT:Subscribe "+sub)
            self.client.subscribe(sub)
        self.client.loop_forever()

    def on_connect(self,
                   client,
                   userdata,
                   flags,
                   rc):
        self.connected = True
        logging.info("MQTT:Connected with result code "+str(rc))

    def on_message(self,
                   client,
                   userdata,
                   msg):
        try:
            payload = json.loads(msg.payload)
        except ValueError:
            payload = msg.payload
        message = dict(topic=msg.topic,
                       payload=msg.payload)
        if self.controller is not None:
            self.controller.parse_message(message)
        else:
            self.buffer.append(message)

    def on_publish(self,
                   path,
                   payload,
                   host="localhost"):
        if host is not None:
            hh = host
        else:
            hh = self.conf["host"]
        publish.single(path,
                       payload,
                       hostname=hh)

    def get_buffer(self):
        toret = copy.deepcopy(self.buffer)
        self.buffer = []
        return toret

    def disconnect(self):
        logging.info("MQTT:Disconnect")
        self.client.disconnect()
        self.connected = False


class TestMqttHand(unittest.TestCase):
    def test_init_connected(self):
        mq = MqttHand()
        self.assertEqual(mq.connected, False)

    def test_init_NoConf_host(self):
        mq = MqttHand()
        self.assertEqual(mq.conf["host"], "localhost")

    def test_init_NoConf_port(self):
        mq = MqttHand()
        self.assertEqual(mq.conf["port"], 1883)

    def test_init_Conf_host(self):
        mq = MqttHand(dict(host="192.169.0.1", port=1884))
        self.assertEqual(mq.conf["host"], "192.169.0.1")

    def test_init_Conf_port(self):
        mq = MqttHand(dict(host="192.169.0.1", port=1884))
        self.assertEqual(mq.conf["port"], 1884)

    def test_start(self):
        mq = MqttHand(dict(host="localhost",
                           port=1883,
                           timeout=60,
                           subscribe=["MqttHand"]))
        mq.start()
        time.sleep(0.1)
        con = mq.connected
        mq.disconnect()
        self.assertEqual(con, True)

    def test_disconnect(self):
        mq = MqttHand(dict(host="localhost",
                           port=1883,
                           timeout=60,
                           subscribe=["MqttHand"]))
        mq.start()
        time.sleep(0.1)
        mq.disconnect()
        con = mq.connected
        self.assertEqual(con, False)

    def test_publish(self):
        mq = MqttHand(dict(host="localhost",
                           port=1883,
                           timeout=60,
                           subscribe=["MqttHand/#"]))
        mq.start()
        time.sleep(0.1)
        mq.on_publish("MqttHand/test",
                      "Hello")
        aux = []
        while aux == []:
            aux = mq.get_buffer()
            time.sleep(0.1)
        mq.disconnect()
        self.assertEqual(aux[0]["payload"],
                         "Hello")

    def test_message_async(self):
        mq = MqttHand(dict(host="localhost",
                           port=1883,
                           timeout=60,
                           subscribe=["MqttHand/#"]))
        mq.start()
        time.sleep(0.1)
        mq.on_publish("MqttHand/test",
                      "Hello")
        aux = []
        while aux == []:
            aux = mq.get_buffer()
            time.sleep(0.1)
        mq.disconnect()
        self.assertEqual(aux[0]["payload"],
                         "Hello")

    def test_message_sync(self):
        class Controller:
            def __init__(self):
                self.message = None

            def parse_message(self, message):
                self.message = message
        cnt = Controller()
        mq = MqttHand(conf=dict(host="localhost",
                                port=1883,
                                timeout=60,
                                subscribe=["MqttHand/#"]),
                      controller=cnt)
        mq.start()
        time.sleep(0.2)
        mq.on_publish("MqttHand/test",
                      "Hello")
        mq.disconnect()
        while cnt.message == None:
            pass
        print cnt.message
        self.assertEqual(cnt.message["payload"], "Hello")


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)s:%(message)s',
        level=logging.DEBUG)
    logging.info("STARTING TEST")
    unittest.main()
    
