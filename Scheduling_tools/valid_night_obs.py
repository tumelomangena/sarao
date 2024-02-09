import datetime as dt
import katpoint
import numpy as np
import time as time
import pandas as pd
import colorama
from colorama import Fore
import pytest


def obs_selection(s_set, s_rise, start_r, end_r, dur, observation_name):
    """ Check if the observation time range is within the LST time range.
    
    Parmeters:
    -------------
    s_set : float
        LST sun set
    s_rise : float
        LST sun rise
    start_r : float
        observation allowed start LST range
    end_r : float
        observation allowed end LST range
    dur : float 
        observation duration in hours
    """
    # check if observation start or end time is within the LST range
    cond1 = start_r >= s_set
    cond2 = end_r > s_set
    if  cond1 or cond2:
        if (cond1 and cond2) or cond1:
            start_time = start_r
            end_time = start_time + dur
        else:
            start_time = end_r
            end_time = start_time + dur
        if end_time > s_rise and end_time >= 24:
            return False
        else:
            if end_time >= 24:
                end_time = end_time - 24
    else:
        return False
    
    
    return observation_name



    
