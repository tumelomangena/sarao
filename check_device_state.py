#!/usr/bin/python
from katcorelib import (standard_script_options, verify_and_connect, user_logger)
import katuilib
from prettytable import PrettyTable
from colorama import Fore
from json import load as load_json
from time import sleep

def get_sensor_data(proxy, sensors):
    """Returns sensor-value pairs for a given proxy and sensor list"""
    sensor_data = {}
    for sen in sensors:
        try:
            sensor_data[sen] = proxy.sensors[sen].get_status()
        except Exception:
            sensor_data[sen] = None
    return sensor_data

def format_sensors(sensor_data, return_faults=False):
    for k in sensor_data.keys():
        if sensor_data[k] == 'error':
            sensor_data[k] = Fore.RED + str(sensor_data[k]) + Fore.RESET
        if sensor_data[k]  == 'warn':
            sensor_data[k] = Fore.YELLOW + str(sensor_data[k]) + Fore.RESET
        if sensor_data[k]  == 'unknown':
            sensor_data[k] = Fore.WHITE + str(sensor_data[k]) + Fore.RESET
        if sensor_data[k]  == 'failure':
            sensor_data[k] = Fore.BLUE + str(sensor_data[k]) + Fore.RESET
    if return_faults:
        return {k:v for (k,v) in sensor_data.items() if v!='nominal'}
    else:
        return sensor_data

def print_table(formatted_data):
    table = PrettyTable()
    table.field_names = ['sensor', 'status']
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
    "--return-faults",
    action="store_true",
    default=False,
    help='return table of faulty sensors only',
)

# assume basic options passed from instruction_set
parser.set_defaults(
    description="Basic health check", proposal_id="20210213-OPS", observer="operator"
)

(opts, args) = parser.parse_args()

with open("sensors.json", "r") as read_file:
    sensors = load_json(read_file)
    tfr_sensors = sensors['tfr_device_status']
    cbf_sensors = sensors['cbf_device_status']
    sdp_sensors = sensors['sdp_device_status']

with verify_and_connect(opts) as kat:
    sleep(5)
    sensor_data = [
        # proxy,     sensor list,  table title
        [kat.tfrmon, tfr_sensors, 'TFR Sensors\n'], [kat.cbfmon_1, cbf_sensors, 'CBF Sensors\n'], [kat, sdp_sensors, 'SDP Sensors\n']
    ]
    sleep(5)
    for i in sensor_data:
        print('\n{}'.format(i[2]))
        data = get_sensor_data(proxy=i[0], sensors=i[1])
        data = format_sensors(data, opts.return_faults)
        print_table(data)
        print('\n')
