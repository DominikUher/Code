""" This code is based on and adapted from the OR-Tools example for Capacited Vehicles Routing Problem (CVRP) """
""" Please find the original code here: https://developers.google.com/optimization/routing/cvrp#entire_program """
""" Distances [m], weight [g], volume [l], and cost [0.1ct] to keep precision reasonably high, as the solver only accepts integer values """

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import ortools.constraint_solver.routing_parameters_pb2
import numpy as np
from utils import get_nodes, get_routes, get_distance_matrix_from_routes, get_time_matrix_from_routes, get_time_list_from_nodes, count_occurrences, int_to_time

# Global variables defaults - Values are adjusted from GUI through set_variables()
vehicles = [np.repeat(1, 38)]
num_vehicles = len(vehicles)
city = 'Paris'
city_int = 0
toll = 0
fss = routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC
fss_string = 'Automatic'
lss = routing_enums_pb2.LocalSearchMetaheuristic.AUTOMATIC
lss_string = 'Automatic'
timeout = 30

# Carrier characteristics
carriers = {}
carriers['ids'] = [1, 2, 3, 4, 5, 6, 7]
carriers['payloads'] = [2800000, 883000, 670000, 2800000, 905000, 720000, 100000] # in g
carriers['volumes'] = [34800, 5800, 3200, 21560, 7670, 4270, 200] # in liters
carriers['cpkm_cities'] = [[2393, 2152, 2079, 2472, 2158, 2102, 3560], [3181, 3017, 2961, 3377, 3082, 3027, 3700], [1070, 892, 833, 1233, 944, 889, 1810]]
carriers['cpkm_outside'] = carriers['cpkm_cities'][city_int]
carriers['cpkm_inside'] = [c+toll if num<3 else c for num, c in enumerate(carriers['cpkm_outside'])]
# TODO: Consider adding constraints for maximum travel distance, time, speed, ...



def set_variables(new_vehicles, new_city, new_toll, new_fss, new_lss, new_time):
    global vehicles
    global num_vehicles
    global city
    global city_int
    global toll
    global fss
    global fss_string
    global lss
    global lss_string
    global timeout
    global carriers

    vehicles = new_vehicles
    num_vehicles = len(vehicles)
    city = new_city
    city_int = 0 if city=='Paris' else 1 if city=='NewYork' else 2
    toll = new_toll
    carriers['cpkm_outside'] = carriers['cpkm_cities'][city_int]
    carriers['cpkm_inside'] = [c+toll if num<3 else c for num, c in enumerate(carriers['cpkm_outside'])]
    timeout = new_time
    fss_string = new_fss
    lss_string = new_lss

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



def create_data_model():
    # Stores the data for the problem
    nodes = get_nodes(city)
    num_nodes = len(nodes.index)
    routes = get_routes(city)
    num_routes = len(routes.index)

    data = {}
    data['distance_total'] = get_distance_matrix_from_routes(routes, num_nodes, 'Total')
    data['distance_inside'] = get_distance_matrix_from_routes(routes, num_nodes, 'Inside')
    data['distance_outside'] = get_distance_matrix_from_routes(routes, num_nodes, 'Outside')
    data['time_routes'] = get_time_matrix_from_routes(routes, num_nodes)
    data['time_nodes'] = get_time_list_from_nodes(nodes)
    data['demands_g'] = [d*1000 for d in nodes['Demand[kg]'].values]
    data['demands_liter'] = nodes['Demand[m^3*10^-3]'].values
    data['vehicle_payloads'] = [carriers['payloads'][i-1] for i in vehicles]
    data['vehicle_volumes'] = [carriers['volumes'][i-1] for i in vehicles]
    data['num_vehicles'] = num_vehicles
    data['depot'] = 0
    return data



