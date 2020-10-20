import network
import time
import sys
import json
import microrf
import webrepl
import machine
from umqtt.robust import MQTTClient

import config
from config import name_to_rf

def log(*msg):
    print(" ".join(str(m) for m in msg))


def init_net():
    ap_if = network.WLAN(network.AP_IF)
    log("Disabling AP")
    ap_if.active(False)
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(config.wifi_id, config.wifi_pass)
    log("STA Connecting")
    for i in range(0, 20):
        log(".")
        time.sleep(1)
        if sta_if.isconnected():
            break
    else:
        log("STA Cannot connect")
        sys.exit(1)
    log("STA Connected")
    log(sta_if.ifconfig())


def init_mqtt():
    log("MQTT Connecting")
    cli = MQTTClient(config.mqtt_name, config.mqtt_server)
    cli.DEBUG = True
    cli.set_callback(sub_cb)
    cli.connect()
    cli.subscribe(config.mqtt_subscribe)
    log("MQTT Connected")
    return cli


def sub_cb(topic, msg):
    log("Message received", msg)
    msg = json.loads(msg)
    if msg.get("name") and name_to_rf.get(msg["name"]):
        args = name_to_rf[msg["name"]]
        args.update({"state": 1 if msg.get("nvalue") else 0})
        log("Switching", msg.get("name"), "to", args["state"])
        microrf.send(**args)


def main():
    init_net()
    mqtt_cli = init_mqtt()
    webrepl.start(password=config.ws_pass)
    machine.freq(160000000)
    log("Waiting for messages")
    while 1:
        mqtt_cli.check_msg()
        time.sleep(0.5)
    mqtt_cli.disconnect()


if __name__ == "__main__":
    main()
