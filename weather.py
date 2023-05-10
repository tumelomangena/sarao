#!/usr/bin/python

from katcorelib import (standard_script_options, verify_and_connect, user_logger)
import katuilib
from prettytable import PrettyTable
from colorama import Fore
from json import load as load_json
from time import sleep
import socket
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def get_sensor_data(proxy, sensors):
    """Returns sensor-value pairs for a given proxy and sensor list"""
    sensor_data = {}
    for sen in sensors:
        try:
            sensor_data[sen] = proxy.sensors[sen].get_value()
        except Exception:
            sensor_data[sen] = None
    return sensor_data



# Parse command-line options that allow the defaults to be overridden
parser = standard_script_options(
    usage="usage: %prog --operator <name> --operator_=False",
    description="script to establish basic health of the mkat system ",
)
parser.add_option(
    "--operator",
    type="string",
    default="ops",
    help='the name of the operator',
)

# assume basic options passed from instruction_set
parser.set_defaults(
    description="Basic health check", proposal_id="20210213-OPS", observer="operator"
)

(opts, args) = parser.parse_args()


with verify_and_connect(opts) as kat:
    sleep(5)
    while True:
        wind = ["gust_wind_speed", "mean_wind_speed"]
        weather = get_sensor_data(kat.anc, wind)
        w = weather["gust_wind_speed"]
        sleep(1)
        weather1 = get_sensor_data(kat.anc, wind)
        w1 = weather1["gust_wind_speed"]
        if w1 == w:
            user_logger.warning("The wind sensor might be faulty, please check the weather plot" )
            print("First value is {}".format(w))
            print("Second value is {}".format(w1))
        else:
            continue