def print_solution(data, manager, routing, solution):
    # Prints solution on console/GUI
    global fss
    global lss
    global timeout
    toll_str = '{:.2f}'.format(toll/1000)
    all_routes_string = ''
    total_cost = 0
    total_distance = 0
    total_time = 0
    total_payload = 0
    total_volume = 0
    chosen_fleet = []
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        route_string = f'Route for vehicle {len(chosen_fleet)+1} (Type {vehicles[vehicle_id]}):\n'
        route_cost = 0
        route_distance = 0
        route_distance_inside = 0
        route_distance_outside = 0
        route_time = 0
        route_payload = 0
        route_volume = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_payload += data['demands_g'][node_index]
            route_volume += data['demands_liter'][node_index]
            route_string += f'[{node_index}] ({route_payload/1000}kg; {route_volume/1000}m3) -> '
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_cost += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
            route_distance += data['distance_total'][node_index][manager.IndexToNode(index)]
            route_distance_inside += data['distance_inside'][node_index][manager.IndexToNode(index)]
            route_distance_outside += data['distance_outside'][node_index][manager.IndexToNode(index)]
            route_time += data['time_routes'][node_index][manager.IndexToNode(index)] + data['time_nodes'][manager.IndexToNode(index)]
        route_string += f'[{manager.IndexToNode(index)}] ({route_payload/1000}kg; {route_volume/1000}m3)\n'
        route_cpkm_in = carriers['cpkm_inside'][vehicles[vehicle_id]-1]/1000
        route_cpkm_out = carriers['cpkm_outside'][vehicles[vehicle_id]-1]/1000
        route_string += f'Cost: {route_cost/1000}€ ({route_cpkm_in}€/km inside and {route_cpkm_out}€/km outside)\n'
        route_string += f'Distance: {route_distance/1000}km ({route_distance_inside/1000}km inside; {route_distance_outside/1000}km outside)\n'
        route_max_payload = carriers['payloads'][vehicles[vehicle_id]-1]/1000
        route_max_volume = carriers['volumes'][vehicles[vehicle_id]-1]/1000
        route_string += f'Load: {route_payload/1000}/{route_max_payload}kg and {route_volume/1000}/{route_max_volume}m3\n'
        route_string += f'Time: {int_to_time(route_time)}\n'
        if route_cost > 0:
            total_distance += route_distance
            total_time += route_time
            total_cost += route_cost
            total_payload += route_payload
            total_volume += route_volume
            chosen_fleet.append(vehicles[vehicle_id])
            all_routes_string += route_string+'\n'
    total_load_string = f'Total load of all routes: {total_payload/1000}kg and {total_volume/1000}m3'
    total_cost_string = f'Total cost of all routes: {total_cost/1000}€'
    total_dist_string = f'Total distance of all routes: {total_distance/1000}km'
    total_time_string = f'Total time of all routes: {int_to_time(total_time)}'
    chosen_fleet_string = f'Chosen fleet: {count_occurrences(chosen_fleet)} ({len(chosen_fleet)} vehicles)'
    chosen_parameter_string = f'Solution for {city} with {toll_str}€/km tolls and fleet {count_occurrences(vehicles)}\nSearch parameters: FSS={fss_string}, LSS={lss_string}, t={timeout}s'
    print(all_routes_string)
    print(total_dist_string)
    print(total_cost_string)
    print(total_load_string)
    print(chosen_fleet_string)
    return all_routes_string, total_load_string, total_dist_string, total_time_string, total_cost_string, chosen_fleet_string, chosen_parameter_string



def main():
    # Solve the CVRP problem
    # Instantiate the data problem
    data = create_data_model()

    # Create the routing index manager
    manager = pywrapcp.RoutingIndexManager(len(data['distance_total']),
                                           data['num_vehicles'], data['depot'])

    # Create Routing Model
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        # Returns the distance between the two nodes
        # Convert from routing variable Index to distance matrix NodeIndex
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_inside'][from_node][to_node]

    routing.RegisterTransitCallback(distance_callback)

    # Create and register a transit callback
    def cost_callback(vehicle_id):
        def dist_callback(from_index, to_index):
            # Returns the distance between the two nodes
            # Convert from routing variable Index to distance matrix NodeIndex
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return round(data['distance_inside'][from_node][to_node] / 1000 * carriers['cpkm_inside'][vehicle_id] + data['distance_outside'][from_node][to_node] / 1000 * carriers['cpkm_outside'][vehicle_id])
        return dist_callback

    # Define arc costs of each vehicle
    cost_callbacks = []
    for vehicle_id, vehicle_type in enumerate(vehicles):
        cost_callbacks.append(routing.RegisterTransitCallback(cost_callback(vehicle_type-1)))
        routing.SetArcCostEvaluatorOfVehicle(cost_callbacks[-1], vehicle_id)

    # Add Cost constraints
    routing.AddDimensionWithVehicleTransits(
        cost_callbacks,
        0,
        1000000,
        True,
        'Cost'
        )
    cost_dimension = routing.GetDimensionOrDie('Cost')
    cost_dimension.SetGlobalSpanCostCoefficient(0)

    # Add Capacity (Weight) constraint
    def payload_callback(from_index):
        # Returns the weight demand of the node
        # Convert from routing variable Index to demands NodeIndex
        from_node = manager.IndexToNode(from_index)
        return data['demands_g'][from_node]

    payload_callback_index = routing.RegisterUnaryTransitCallback(payload_callback)
    routing.AddDimensionWithVehicleCapacity(
        payload_callback_index,
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

    # Add Time dimension.
    def time_callback(from_index, to_index):
        # Returns the time  between the two nodes
        # Convert from routing variable Index to distance matrix NodeIndex
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['time_routes'][from_node][to_node] + data['time_nodes'][to_node]

    time_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.AddDimension(
        time_callback_index,
        0, # zero slack
        28800, # maximum 8h
        True, # starts at zero
        'Time'
    )

    # Setting first solution heuristic
    global fss
    global lss
    global timeout
    try:
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    except Exception as e:
        print('Error occured: ', e)
        input('Press any key to exit.')
    search_parameters.first_solution_strategy = (fss)
    search_parameters.local_search_metaheuristic = (lss)
    search_parameters.time_limit.FromSeconds(timeout)

    # Solve the problem
    try:
        solution = routing.SolveWithParameters(search_parameters)
    except Exception as e:
        return '', '', '', '', f'Error occurred while solving: {e}', '', f'### {e}'


    # Print solution on console
    if solution:
        return print_solution(data, manager, routing, solution)
    else:
        return '', '', 'Please check your chosen parameters for feasibility.', '', 'No solution could be found!', '', 'No solution could be found'

if __name__ == '__main__':
    main()