import pandas as pd
import numpy as np
import math
from collections import defaultdict

# Function to compute a euclidean distrance matrix from lat/lon
def compute_euclidean_distance_matrix(locations):
    """Creates callback to return distance between points."""
    distances = {}
    for from_counter, from_node in enumerate(locations):
        distances[from_counter] = {}
        for to_counter, to_node in enumerate(locations):
            if from_counter == to_counter:
                distances[from_counter][to_counter] = 0
            else:
                # Euclidean distance
                distances[from_counter][to_counter] = (int(
                    math.hypot((from_node[0] - to_node[0]),
                               (from_node[1] - to_node[1]))))
    return distances

# Function to display a long list of vehicles in a short dict of types and occurence
# [1, 1, 2, 2, 2, 3, 3, 3, 3, 7] -> {1: 2, 2: 3, 3: 4, 7: 1}
def count_occurrences(list):
    d = defaultdict(int)
    for item in list:
        d[item] += 1
    return dict(d)

# Function to generate list of vehicles from list of vehicle types
# [2, 3, 4, 0, 0, 0, 1] -> [1, 1, 2, 2, 2, 3, 3, 3, 3, 7]
def generate_vehicles(list):
    out_list = []
    for id, num in enumerate(list):
        for x in range(num*2): # Double the amount to allow for two routes per vehicle (morning+evening)
            out_list.append(id+1)
    return out_list

def time_to_int(time):
    hours = int(time[0:2])
    minutes = int(time[3:5])
    seconds = int(time[6:8])
    return (hours*3600 + minutes*60 + seconds)

def int_to_time(seconds):
    hours = math.floor(seconds/3600)
    hours_str = hours if hours>9 else f'0{hours}'
    seconds -= hours*3600
    minutes = math.floor(seconds/60)
    minutes_str = minutes if minutes>9 else f'0{minutes}'
    seconds -= minutes*60
    seconds_str = seconds if seconds>9 else f'0{seconds}'
    return f'{hours_str}:{minutes_str}:{seconds_str}'

def get_nodes(city):
    return pd.read_csv(f'./instances/{city}.nodes', sep=' ')

def get_routes(city):
    return pd.read_csv(f'./instances/{city}.routes', sep=' ')

def get_distance_matrix_from_routes(routes, num_nodes, dist_type):
    # Returns distance matrix computed from custom .routes format
    valid = ['Total', 'Inside', 'Outside']
    if dist_type not in valid:
        raise ValueError(f"{dist_type} is not a valid distance type.\nAcceptable values are: {valid}")
    km_list = routes[f'Distance{dist_type}[km]']
    m_list = [int(1000 * x) for x in km_list] 
    # km_matrix = list(zip(*([iter(routes[f'Distance{dist_type}[km]'])]*num_nodes)))
    m_matrix = list(zip(*([iter(m_list)]*num_nodes)))
    return m_matrix

def get_time_matrix_from_routes(routes, num_nodes):
    # Returns distance matrix computed from custom .routes format
    time_list = routes['Duration[s]']
    s_list = [time_to_int(x) for x in time_list]
    s_matrix = list(zip(*([iter(s_list)]*num_nodes)))
    return s_matrix

def get_time_list_from_nodes(nodes):
    # Returns list of times taken for serving each node in nodes
    time_list = nodes['Duration']
    s_list = [time_to_int(x) for x in time_list]
    return s_list