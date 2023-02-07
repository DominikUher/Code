import pandas as pd
import numpy as np
import math
from collections import defaultdict
from ortools.constraint_solver import routing_enums_pb2
import matplotlib.pyplot as plt
from time import strftime, localtime


# Function to compute a euclidean distrance matrix from lat/lon
def compute_euclidean_distance_matrix(locations):
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
        for x in range(num):
            out_list.append(id+1)
    return out_list


# Function to convert from time (XX:XX:XX) to int time in seconds
def time_to_int(time):
    hours = int(time[0:2])
    minutes = int(time[3:5])
    seconds = int(time[6:8])
    return (hours*3600 + minutes*60 + seconds)


# Function to convert from integer seconds to time (XX:XX:XX)
def int_to_time(seconds):
    hours = math.floor(seconds/3600)
    hours_str = hours if hours>9 else f'0{hours}'
    seconds -= hours*3600
    minutes = math.floor(seconds/60)
    minutes_str = minutes if minutes>9 else f'0{minutes}'
    seconds -= minutes*60
    seconds_str = seconds if seconds>9 else f'0{seconds}'
    return f'{hours_str}:{minutes_str}:{seconds_str}'


# Function to read in node information regarding a city from /instances/ .nodes file
def get_nodes(city):
    return pd.read_csv(f'./instances/{city}.nodes', sep=' ')


# Function to read in route information reagrding a city from /instances/ .routes file
def get_routes(city):
    return pd.read_csv(f'./instances/{city}.routes', sep=' ')


# Function to calculate a distance matrix from .routes format data
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


# Function to get a time matrix from .routes format data
def get_time_matrix_from_routes(routes, num_nodes):
    # Returns distance matrix computed from custom .routes format
    time_list = routes['Duration[s]']
    s_list = [time_to_int(x) for x in time_list]
    s_matrix = list(zip(*([iter(s_list)]*num_nodes)))
    return s_matrix


# Function to get processing times for each node
def get_time_list_from_nodes(nodes):
    # Returns list of times taken for serving each node in nodes
    time_list = nodes['Duration']
    s_list = [time_to_int(x) for x in time_list]
    return s_list


# Function to write output data from routing to CSV file
def write_to_csv(csv, city, toll, timeout, time, routes):
    data_out = {
            'City': [city],
            'Toll [ct]': [toll],
            'Construction heuristic': [csv[5]],
            'Metaheuristic': [csv[6]],
            'Max_Time [s]': [timeout],
            'Actual_Time [s]': [time],
            'Total_Cost [€]': [csv[0]],
            'Fleet': [csv[1]],
            'Total_Weight [kg]': [csv[2]],
            'Total_Volume [m3]': [csv[3]],
            'Total_Distance [km]': [csv[4]],
            'Routes': routes
        }
    try:
        df = pd.DataFrame(data_out)
        df.to_csv(f'output/{city}_{toll}_{timeout}_FSS{csv[5]}_LSS{csv[6]}.csv', index=False, sep=';')
    except Exception as e:
        return f'Error: {e}\n'
    return 'Output written to CSV file\n'


# Function to perform sanity check on user-defined parameters to avoid running impossible searches
def check_infeasibility(vehicle_weights, vehicle_volumes, demand_weights, demand_volumes):
    available_weight = np.sum(vehicle_weights)
    available_volume = np.sum(vehicle_volumes)
    needed_weight = np.sum(demand_weights)
    needed_volume = np.sum(demand_volumes)
    if available_weight < needed_weight:
        return True, ['No solution possible!', '', f'Demanded weight {needed_weight/1000}kg > Available capacity {available_weight/1000}kg', '', 'No solution possible!', '', 'No solution possible due to insufficient weight capacity', False]
    elif available_volume < needed_volume:
        return True, ['No solution possible!', '', f'Demanded volume {needed_volume/1000}m3 > Available volume {available_volume/1000}m3', '', 'No solution possible!', '', 'No solution possible due to insufficient volume capacity', False]
    else:
        return False, ''


