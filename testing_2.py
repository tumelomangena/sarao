#!/usr/bin/env python
# Observe a bandpass calibrator to establish some basic health
# properties of the MeerKAT telescope.

import itertools
import numpy as np
import time
import functions 
import scipy.ndimage
from prettytable import PrettyTable
from colorama import Fore
from json import load as load_json
from time import sleep
from katcorelib.observe import (standard_script_options, verify_and_connect,
                                collect_targets, start_session, user_logger, SessionSDP, CalSolutionsUnavailable)

#from scikits.fitting import ScatterFit, GaussianFit
#from katpoint import (rad2deg, deg2rad, lightspeed, wrap_angle,
#                      RefractionCorrection)





# Group the frequency channels into this many sections to obtain pointing fits
NUM_CHUNKS = 16
            


class NoTargetsUpError(Exception):
    """No targets are above the horizon at the start of the observation."""


# Set up standard script options
usage = "%prog [options] <'target/catalogue'> [<'target/catalogue'> ...]"
description = 'Observe a bandpass calibrator to establish some ' \
              'basic health properties of the MeerKAT system.'
parser = standard_script_options(usage, description)
# Add experiment-specific options
parser.add_option('--verify-duration', type='float', default=64.0,
                  help='Length of time to revisit source for verification, '
                       'in seconds (default=%default)')
parser.add_option('--fengine-gain', type='int_or_default', default='default',
                  help='Set correlator F-engine gain (average magnitude)')
parser.add_option('-t', '--track-duration', type='float', default=32.0,
                  help='Length of time to track the source for calibration, '
                       'in seconds (default=%default)')
parser.add_option('--fft-shift', type='int_or_default', default='default',
                  help='Set correlator F-engine FFT shift')
parser.add_option('--reset-delays', action='store_true', default=False,
                  help='Zero the delay adjustments afterwards (i.e. check only)')
parser.add_option('--reconfigure-sdp', action="store_true", default=False,
                  help='Reconfigure SDP subsystem at the start to clear '
                       'crashed containers or to load a new version of SDP')
#parser.add_option('-t', '--track-duration', type='float', default=16.0,
#                  help='Duration of each offset pointing, in seconds (default=%default)')
parser.add_option('--max-extent', type='float', default=1.0,
                  help='Maximum distance of offset from target, in degrees')
parser.add_option('--pointings', type='int', default=10,
                  help='Number of offset pointings')
parser.add_option('--flatten-bandpass', action='store_true', default=False,
                  help='Apply bandpass magnitude correction on top of phase correction')
parser.add_option('--random-phase', action='store_true', default=False,
                  help='Apply random phases in F-engine (incoherent beamformer)')
parser.add_option('--disable-hv-correction', action='store_true', default=False,
                  help='Do not correct HV phase (but still fire the noise diode)')
parser.add_option('--max-gap-MHz', type='float', default=128.0,
                  help='The maximum gap in the bandpass gain that will still be '
                       'interpolated across, in MHz (default=%default)')


# Set default value for any option (both standard and experiment-specific options)
parser.set_defaults(observer='basic_health', nd_params='off',
                    project_id='MKAIV-308', reduction_label='MKAIV-308',
                    description='Basic health test of the system.',
                    horizon=25, track_duration=64)
# Parse the command line
opts, args = parser.parse_args()

if len(args) == 0:
    raise ValueError("Please specify at least one target argument via name "
                     "('J1939-6342'), description ('radec, 19:39, -63:42') or "
                     "catalogue file name ('three_calib.csv')")

