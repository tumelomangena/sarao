import numpy as np
import scipy.ndimage
import time
from prettytable import PrettyTable
from colorama import Fore
from json import load as load_json
from time import sleep
from katcorelib.observe import (standard_script_options, verify_and_connect,
                                collect_targets, start_session, user_logger,
                                CalSolutionsUnavailable)

from scikits.fitting import ScatterFit, GaussianFit
from katpoint import (rad2deg, deg2rad, lightspeed, wrap_angle,
                      RefractionCorrection)

# Group the frequency channels into this many sections to obtain pointing fits
NUM_CHUNKS = 16

#=====================================subsystem sensors===========================================
def get_sensor_data(proxy, sensors):
    """Returns sensor-status pairs for a given proxy and list of sensors"""
    sensor_data = {}
    for sen in sensors:
        try:
            sensor_data[sen] = proxy.sensors[sen].get_status()
        except Exception:
            sensor_data[sen] = None
    return sensor_data

def format_sensors(sensor_data):
    for k in sensor_data.keys():
        if sensor_data[k] == 'error':
            sensor_data[k] = Fore.RED + str(sensor_data[k]) + Fore.RESET
        if sensor_data[k]  == 'warn':
            sensor_data[k] = Fore.YELLOW + str(sensor_data[k]) + Fore.RESET
        if sensor_data[k]  == 'unknown':
            sensor_data[k] = Fore.WHITE + str(sensor_data[k]) + Fore.RESET
        if sensor_data[k]  == 'failure':
            sensor_data[k] = Fore.BLUE + str(sensor_data[k]) + Fore.RESET

        return {k:v for (k,v) in sensor_data.items() if v!='nominal'}


def print_table(data):
    table = PrettyTable()
    table.field_names = ['sensor', 'status']
    for i in data.items():
        table.add_row(i)
    print(table)



def str_insert(list, str):
    # Using format()
    str += '{0}'
    list = [str.format(i) for i in list]
    return(list)

#=====================================beamformer phaseup===========================================
def clean_bandpass(bp_gains, cal_channel_freqs, max_gap_Hz):
    """Clean up bandpass gains by linear interpolation across narrow flagged regions."""
    clean_gains = {}
    # Linearly interpolate across flagged regions as long as they are not too large
    for inp, bp in bp_gains.items():
        flagged = np.isnan(bp)
        if flagged.all():
            clean_gains[inp] = bp
            continue
        chans = np.arange(len(bp))
        interp_bp = np.interp(chans, chans[~flagged], bp[~flagged])
        # Identify flagged regions and tag each with unique integer label
        gaps, n_gaps = scipy.ndimage.label(flagged)
        for n in range(n_gaps):
            gap = np.nonzero(gaps == n + 1)[0]
            gap_freqs = cal_channel_freqs[gap]
            lower = gap_freqs.min()
            upper = gap_freqs.max()
            if upper - lower > max_gap_Hz:
                interp_bp[gap] = np.nan
        clean_gains[inp] = interp_bp
    return clean_gains


