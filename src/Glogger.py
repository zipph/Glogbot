import telepot
from telepot.loop import MessageLoop
import json
import logging
import time
import datetime
import subprocess

from MqttHand import MqttHand
import sys
reload(sys)  
sys.setdefaultencoding('utf8')



class Glogger():
    def __init__(self, conf):
        self.conf = conf
        self.bot = telepot.Bot(conf["token"])
        self.mq = MqttHand(conf["mqtt"])
        

    def run(self):

        me = self.bot.getMe()

        for k in me.keys():
            logging.info(k + ": " + str(me[k]))

        MessageLoop(self.bot, self.handle).run_as_thread()
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

    def handle(self, msg):
        idm = msg["chat"]["id"]
        if idm == self.conf["id"]:
            out = subprocess.check_output(msg["text"].lower().split(" "))
            self.bot.sendMessage(idm, str(out))


