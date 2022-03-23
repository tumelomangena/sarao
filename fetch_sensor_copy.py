#!/usr/bin/python
from katcorelib import (standard_script_options, verify_and_connect, user_logger)
import katuilib
from prettytable import PrettyTable
from colorama import Fore
from json import load as load_json
from time import sleep
import numpy as np
import csv



s = raw_input("Would you like to save the data in a file? ")


def get_sensor_data(proxy, sensors):
    """Returns sensor-value for a given proxy and sensor list"""
    sensor_data = {}
    info = ["value", "status", "description"]
    if opts.info_request == "value":
        for sen in sensors:
            try:
                sensor_data[sen] = proxy.sensors[sen].get_value()
            except Exception:
                sensor_data[sen] = None

    if opts.info_request == "status":
        for sen in sensors:
            try:
                sensor_data[sen] = proxy.sensors[sen].get_status()
            except Exception:
                sensor_data[sen] = None

    if opts.info_request == "description":
        for sen in sensors:
            try:
                sensor_data[sen] = proxy.sensors[sen].description
            except Exception:
                sensor_data[sen] = None


    return sensor_data


def print_table(formatted_data):
    table = PrettyTable()
    table.field_names = ['sensor', 'value']
    for i in formatted_data.items():
        table.add_row(i)
    print(table)

# Parse command-line options that allow the defaults to be overridden
parser = standard_script_options(
    usage="usage: %prog --operator <name> --receiver-band=False",
    description="script to establish basic health of the mkat system ",
)
parser.add_option(
    "--operator",
    type="string",
    default="ops",
    help='the name of the operator',
)
parser.add_option(
    "--sensor-group",
    type="string",
    default=False,
    help='sensor group name',
)

parser.add_option(
    "--info-request",
    type="string",
    default=False,
    help='which information is requested',
)

# assume basic options passed from instruction_set
parser.set_defaults(
    description="fetch sensors description", proposal_id="20210213-OPS", observer="operator"
)

(opts, args) = parser.parse_args()

#if opts.sensor-group not in ["anc" , "ants" , "cbf", "tfr", "sdp", "cam", "kataware"]:
#    raise ValueError("Please provide correct sensor group name")

sensor_g = ["anc" , "ants" , "cbf", "tfr", "sdp", "cam", "kataware"]
info = ["value", "status", "description"]

with open("sen.json", "r") as read_file:
    sensors = load_json(read_file)
    for i in sensor_g:
        if i == opts.sensor_group:
            sensors = sensors[i]

with verify_and_connect(opts) as kat:
    sleep(5)
    group = get_sensor_data(kat, sensors)
    print(' Sensors for {}'.format(opts.sensor_group))
    print_table(group)


#saving data option
if s == "yes":
    with open(''+(opts.sensor_group)+'_data.csv', 'wb') as opts.sensor_group:
        writer = csv.writer(opts.sensor_group)
        for key, value in group.iteritems():
            writer.writerow([key, value])