def calculate_corrections(G_gains, B_gains, delays, cal_channel_freqs,
                          random_phase, flatten_bandpass,
                          target_average_correction):
    """Turn cal pipeline products into corrections to be passed to F-engine."""
    average_gain = {}
    gain_corrections = {}
    # First find relative corrections per input with arbitrary global average
    for inp in G_gains:
        # Combine all calibration products for input into single array of gains
        K_gains = np.exp(-2j * np.pi * delays[inp] * cal_channel_freqs)
        gains = K_gains * B_gains[inp] * G_gains[inp]
        if np.isnan(gains).all():
            average_gain[inp] = gain_corrections[inp] = 0.0
            continue
        abs_gains = np.abs(gains)
        # Track the average gain to fix overall power level (and as diagnostic)
        average_gain[inp] = np.nanmedian(abs_gains)
        corrections = 1.0 / gains
        if not flatten_bandpass:
            # Let corrections have constant magnitude equal to 1 / (avg gain),
            # which ensures that power levels are still equalised between inputs
            corrections *= abs_gains / average_gain[inp]
        if random_phase:
            corrections *= np.exp(2j * np.pi * np.random.rand(len(corrections)))
        gain_corrections[inp] = np.nan_to_num(corrections)
    # All invalid gains (NaNs) have now been turned into zeros
    valid_average_gains = [g for g in average_gain.values() if g > 0]
    if not valid_average_gains:
        raise ValueError("All gains invalid and beamformer output will be zero!")
    global_average_gain = np.median(valid_average_gains)

    # Iterate over inputs again and fix average values of corrections
    for inp in sorted(G_gains):
        relative_gain = average_gain[inp] / global_average_gain
        if relative_gain == 0.0:
            user_logger.warning("%s has no valid gains and will be zeroed", inp)
            continue
        # This ensures that input at the global average gets target correction
        gain_corrections[inp] *= target_average_correction * global_average_gain
        safe_relative_gain = np.clip(relative_gain, 0.5, 2.0)
        if relative_gain == safe_relative_gain:
            user_logger.info("%s: average gain relative to global average = %5.2f",
                             inp, relative_gain)
        else:
            user_logger.warning("%s: average gain relative to global average "
                                "= %5.2f out of range, clipped to %.1f",
                                inp, relative_gain, safe_relative_gain)
            gain_corrections[inp] *= relative_gain / safe_relative_gain
    return gain_corrections





#===============================reference poitning======================================

def get_offset_gains(session, offsets, offset_end_times, track_duration):
    """Extract gains per pointing offset, per receptor and per frequency chunk.

    Parameters
    ----------
    session : :class:`katcorelib.observe.CaptureSession` object
        The active capture session
    offsets : sequence of *N* pairs of float (i.e. shape (*N*, 2))
        Requested (x, y) pointing offsets relative to target, in degrees
    offset_end_times : sequence of *N* floats
        Unix timestamp at the end of each pointing track
    track_duration : float
        Duration of each pointing track, in seconds

    Returns
    -------
    data_points : dict mapping receptor index to (x, y, freq, gain, weight) seq
        Complex gains per receptor, as multiple records per offset and frequency

    """
    cal_channel_freqs = session.get_cal_channel_freqs()
    chunk_freqs = cal_channel_freqs.reshape(NUM_CHUNKS, -1).mean(axis=1)
    pols = session.telstate['cal_pol_ordering']
    data_points = {}
    # Iterate over offset pointings
    for offset, offset_end in zip(offsets, offset_end_times):
        offset_start = offset_end - track_duration
        # Obtain interferometric gains per pointing from the cal pipeline
        try:
            bp_gains = session.get_cal_solutions('B', start_time=offset_start,
                                                 end_time=offset_end)
            gains = session.get_cal_solutions('G', start_time=offset_start,
                                              end_time=offset_end)
        except CalSolutionsUnavailable as err:
            user_logger.warning('Skipping offset %s: %s', offset, err)
            continue
        # Iterate over receptors
        for a, ant in enumerate(session.observers):
            pol_gain = np.zeros(NUM_CHUNKS)
            pol_weight = np.zeros(NUM_CHUNKS)
            # Iterate over polarisations (effectively over inputs)
            for pol in pols:
                inp = ant.name + pol
                bp_gain = bp_gains.get(inp)
                gain = gains.get(inp)
                if bp_gain is None or gain is None:
                    continue
                masked_gain = np.ma.masked_invalid(bp_gain * gain)
                abs_gain_chunked = np.abs(masked_gain).reshape(NUM_CHUNKS, -1)
                abs_gain_mean = abs_gain_chunked.mean(axis=1)
                abs_gain_std = abs_gain_chunked.std(axis=1)
                abs_gain_var = abs_gain_std.filled(np.inf) ** 2
                # Replace any zero variance with the smallest non-zero variance
                # across chunks, but if all are zero it is fishy and ignored.
                zero_var = abs_gain_var == 0.
                if all(zero_var):
                    abs_gain_var = np.ones_like(abs_gain_var) * np.inf
                else:
                    abs_gain_var[zero_var] = abs_gain_var[~zero_var].min()
                # Number of valid samples going into statistics
                abs_gain_N = (~abs_gain_chunked.mask).sum(axis=1)
                # Generate standard precision weights based on empirical stdev
                abs_gain_weight = abs_gain_N / abs_gain_var
                # Prepare some debugging output
                stats_mean = ' '.join("%4.2f" % (m,) for m in
                                      abs_gain_mean.filled(np.nan))
                stats_std = ' '.join("%4.2f" % (s,) for s in
                                     abs_gain_std.filled(np.nan))
                stats_N = ' '.join("%4d" % (n,) for n in abs_gain_N)
                bp_mean = np.nanmean(np.abs(bp_gain))
                user_logger.debug("%s %s %4.2f mean | %s",
                                  tuple(offset), inp, np.abs(gain), stats_mean)
                user_logger.debug("%s %s %4.2f std  | %s",
                                  tuple(offset), inp, bp_mean, stats_std)
                user_logger.debug("%s %s      N    | %s",
                                  tuple(offset), inp, stats_N)
                # Blend new gains into existing via weighted averaging.
                # XXX We currently combine HH and VV gains at the start to get
                # Stokes I gain but in future it might be better to fit
                # separate beams to HH and VV.
                pol_gain, pol_weight = np.ma.average(
                    np.c_[pol_gain, abs_gain_mean], axis=1,
                    weights=np.c_[pol_weight, abs_gain_weight], returned=True)
            if pol_weight.sum() > 0:
                # Turn masked values into NaNs pre-emptively to avoid warning
                # when recarray in beam fitting routine forces this later on.
                pol_gain = pol_gain.filled(np.nan)
                data = data_points.get(a, [])
                for freq, gain, weight in zip(chunk_freqs, pol_gain, pol_weight):
                    data.append((offset[0], offset[1], freq, gain, weight))
                data_points[a] = data
    if not data_points:
        raise CalSolutionsUnavailable("No complete gain solutions found in "
                                      "telstate for any offset")
    return data_points


