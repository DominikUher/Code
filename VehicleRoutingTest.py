""" This code is based on and adapted from the OR-Tools example for Capacited Vehicles Routing Problem (CVRP) """
""" Please find the original code here: https://developers.google.com/optimization/routing/cvrp#entire_program """
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import ortools.constraint_solver.routing_parameters_pb2
import time
import pandas as pd
import numpy as np
from utils import *

vehicles = np.repeat(np.arange(1, 8), 10) # TODO: hardcoded for now, make editable alter
num_vehicles = len(vehicles)
city = 'NewYork' # TODO: hardcoded for now, make editable later
    

def create_data_model():
    # Carrier characteristics
    carriers = {}
    carriers['ids'] = [1, 2, 3, 4, 5, 6, 7]
    carriers['payloads'] = [2800000, 883000, 670000, 2800000, 905000, 720000, 100000] # in g
    carriers['volumes'] = [34800, 5800, 3200, 21560, 7670, 4270, 200] # in liters
    carriers['cpkm_inside'] = [1, 1, 1, 1, 1, 1, 1]
    carriers['cpkm_outside'] = [1, 1, 1, 1, 1, 1, 1]

    # Stores the data for the problem
    nodes = get_nodes(city)
    num_nodes = len(nodes.index)
    routes = get_routes(city)
    num_routes = len(routes.index)

    data = {}
    data['distance_total'] = get_distance_matrix_from_routes(routes, num_nodes, 'Total')
    data['distance_inside'] = get_distance_matrix_from_routes(routes, num_nodes, 'Inside')
    data['distance_outside'] = get_distance_matrix_from_routes(routes, num_nodes, 'Outside')
    data['demands_g'] = [d*1000 for d in nodes['Demand[kg]'].values]
    data['demands_liter'] = nodes['Demand[m^3*10^-3]'].values
    data['vehicle_payloads'] = [carriers['payloads'][i-1] for i in vehicles]
    data['vehicle_volumes'] = [carriers['volumes'][i-1] for i in vehicles]
    data['num_vehicles'] = num_vehicles
    data['depot'] = 0
    return data


def print_solution(data, manager, routing, solution):
    # Prints solution on console
    print(f'Objective: {solution.ObjectiveValue()}')
    total_distance = 0
    total_payload = 0
    total_volume = 0
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        vehicle_output = 'Route for vehicle {0} (Type: {1}):\n'.format(vehicle_id, vehicles[vehicle_id])
        route_distance = 0
        route_payload = 0
        route_volume = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_payload += data['demands_g'][node_index]
            route_volume += data['demands_liter'][node_index]
            vehicle_output += ' {0} Load({1}kg; {2}m3) -> '.format(node_index, route_payload/1000, route_volume/1000)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        vehicle_output += ' {0} Load({1}kg; {2}m3)\n'.format(manager.IndexToNode(index),
                                                 route_payload/1000, route_volume/1000)
        vehicle_output += 'Distance of the route: {}m\n'.format(route_distance)
        vehicle_output += 'Load of the route: {0}kg and {1}m3\n'.format(route_payload/1000, route_volume/1000)
        if route_distance > 0:
            print(vehicle_output)
            total_distance += route_distance
            total_payload += route_payload
            total_volume += route_volume
    print('Total distance of all routes: {}m'.format(total_distance))
    print('Total load of all routes: {0}kg and {1}m3'.format(total_payload/1000, total_volume/1000))



def main():
    # Solve the CVRP problem
    # Instantiate the data problem
    data = create_data_model()

    # Create the routing index manager
    manager = pywrapcp.RoutingIndexManager(len(data['distance_total']),
                                           data['num_vehicles'], data['depot'])

    # Create Routing Model
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_total'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)


    # Add Capacity (Weight) constraint
    def demand_callback(from_index):
        """Returns the weight demand of the node."""
        # Convert from routing variable Index to demands NodeIndex
        from_node = manager.IndexToNode(from_index)
        return data['demands_g'][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(
        demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        data['vehicle_payloads'],  # vehicle maximum capacities
        True,  # start cumul to zero
        'Payload')

    # Add Capacity (Volume) constraint.
    def volume_callback(from_index):
        #Returns the volume demand of the node.
        # Convert from routing variable Index to demands NodeIndex.
        from_node = manager.IndexToNode(from_index)
        return data['demands_liter'][from_node]

    volume_callback_index = routing.RegisterUnaryTransitCallback(volume_callback)
    routing.AddDimensionWithVehicleCapacity(
        volume_callback_index,
        0,
        data['vehicle_volumes'],
        True,
        'Volume'
    )

    # Setting first solution heuristic
    try:
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    except Exception as e:
        print('Error occured: ', e)
        input('Press any key to exit.')
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.AUTOMATIC)
    search_parameters.time_limit.FromSeconds(600)

    # Solve the problem
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console
    if solution:
        print_solution(data, manager, routing, solution)



if __name__ == '__main__':
    # import cProfile
    # from pstats import Stats

    # pr = cProfile.Profile()
    # pr.enable()

    main()

    # pr.disable()
    # stats = Stats(pr)
    # stats.sort_stats('tottime').print_stats(10)