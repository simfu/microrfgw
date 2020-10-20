import machine
from time import sleep_ms, sleep_us

tx_pin = machine.Pin(14, machine.Pin.OUT)


def send(sender, group, unit, state, repeat=3, learn=False):

    n_tx = 6
    if learn:
        n_tx = n_tx*10

    isr = machine.disable_irq()
    sleep_ms(50)
    for r in range(repeat):
        for i in range(n_tx):
            send_one(sender, group, unit, state)
            sleep_ms(50)
        sleep_ms(1000)
    machine.enable_irq(isr)


HIGH_PULSE_LEN = 280 - 65
LOW_PULSE_LOCK_LEN = 2650
LOW_PULSE_0_LEN = 280
LOW_PULSE_1_LEN = 1340


def send_one(sender, group, unit, state):
    """
    Send one frame to Chacon DIO device

    Frame is 32bits long:
      sender_id(26b)|is_group_cmd(1b)|on_or_off_state(1b)|device_unit_id(4b)

    Each frame bit is encoded to raw bit w/ Manchester (0 -> 01, 1 -> 10)

    Each raw bit is transmitted to radio using following encoding (ASK):
      0 -> transmitting during 280ms, not transmitting during 280ms
      1 -> transmitting during 280ms, not transmitting during 1340ms

    Each frame is surronded by lock signal:
      transmitting during 280ms, not transmitting during 2650ms
    """

    msg = 0x00000000
    msg |= (sender & 0x3FFFFFFF) << (32 - 26)
    msg |= (group & 0x01) << (32 - 27)
    msg |= (state & 0x01) << (32 - 28)
    msg |= unit & 0xF

    # log("Send msg:", msg, " (sender:", sender, " group", group, " state", state, " code", code, ")")

    # log("Send lock")
    send_pulse(HIGH_PULSE_LEN, LOW_PULSE_LOCK_LEN)
    # Data
    for i in range(1, 33):
        if msg & (1 << (32 - i)):
            # log("Send manchester data 1")
            send_pulse(HIGH_PULSE_LEN, LOW_PULSE_1_LEN)
            send_pulse(HIGH_PULSE_LEN, LOW_PULSE_0_LEN)
        else:
            # log("Send manchester data 0")
            send_pulse(HIGH_PULSE_LEN, LOW_PULSE_0_LEN)
            send_pulse(HIGH_PULSE_LEN, LOW_PULSE_1_LEN)
    # log("Send end")
    send_pulse(HIGH_PULSE_LEN, LOW_PULSE_LOCK_LEN)


def send_pulse(high_len, low_len, setval=tx_pin.value, sleepus=sleep_us):
    # log("Write", value, " on", tx_pin, " and sleep for", tx_len, "")
    setval(1)
    sleepus(high_len)
    setval(0)
    sleepus(low_len)