def fwhm_to_sigma(fwhm):
    """Standard deviation of Gaussian function with specified FWHM beamwidth.

    This returns the standard deviation of a Gaussian beam pattern with a
    specified full-width half-maximum (FWHM) beamwidth. This beamwidth is the
    width between the two points left and right of the peak where the Gaussian
    function attains half its maximum value.

    """
    # Gaussian function reaches half its peak value at sqrt(2 log 2)*sigma
    return fwhm / 2.0 / np.sqrt(2.0 * np.log(2.0))


def sigma_to_fwhm(sigma):
    """FWHM beamwidth of Gaussian function with specified standard deviation.

    This returns the full-width half-maximum (FWHM) beamwidth of a Gaussian beam
    pattern with a specified standard deviation. This beamwidth is the width
    between the two points left and right of the peak where the Gaussian
    function attains half its maximum value.

    """
    # Gaussian function reaches half its peak value at sqrt(2 log 2)*sigma
    return 2.0 * np.sqrt(2.0 * np.log(2.0)) * sigma


class BeamPatternFit(ScatterFit):
    """Fit analytic beam pattern to total power data defined on 2-D plane.

    This fits a two-dimensional Gaussian curve (with diagonal covariance matrix)
    to total power data as a function of 2-D coordinates. The Gaussian bump
    represents an antenna beam pattern convolved with a point source.

    Parameters
    ----------
    center : sequence of 2 floats
        Initial guess of 2-element beam center, in target coordinate units
    width : sequence of 2 floats, or float
        Initial guess of single beamwidth for both dimensions, or 2-element
        beamwidth vector, expressed as FWHM in units of target coordinates
    height : float
        Initial guess of beam pattern amplitude or height

    Attributes
    ----------
    expected_width : real array, shape (2,), or float
        Initial guess of beamwidth, saved as expected width for checks
    radius_first_null : float
        Radius of first null in beam in target coordinate units (stored here for
        convenience, but not calculated internally)
    refined : int
        Number of scan-based baselines used to refine beam (0 means unrefined)
    is_valid : bool
        True if beam parameters are within reasonable ranges after fit
    std_center : array of float, shape (2,)
        Standard error of beam center, only set after :func:`fit`
    std_width : array of float, shape (2,), or float
        Standard error of beamwidth(s), only set after :func:`fit`
    std_height : float
        Standard error of beam height, only set after :func:`fit`

    """
    def __init__(self, center, width, height):
        ScatterFit.__init__(self)
        if not np.isscalar(width):
            width = np.atleast_1d(width)
        self._interp = GaussianFit(center, fwhm_to_sigma(width), height)
        self.center = self._interp.mean
        self.width = sigma_to_fwhm(self._interp.std)
        self.height = self._interp.height

        self.expected_width = width
        # Initial guess for radius of first null
        # XXX: POTENTIAL TWEAK
        self.radius_first_null = 1.3 * np.mean(self.expected_width)
        # Beam initially unrefined and invalid
        self.refined = 0
        self.is_valid = False
        self.std_center = self.std_width = self.std_height = None

    def fit(self, x, y, std_y=1.0):
        """Fit a beam pattern to data.

        The center, width and height of the fitted beam pattern (and their
        standard errors) can be obtained from the corresponding member variables
        after this is run.

        Parameters
        ----------
        x : array-like, shape (2, N)
            Sequence of 2-dimensional target coordinates (as column vectors)
        y : array-like, shape (N,)
            Sequence of corresponding total power values to fit
        std_y : float or array-like, shape (N,), optional
            Measurement error or uncertainty of `y` values, expressed as standard
            deviation in units of `y`

        """
        self._interp.fit(x, y, std_y)
        self.center = self._interp.mean
        self.width = sigma_to_fwhm(self._interp.std)
        self.height = self._interp.height
        self.std_center = self._interp.std_mean
        self.std_width = sigma_to_fwhm(self._interp.std_std)
        self.std_height = self._interp.std_height
        self.is_valid = not any(np.isnan(self.center)) and self.height > 0.
        # XXX: POTENTIAL TWEAK
        norm_width = self.width / self.expected_width
        self.is_valid &= all(norm_width > 0.9) and all(norm_width < 1.25)

    def __call__(self, x):
        """Evaluate fitted beam pattern function on new target coordinates.

        Parameters
        ----------
        x : array-like, shape (2, M)
            Sequence of 2-dimensional target coordinates (as column vectors)

        Returns
        -------
        y : array, shape (M,)
            Sequence of total power values representing fitted beam

        """
        return self._interp(x)


