import telepot
from telepot.loop import MessageLoop
import json
import logging
import time
import datetime

from MqttHand import MqttHand

def handle(msg):
    idm = msg["chat"]["id"]
    if msg["text"] == "holis":
        bot.sendMessage(idm, "hla k Ase")
    if msg["text"] == "Date":
        bot.sendMessage(idm, str(datetime.datetime.now()))

class Glogger():
    def __init__(self, conf):
        self.conf = conf
        self.bot = telepot.Bot(conf["token"])
        self.mq = MqttHand(conf["mqtt"])
        

    def run(self):

        me = self.bot.getMe()

        for k in me.keys():
            logging.info(k + ": " + str(me[k]))

        MessageLoop(self.bot, handle).run_as_thread()
        self.mq.start()

        try:
            while 1:
                try:
                    buff = self.mq.get_buffer()
                    for elem in buff:
                        pay = json.loads(elem["payload"])
                        if "glog" in pay.keys():
                            if pay["glog"] == True and pay["text"] != "":
                                self.bot.sendMessage(self.conf["id"], pay["text"])
                except:
                    logging.critical("exception en msg sendind")
                time.sleep(1)
        except KeyboardInterrupt:
            self.mq.disconnect()


