""" This code is based on and adapted from the OR-Tools example for Capacited Vehicles Routing Problem (CVRP) """
""" Please find the original code here: https://developers.google.com/optimization/routing/cvrp#entire_program """
""" Distances [m], weight [g], volume [l], and cost [0.1ct] to keep precision reasonably high, as the solver only accepts integer values """

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import numpy as np
from utils import get_nodes, get_routes, get_distance_matrix_from_routes, get_time_matrix_from_routes, get_time_list_from_nodes, count_occurrences, int_to_time, get_fss, get_lss, check_infeasibility

# Global variables defaults - Values are adjusted from GUI through set_variables()
vehicles = np.repeat(1, 38)
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
carriers['ranges'] = [1028571, 875000, 847458, 79710, 205023, 118977, 100000] # in m
carriers['cpkm_cities'] = [[2393, 2152, 2079, 2472, 2158, 2102, 3560], [3181, 3017, 2961, 3377, 3082, 3027, 3700], [1070, 892, 833, 1233, 944, 889, 1810]]
carriers['cpkm_outside'] = carriers['cpkm_cities'][city_int]
carriers['cpkm_inside'] = [c+toll if num<3 else c for num, c in enumerate(carriers['cpkm_outside'])]



def set_variables(new_vehicles, new_city, new_toll, new_fss, new_lss, new_time):
    global vehicles
    global city
    global carriers
    global num_vehicles
    global fss
    global fss_string
    global lss
    global lss_string
    global timeout

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
    fss = get_fss(new_fss)
    lss = get_lss(new_lss)



def create_data_model():
    global city
    global carriers
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
    data['ranges'] = [carriers['ranges'][i-1] for i in vehicles]
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
        route_max_range = carriers['ranges'][vehicles[vehicle_id]-1]/1000
        route_string += f'Distance: {route_distance/1000}/{route_max_range}km ({route_distance_inside/1000}km inside; {route_distance_outside/1000}km outside)\n'
        route_cpkm_in = carriers['cpkm_inside'][vehicles[vehicle_id]-1]/1000
        route_cpkm_out = carriers['cpkm_outside'][vehicles[vehicle_id]-1]/1000
        route_string += f'Cost: {route_cost/1000}€ ({route_cpkm_in}€/km inside and {route_cpkm_out}€/km outside)\n'
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
    print(f'{all_routes_string}\n{total_dist_string}\n{total_cost_string}\n{total_load_string}\n{chosen_fleet_string}')
    return all_routes_string, total_load_string, total_dist_string, total_time_string, total_cost_string, chosen_fleet_string, chosen_parameter_string, [total_cost/1000, f'{count_occurrences(chosen_fleet)}', total_payload/1000, total_volume/1000, total_distance/1000]



def main():
    # Solve the CVRP problem
    # Instantiate the data problem
    data = create_data_model()

    # Check if provided vehicles have enough weight/volume to cover capacity in theory
    impossible, out_string = check_infeasibility(data['vehicle_payloads'], data['vehicle_volumes'], data['demands_g'], data['demands_liter'])
    if impossible:
        return out_string

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
        return data['distance_total'][from_node][to_node]

    distance_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.AddDimensionWithVehicleCapacity(
        distance_callback_index,
        0, # zero slack
        data['ranges'], # maximum ranges
        True, # start at zero
        'Range'
        )

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
    search_parameters.first_solution_strategy = fss
    search_parameters.local_search_metaheuristic = lss
    search_parameters.time_limit.FromSeconds(timeout)

    # Solve the problem
    try:
        solution = routing.SolveWithParameters(search_parameters)
    except Exception as e:
        return '', '', '', '', f'Error occurred while solving: {e}', '', f'{e}', False


    # Print solution on console
    if solution:
        return print_solution(data, manager, routing, solution)
    else:
        return 'No solution could be found!', '', 'Please check your chosen parameters for feasibility.', '', 'No solution could be found!', '', 'No solution could be found', False

if __name__ == '__main__':
    main()