def fit_primary_beams(session, data_points):
    """Fit primary beams to receptor gains obtained at various offset pointings.

    Parameters
    ----------
    session : :class:`katcorelib.observe.CaptureSession` object
        The active capture session
    data_points : dict mapping receptor index to (x, y, freq, gain, weight) seq
        Complex gains per receptor, as multiple records per offset and frequency

    Returns
    -------
    beams : dict mapping receptor name to list of :class:`BeamPatternFit`
        Fitted primary beams, per receptor and per frequency chunk

    """
    beams = {}
    # Iterate over receptors
    for a in data_points:
        data = np.rec.fromrecords(data_points[a], names='x,y,freq,gain,weight')
        data = data.reshape(-1, NUM_CHUNKS)
        ant = session.observers[a]
        # Iterate over frequency chunks but discard typically dodgy band edges
        for chunk in range(1, NUM_CHUNKS - 1):
            chunk_data = data[:, chunk]
            is_valid = np.nonzero(~np.isnan(chunk_data['gain']) &
                                  (chunk_data['weight'] > 0.))[0]
            chunk_data = chunk_data[is_valid]
            if len(chunk_data) == 0:
                continue
            expected_width = rad2deg(ant.beamwidth * lightspeed /
                                     chunk_data['freq'][0] / ant.diameter)
            # Convert power beamwidth to gain / voltage beamwidth
            expected_width = np.sqrt(2.0) * expected_width
            # XXX This assumes we are still using default ant.beamwidth of 1.22
            # and also handles larger effective dish diameter in H direction
            expected_width = (0.8 * expected_width, 0.9 * expected_width)
            beam = BeamPatternFit((0., 0.), expected_width, 1.0)
            x = np.c_[chunk_data['x'], chunk_data['y']].T
            y = chunk_data['gain']
            std_y = np.sqrt(1. / chunk_data['weight'])
            try:
                beam.fit(x, y, std_y)
            except TypeError:
                continue
            beamwidth_norm = beam.width / np.array(expected_width)
            center_norm = beam.center / beam.std_center
            user_logger.debug("%s %2d %2d: height=%4.2f width=(%4.2f, %4.2f) "
                              "center=(%7.2f, %7.2f)%s",
                              ant.name, chunk, len(y), beam.height,
                              beamwidth_norm[0], beamwidth_norm[1],
                              center_norm[0], center_norm[1],
                              ' X' if not beam.is_valid else '')
            # Store beam per frequency chunk and per receptor
            beams_freq = beams.get(ant.name, [None] * NUM_CHUNKS)
            beams_freq[chunk] = beam
            beams[ant.name] = beams_freq
    return beams