# Function to get correct index for solver from strategy name
def get_fss(new_fss):
    match new_fss:
        case 'Automatic FSS':
            fss = routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC
        case 'Path Cheapest Arc':
            fss = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        case 'Path Most Constrained Arc':
            fss = routing_enums_pb2.FirstSolutionStrategy.PATH_MOST_CONSTRAINED_ARC
        case 'Evaluator Strategy':
            fss = routing_enums_pb2.FirstSolutionStrategy.EVALUATOR_STRATEGY
        case 'Savings':
            fss = routing_enums_pb2.FirstSolutionStrategy.SAVINGS
        case 'Sweep':
            fss = routing_enums_pb2.FirstSolutionStrategy.SWEEP
        case 'Christofides':
            fss = routing_enums_pb2.FirstSolutionStrategy.CHRISTOFIDES
        case 'All Unperformed':
            fss = routing_enums_pb2.FirstSolutionStrategy.ALL_UNPERFORMED
        case 'Best Insertion':
            fss = routing_enums_pb2.FirstSolutionStrategy.BEST_INSERTION
        case 'Parallel Cheapest Insertion':
            fss = routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
        case 'Local Cheapest Insertion':
            fss = routing_enums_pb2.FirstSolutionStrategy.LOCAL_CHEAPEST_INSERTION
        case 'Global Cheapest Arc':
            fss = routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC
        case 'Local Cheapest Arc':
            fss = routing_enums_pb2.FirstSolutionStrategy.LOCAL_CHEAPEST_ARC
        case 'First Unbound Min Value':
            fss = routing_enums_pb2.FirstSolutionStrategy.FIRST_UNBOUND_MIN_VALUE
    return fss


# Function to get correct index for solver from strategy name
def get_lss(new_lss):    
    match new_lss:
        case 'Automatic LSS':
            lss = routing_enums_pb2.LocalSearchMetaheuristic.AUTOMATIC
        case 'Greedy Descent':
            lss = routing_enums_pb2.LocalSearchMetaheuristic.GREEDY_DESCENT
        case 'Guided Local Search':
            lss = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        case 'Simulated Annealing':
            lss = routing_enums_pb2.LocalSearchMetaheuristic.SIMULATED_ANNEALING
        case 'Tabu Search':
            lss = routing_enums_pb2.LocalSearchMetaheuristic.TABU_SEARCH
        case 'Generic Tabu Search':
            lss = routing_enums_pb2.LocalSearchMetaheuristic.GENERIC_TABU_SEARCH
    return lss

# Function to visualise routes taken and adapted from LiveCoding code by Gerhard Hiemann
# Each vehicle type should be plotted in a different base colour with variations between vehicles 
def draw_routes(types: list[int], types_seq: list[int], routes: list[list[int]], nodes: dict, city: str):
    # Keep track of how many types have been seen already / where in the color scheme we are
    # Start all at 3, to avoid getting very light line colours on white background
    types_seen = [3, 3, 3, 3, 3, 3, 3]

    # Define colour schemes for vehicles (plus 6 to skip first and last three entries as they are too light/dark to distinguish)
    colors = [plt.cm.get_cmap('Greys', types[0]+6),
        plt.cm.get_cmap('Reds', types[1]+6),
        plt.cm.get_cmap('RdPu', types[2]+6),
        plt.cm.get_cmap('Greens', types[3]+6),
        plt.cm.get_cmap('Blues', types[4]+6),
        plt.cm.get_cmap('Purples', types[5]+6),
        plt.cm.get_cmap('cool', types[6]+6)]

    time = strftime('%H:%M:%S', localtime())
    fig, ax = plt.subplots(num=f'Routes calculated for {city} at {time}')
    fig.tight_layout()
    ax.axis('equal')
    plt.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
    plt.tick_params(axis='y', which='both', right=False, left=False, labelleft=False)

    for id, route in enumerate(routes):
        path = list()
        for node in range(len(route)):
            path.append((nodes.Lon.iat[route[node]], nodes.Lat.iat[route[node]]))
        # plot control points and connecting lines
        x, y = zip(*path)
        vtype = types_seq[id]
        line, = ax.plot(x, y, 'o-', color=colors[vtype-1](types_seen[vtype-1]), label=f'{id+1}: {vtype}')
        types_seen[vtype-1] += 1
    plt.legend(loc='center right', bbox_to_anchor=(0.15, 0.5), bbox_transform=fig.transFigure)
    for pos in ['right', 'top', 'bottom', 'left']:
        plt.gca().spines[pos].set_visible(False)
        
    plt.show(block=False)