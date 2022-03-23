
#!/usr/bin/python
from katcorelib import (standard_script_options, verify_and_connect, user_logger)
import katuilib
from prettytable import PrettyTable
from colorama import Fore
from json import load as load_json
from time import sleep
import numpy as np

a = ["{0:03}".format(i) for i in range(64)]

def str_insert(list, str):
    # Using format()
    str += '{0}'
    list = [str.format(i) for i in list]
    return(list)


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
    for i in sorted(formatted_data.items()):
        table.add_row(i)
    print(table)


ants = str_insert(a, "m")

sensor_list = ["_ap_tiltmeter_read_error", "_dig_l_band_adc_hpol_rf_power_in", "_dig_l_band_adc_vpol_rf_power_in","_dig_u_band_adc_hpol_rf_power_in", "_dig_u_band_adc_hpol_rf_power_in",
                "_dig_l_band_rfcu_hpol_rf_power_in", "_dig_l_band_rfcu_vpol_rf_power_in", "_dig_u_band_rfcu_hpol_rf_power_in", "_dig_u_band_rfcu_vpol_rf_power_in"]

list_ = []

for i in ants:
    d = str_insert(sensor_list, str(i))
    list_.append(d)


flat_list = []
for sublist in list_:
    for item in sublist:
        flat_list.append(item)

flat_list = sorted(flat_list)
print(flat_list)

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


with verify_and_connect(opts) as kat:
    sleep(5)

    s = get_sensor_data(kat,flat_list)
    p = format_sensors(s, opts.return_faults)
    print_table(p)