def calc_pointing_offsets(session, beams, target, middle_time,
                          temperature, pressure, humidity):
    """Calculate pointing offsets per receptor based on primary beam fits.

    Parameters
    ----------
    session : :class:`katcorelib.observe.CaptureSession` object
        The active capture session
    beams : dict mapping receptor name to list of :class:`BeamPatternFit`
        Fitted primary beams, per receptor and per frequency chunk
    target : :class:`katpoint.Target` object
        The target on which offset pointings were done
    middle_time : float
        Unix timestamp at the middle of sequence of offset pointings, used to
        find the mean location of a moving target (and reference for weather)
    temperature, pressure, humidity : float
        Atmospheric conditions at middle time, used for refraction correction

    Returns
    -------
    pointing_offsets : dict mapping receptor name to offset data (10 floats)
        Pointing offsets per receptor in degrees, stored as a sequence of
          - requested (az, el) after refraction (input to the pointing model),
          - full (az, el) offset, including contributions of existing pointing
            model, any existing adjustment and newly fitted adjustment
            (useful for fitting new pointing models as it is independent),
          - full (az, el) adjustment on top of existing pointing model,
            replacing any existing adjustment (useful for reference pointing),
          - relative (az, el) adjustment on top of existing pointing model and
            adjustment (useful for verifying reference pointing), and
          - rough uncertainty (standard deviation) of (az, el) adjustment.

    """
    pointing_offsets = {}
    # Iterate over receptors
    for ant in sorted(session.observers):
        beams_freq = beams.get(ant.name, [])
        beams_freq = [b for b in beams_freq if b is not None and b.is_valid]
        if not beams_freq:
            user_logger.debug("%s had no valid primary beam fitted", ant.name)
            continue
        offsets_freq = np.array([b.center for b in beams_freq])
        offsets_freq_std = np.array([b.std_center for b in beams_freq])
        weights_freq = 1. / offsets_freq_std ** 2
        # Do weighted average of offsets over frequency chunks
        results = np.average(offsets_freq, axis=0, weights=weights_freq,
                             returned=True)
        pointing_offset = results[0]
        pointing_offset_std = np.sqrt(1. / results[1])
        user_logger.debug("%s x=%+7.2f'+-%.2f\" y=%+7.2f'+-%.2f\"", ant.name,
                          pointing_offset[0] * 60, pointing_offset_std[0] * 3600,
                          pointing_offset[1] * 60, pointing_offset_std[1] * 3600)
        # Get existing pointing adjustment
        receptor = getattr(session.kat, ant.name)
        az_adjust = receptor.sensor.pos_adjust_pointm_azim.get_value()
        el_adjust = receptor.sensor.pos_adjust_pointm_elev.get_value()
        existing_adjustment = deg2rad(np.array((az_adjust, el_adjust)))
        # Start with requested (az, el) coordinates, as they apply
        # at the middle time for a moving target
        requested_azel = target.azel(timestamp=middle_time, antenna=ant)
        # Correct for refraction, which becomes the requested value
        # at input of pointing model
        rc = RefractionCorrection()
        def refract(az, el):  # noqa: E306, E301
            """Apply refraction correction as at the middle of scan."""
            return [az, rc.apply(el, temperature, pressure, humidity)]
        refracted_azel = np.array(refract(*requested_azel))
        # More stages that apply existing pointing model and/or adjustment
        pointed_azel = np.array(ant.pointing_model.apply(*refracted_azel))
        adjusted_azel = pointed_azel + existing_adjustment
        # Convert fitted offset back to spherical (az, el) coordinates
        pointing_offset = deg2rad(np.array(pointing_offset))
        beam_center_azel = target.plane_to_sphere(*pointing_offset,
                                                  timestamp=middle_time,
                                                  antenna=ant)
        # Now correct the measured (az, el) for refraction and then apply the
        # existing pointing model and adjustment to get a "raw" measured
        # (az, el) at the output of the pointing model stage
        beam_center_azel = refract(*beam_center_azel)
        beam_center_azel = ant.pointing_model.apply(*beam_center_azel)
        beam_center_azel = np.array(beam_center_azel) + existing_adjustment
        # Make sure the offset is a small angle around 0 degrees
        full_offset_azel = wrap_angle(beam_center_azel - refracted_azel)
        full_adjust_azel = wrap_angle(beam_center_azel - pointed_azel)
        relative_adjust_azel = wrap_angle(beam_center_azel - adjusted_azel)
        # Cheap 'n' cheerful way to convert cross-el uncertainty to azim form
        offset_azel_std = pointing_offset_std / \
            np.array([np.cos(refracted_azel[1]), 1.])
        # We store all variants of the pointing offset since we have it all
        # at our fingertips here
        point_data = np.r_[rad2deg(refracted_azel), rad2deg(full_offset_azel),
                           rad2deg(full_adjust_azel),
                           rad2deg(relative_adjust_azel), offset_azel_std]
        pointing_offsets[ant.name] = point_data
    return pointing_offsets


def save_pointing_offsets(session, pointing_offsets, middle_time):
    """Save pointing offsets to telstate and display to user.

    Parameters
    ----------
    session : :class:`katcorelib.observe.CaptureSession` object
        The active capture session
    pointing_offsets : dict mapping receptor name to offset data (10 floats)
        Pointing offsets per receptor, in degrees
    middle_time : float
        Unix timestamp at the middle of sequence of offset pointings

    """
    # Pointing adjustments go into root view as other capture blocks need it
    telstate = session.telstate.root()
    user_logger.info("Ant  refracted (az, el)     relative adjustment")
    user_logger.info("---- --------------------   --------------------")
    for ant in sorted(session.observers):
        try:
            offsets = pointing_offsets[ant.name].copy()
        except KeyError:
            user_logger.warn('%s had no valid primary beam fitted', ant.name)
        else:
            sensor_name = '%s_pointing_offsets' % (ant.name,)
            telstate.add(sensor_name, offsets, middle_time)
            # Display all offsets in arcminutes
            offsets[2:] *= 60.
            user_logger.info("%s (%+6.2f, %5.2f) deg -> (%+7.2f', %+7.2f')",
                             ant.name, *offsets[[0, 1, 6, 7]])