# Build up sequence of pointing offsets running linearly in x and y directions
scan = np.linspace(-opts.max_extent, opts.max_extent, opts.pointings // 2)
offsets_along_x = np.c_[scan, np.zeros_like(scan)]
offsets_along_y = np.c_[np.zeros_like(scan), scan]
offsets = np.r_[offsets_along_y, offsets_along_x]
offset_end_times = np.zeros(len(offsets))
middle_time = 0.0
weather = {}

# ND states
nd_off = {'diode': 'coupler', 'on': 0., 'off': 0., 'period': -1.}
nd_on = {'diode': 'coupler', 'on': opts.track_duration, 'off': 0., 'period': 0.}

# antennas representation
a = ["{0:03}".format(i) for i in range(65)] 
ants = ["m{}".format(i) for i in a]
band = ["l","u"]

def sensor_format(band, ants):
    sensors_lists = []
    for j in band:
        sen = [["{}_dig_{}_band_adc_hpol_rf_power_in".format(i,j) for i in ants],
        ["{}_dig_{}_band_adc_vpol_rf_power_in".format(i,j) for i in ants],
        ["{}_dig_{}_band_rfcu_hpol_rf_power_in".format(i,j) for i in ants],
        ["{}_dig_{}_band_rfcu_vpol_rf_power_in".format(i,j) for i in ants],
        ["{}_ap_tiltmeter_read_error".format(i) for i in ants]]
        sensors_lists.append(sen)
    sensors_l = list(itertools.chain(*sensors_lists))
    sensors = list(itertools.chain(*sensors_l))
 
    return sensors

# accessing sensor file
with open("/home/kat/usersnfs/tumelo/sensors.json", "r") as read_file:
    sensors = load_json(read_file)
    tfr_sensors = sensors['tfr_device_status']
    cbf_sensors = sensors['cbf_device_status']
    sdp_sensors = sensors['sdp_device_status']
    

# Check options and build KAT configuration, connecting to proxies and devices
with verify_and_connect(opts) as kat:

#=======================sensor information===================================
    sleep(5)

    data_tfr = functions.get_sensor_data(kat.tfrmon, tfr_sensors)
    #data_sdp = functions.get_sensor_data(kat, sdp_sensors)
    #data_cbf = functions.get_sensor_data(kat, cbf_sensors)
    ants_s = sensor_format(band, ants)
    data_ants = functions.get_sensor_data(kat, ants_s)
    data_cbf = functions.get_sensor_data(kat.cbf, cbf_sensors)

    sleep(5)

    data_t = functions.format_sensors(data_tfr)
    #data_s = functions.format_sensors(data_sdp)
    data_c = functions.format_sensors(data_cbf)
    data_a = functions.format_sensors(data_ants)
 #   data_c = functions.format_sensors(data_cbf)
    sleep(5)

    user_logger.info("Checking problematic device status system sensors ")
    functions.print_table(data_t)
    #functions.print_table(data_s)
    functions.print_table(data_c)
    functions.print_table(data_a)



    if opts.reconfigure_sdp:
        user_logger.info("Reconfiguring SDP subsystem")
        sdp = SessionSDP(kat)
        sdp.req.product_reconfigure(timeout=300)  # Same timeout as in SDP proxy

    observation_sources = collect_targets(kat, args)
    user_logger.info(observation_sources.visibility_list())
    # Start capture session
    with start_session(kat, **vars(opts)) as session:
        session.standard_setup(**vars(opts))
        # Reset F-engine to a known good state first
        session.set_fengine_fft_shift(opts.fft_shift)
        session.set_fengine_gains(opts.fengine_gain)
        session.adjust_fengine_delays(0)

        if opts.fft_shift is not None:
            session.set_fengine_fft_shift(opts.fft_shift)
        fengine_gain = session.set_fengine_gains(opts.fengine_gain)
        # Quit if there are no sources to observe or not enough antennas for cal
        if len(session.ants) < 4:
            raise ValueError('Not enough receptors to do calibration - you '
                             'need 2 and you have %d' % (len(session.ants),))
        sources_above_horizon = observation_sources.filter(el_limit_deg=opts.horizon)
        if not sources_above_horizon:
            raise NoTargetsUpError("No targets are currently visible - "
                                   "please re-run the script later")
        # Pick the first source that is up (this assumes that the sources in
        # the catalogue are ordered from highest to lowest priority)
        target = sources_above_horizon.targets[0]
        target.add_tags('bfcal single_accumulation')
        session.capture_start()
        # Calibration tests
        user_logger.info("Performing calibration tests")
        session.label('calibration')
        user_logger.info("Initiating %g-second track on target '%s'",
                         opts.track_duration, target.name)
        session.track(target, duration=opts.track_duration, announce=False)
        # Fire noise diode during track
        session.fire_noise_diode(on=opts.track_duration, off=0)
        # Attempt to jiggle cal pipeline to drop its gains
        session.stop_antennas()
        user_logger.info("Waiting for gains to materialise in cal pipeline")
        # Wait for the last bfcal product from the pipeline
        hv_delays = session.get_cal_solutions('KCROSS_DIODE', timeout=300.)
        delays = session.get_cal_solutions('K')
        # Add HV delay to total delay
        for inp in delays:
            delays[inp] += hv_delays[inp]
        # The main course
        session.adjust_fengine_delays(delays)
        if opts.verify_duration > 0:
            session.label('corrected')
            user_logger.info("Revisiting target %r for %g seconds "
                             "to see if delays are fixed",
                             target.name, opts.verify_duration)
            session.track(target, duration=0, announce=False)
            session.fire_noise_diode(on=opts.verify_duration, off=0)
        if opts.reset_delays:
            session.adjust_fengine_delays(0)
        else:
            # Set last-delay-calibration script sensor on the subarray.
            session.sub.req.set_script_param('script-last-delay-calibration',
                                             kat.sb_id_code)
        #====================bf_phaseup====================================
        # Pick the first source that is up (this assumes that the sources in
        # the catalogue are ordered from highest to lowest priority)
        target = sources_above_horizon.targets[0]
        user_logger.info("Performing beamformer phaseup")
        target.add_tags('bfcal single_accumulation')
        session.capture_start()
        session.label('un_corrected')
        user_logger.info("Initiating %g-second track on target %r",
                         opts.track_duration, target.description)
        # Get onto the source
        session.track(target, duration=0, announce=False)
        # Fire noise diode during track
        session.fire_noise_diode(on=opts.track_duration, off=0)
        # Attempt to jiggle cal pipeline to drop its gain solutions
        session.stop_antennas()
        user_logger.info("Waiting for gains to materialise in cal pipeline")
        hv_gains = {}
        hv_delays = {}
        timeout = 60 + opts.track_duration
        # Wait for the last relevant bfcal product from the pipeline
        if opts.disable_hv_correction:
            user_logger.warning('HV phase correction disabled by script option')
        else:
            try:
                hv_gains = session.get_cal_solutions('BCROSS_DIODE_SKY', timeout)
            except CalSolutionsUnavailable as err:
                user_logger.warning("No BCROSS_DIODE_SKY solutions found - "
                                    "falling back to BCROSS_DIODE only: %s", err)
                hv_gains = session.get_cal_solutions('BCROSS_DIODE')
            hv_delays = session.get_cal_solutions('KCROSS_DIODE')
            timeout = 0.0
        gains = session.get_cal_solutions('G', timeout)
        bp_gains = session.get_cal_solutions('B')
        delays = session.get_cal_solutions('K')
        # Add HV delay to the usual delay
        for inp in sorted(delays):
            delays[inp] += hv_delays.get(inp, 0.0)
            if np.isnan(delays[inp]):
                user_logger.warning("Delay fit failed on input %s (all its "
                                    "data probably flagged)", inp)
        # Add HV phase to bandpass phase
        for inp in bp_gains:
            bp_gains[inp] *= hv_gains.get(inp, 1.0)
        cal_channel_freqs = session.get_cal_channel_freqs()
        bp_gains = functions.clean_bandpass(bp_gains, cal_channel_freqs, max_gap_Hz=opts.max_gap_MHz*1e6)

        if opts.random_phase:
            user_logger.warning("Setting F-engine gains with random phases "
                                "(you asked for it)")
        else:
            user_logger.info("Setting F-engine gains to phase up antennas")
        if not kat.dry_run:
            corrections = functions.calculate_corrections(gains, bp_gains, delays,
                                                cal_channel_freqs, opts.random_phase,
                                                opts.flatten_bandpass, fengine_gain)
            session.set_fengine_gains(corrections)
        if opts.verify_duration > 0:
            session.label('corrected')
            user_logger.info("Revisiting target %r for %g seconds to verify "
                             "phase-up", target.name, opts.verify_duration)
            session.track(target, duration=0, announce=False)
            session.fire_noise_diode(on=opts.verify_duration, off=0)

        if not opts.random_phase:
            # Set last-phaseup script sensor on the subarray.
            session.sub.req.set_script_param('script-last-phaseup', kat.sb_id_code)
        if not opts.dry_run:
            session.get_precise_time_reading('wide_tied_array_channelised_voltage_0x',
                                                 timeout=90)
            session.get_precise_time_reading('wide_tied_array_channelised_voltage_0y',
                                                 timeout=90)

        #=========================interferometric pointing======================================
        user_logger.info("Performing interferometric pointing tests")
        session.label('interferometric_pointing')
        session.capture_start()
        # XXX Eventually pick closest source as our target, now take first one
        target = observation_sources.targets[0]
        target.add_tags('bfcal single_accumulation')
        session.label('interferometric_pointing')
        user_logger.info("Initiating interferometric pointing scan on target "
                         "'%s' (%d pointings of %g seconds each)",
                         target.name, len(offsets), opts.track_duration)
        session.track(target, duration=0, announce=False)
        # Point to the requested offsets and collect extra data at middle time
        for n, offset in enumerate(offsets):
            user_logger.info("initiating track on offset of (%g, %g) degrees", *offset)
            session.ants.req.offset_fixed(offset[0], offset[1], opts.projection)
            session.track(target, duration=opts.track_duration, announce=False)
            offset_end_times[n] = time.time()
            if not kat.dry_run and n == len(offsets) // 2 - 1:
                # Get weather data for refraction correction at middle time
                temperature = kat.sensor.anc_air_temperature.get_value()
                pressure = kat.sensor.anc_air_pressure.get_value()
                humidity = kat.sensor.anc_air_relative_humidity.get_value()
                weather = {'temperature': temperature, 'pressure': pressure,
                           'humidity': humidity}
                middle_time = offset_end_times[n]
                user_logger.info("reference time = %.1f, weather = "
                                 "%.1f deg C | %.1f hPa | %.1f %%",
                                 middle_time, temperature, pressure, humidity)
        # Clear offsets in order to jiggle cal pipeline to drop its final gains
        # XXX We assume that the final entry in `offsets` is not the origin
        user_logger.info("returning to target to complete the scan")
        session.ants.req.offset_fixed(0., 0., opts.projection)
        session.track(target, duration=0, announce=False)
        user_logger.info("Waiting for gains to materialise in cal pipeline")

        # Perform basic interferometric pointing reduction
        if not kat.dry_run:
            # Wait for last piece of the cal puzzle (crash if not on time)
            last_offset_start = offset_end_times[-1] - opts.track_duration
            session.get_cal_solutions('G', timeout=300.,
                                      start_time=last_offset_start)
            user_logger.info('Retrieving gains, fitting beams, storing offsets')
            data_points = functions.get_offset_gains(session, offsets, offset_end_times,
                                           opts.track_duration)
            beams = functions.fit_primary_beams(session, data_points)
            pointing_offsets = functions.calc_pointing_offsets(session, beams, target,
                                                     middle_time, **weather)
            functions.save_pointing_offsets(session, pointing_offsets, middle_time)

        # reset the gains 
        session.set_fengine_gains(opts.fengine_gain)
