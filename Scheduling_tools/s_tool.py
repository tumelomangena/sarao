import numpy as np
import pandas as pd


def nightobs(filename, datefile):
    """Extracting only night time observations\
    from a given file of observational information
    
        Parmeters:
    -------------
    filename : csv file
        file containing all observations
    s_rise : float
        LST sun rise
    """
    
    ndates = []
    for j in range(len(datefile)):
        ndates.append(datefile[j].strftime('%Y-%m-%d'))
    data = pd.read_csv(filename)
    night_obs = data['night_obs']
    LST_starts = data['lst_start']
    LST_ends = data['lst_start_end']
    duration = data['simulated_duration']
    proposal_id = data['proposal_id']
    #proposal_id = sorted(proposal_id)
    ID = data['id']
    
    obs = {}
    for i in range(len(night_obs)):
        if night_obs[i] == 'Yes':
            obs[ID[i]] = [proposal_id[i],LST_starts[i],LST_ends[i],duration[i]]
    return obs, ndates


def format_params(obs):
    
    duration_ = []
    LST_start = []
    LST_end = []
    obs_id = []
    for i in obs.values():
        duration_.append(round(i[3]/3600,2))    
        g1 = i[1].replace(':', '.')
        f1 = float(g1)
        LST_start.append(f1)
        g2 = i[2].replace(':', '.') 
        f2 = float(g2)
        LST_end.append(f2)
        obs_id.append(i[0])

    duration_ = [0 if math.isnan(x) else x for x in duration_]

    return LST_start, LST_end, duration_, obs_id