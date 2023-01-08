import pandas as pd
import math
from collections import defaultdict

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

def count_occurrences(list):
    d = defaultdict(int)
    for item in list:
        d[item] += 1
    return dict(d)

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