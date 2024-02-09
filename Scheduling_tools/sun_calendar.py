import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt
#import datetime
import katpoint
import numpy as np
import time as time
import pandas as pd
import math
import colorama
from colorama import Fore
import pytest
from datetime import date 


def rise_set(timestamp):
    site = katpoint.Antenna("m000, -30:42:39.8, 21:26:38.0, 1086.6, 13.5") # the site position using one antenna(m000)
    site.observer.date=katpoint.Timestamp(timestamp).to_ephem_date() # Set time
    site.observer.horizon='00:00:00.0' # Set horizon
    observer = site.observer 
    Sun = katpoint.Target("Sun,special")# Make sun object
    ephem_sun = Sun.body #Sun as an object
    ephem_sun.compute(observer) #compute for position of the observer
    return observer.next_rising(ephem_sun),observer.next_setting(ephem_sun)


def sun_set_rise(start_date, end_date):
    
    date_start = dt.datetime.strptime(start_date, '%Y-%m-%d')
    date_end = dt.datetime.strptime(end_date, '%Y-%m-%d')

    date1 = date(date_start.year, date_start.month, date_start.day)
    date2 = date(date_end.year, date_end.month, date_end.day)
    delta = date2 - date1
    days = delta.days
    
    settime, risetime = np.zeros((days,1)),np.zeros((days,1))
    site = katpoint.Antenna("m000, -30:42:39.8, 21:26:38.0, 1086.6, 13.5")
    S = []
    R = []
    D = []
    for day in range(1, days):
        time_ = dt.datetime(date_start.year, date_start.month, day)
        t = dt.datetime.timestamp(time_)
        if day == 1:
            timestamp = t
        else:
            timestamp = t + 24*60*60*day
        rise_time, set_time = rise_set(timestamp)
        risetime[day] = np.degrees(site.local_sidereal_time(rise_time))/15.
        settime[day] = np.degrees(site.local_sidereal_time(set_time))/15.
        S.append(settime[day])
        R.append(risetime[day])
        D.append(time_)
        
    calender = [{"date": D,
        "lst_sunrise":R,
        "lst_sunset": S}
               ]
        
    return calender


def get_nighttime(riset,sett):
    'Arranging LST rise and set time to show night time '
    ind1 = 0
    ind2 = -1
       
    rt_new = np.delete(riset, ind1)
    st_new = np.delete(sett,ind2)
    set_rise = {}
    for i in range(len(riset)-1):
        set_rise[i] = [st_new[i],rt_new[i]]
    return set_rise

