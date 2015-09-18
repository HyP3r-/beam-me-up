# -*- coding: utf-8 -*-
import struct
import operator
import serial


SET = 0x00
GET = 0x01

serial = serial.Serial(port="/dev/ttyUSB0",
                       baudrate=38400,
                       bytesize=serial.EIGHTBITS,
                       parity=serial.PARITY_EVEN,
                       stopbits=serial.STOPBITS_ONE,
                       timeout=1)


def power_on():
    """
    power on function
    """
    send_message(0x17, 0x2E, SET, 0x00, 0x00)
    send_message(0x17, 0x2E, SET, 0x00, 0x00)


def power_off():
    """
    power off function
    """
    send_message(0x17, 0x2F, SET, 0x00, 0x00)


def mute_on():
    """
    mute the projector
    """
    send_message(0x00, 0x30, SET, 0x00, 0x01)


def mute_off():
    """
    unmute the projector
    """
    send_message(0x00, 0x30, SET, 0x00, 0x00)


# Method to send messages to Projector, including message wrapper
def send_message(item_number_upper, item_number_lower, set_get, data_upper, data_lower):
    # calculate the check sum
    check_sum = reduce(operator.or_, [item_number_upper,
                                      item_number_lower,
                                      set_get,
                                      data_upper,
                                      data_lower])

    # generate the message
    send_message = struct.pack("BBBBBBBB",
                               0xA9,
                               item_number_upper,
                               item_number_lower,
                               set_get,
                               data_upper,
                               data_lower,
                               check_sum,
                               0x9A)

    # send the message
    serial.write(send_message)

    # wait for data
    message = serial.read(8)

    # if not the full message was received we have a problem
    if len(message) != 8:
        raise Exception("SET: Projector is not responding correctly!")

    # unpack the message
    receive_message = struct.unpack("BBBBBBBB", message)
    if send_message[3] == 0x00 and receive_message[1] == 0x01:
        return None
    elif send_message[3] == 0x01 and receive_message[1] == 0x01:
        return receive_message[4] << 8 or receive_message[5]
    elif receive_message[1] == 0x00:
        raise Exception(
            "Projector returns errorcode: " + str(receive_message[4] << 8) or str(receive_message[5]))
    else:
        raise Exception("Error, please contact admin!")