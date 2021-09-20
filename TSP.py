from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from WarehouseMapping import WarehouseMapping, Place, PICKER_VELOCITY
from typing import List


def create_data_model(mapping, map):
    """Stores the data for the problem."""
    data = {}
    data['distance_matrix'] = map
    data['num_vehicles'] = 1
    data['starts'] = [0]
    data['ends'] = [len(map)-1]
    return data

def get_route(manager, routing, solution, index_to_locs):
    # Get vehicle routes and store them in a two dimensional array whose
    # i,j entry is the jth location visited by vehicle i along its route.
    index = routing.Start(0)
    route = [index_to_locs.get(manager.IndexToNode(index))]
    while not routing.IsEnd(index):
        index = solution.Value(routing.NextVar(index))
        route.append(index_to_locs.get(manager.IndexToNode(index)))
    route.pop(0)
    route.pop(-1)
    return route

def print_solution(manager, routing, solution, index_to_locs):
    index = routing.Start(0)
    index = solution.Value(routing.NextVar(index))
    plan_output = 'Best route found:\n'
    route_distance = 0
    while not routing.IsEnd(index):
        plan_output += ' {} ->'.format(index_to_locs.get(manager.IndexToNode(index)))
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
    # plan_output += ' {}\n'.format(index_to_locs.get(manager.IndexToNode(index)))
    plan_output += 'Route walking distance: {} meters\n'.format(route_distance)
    #print(plan_output)
    return route_distance

def findMinimalRoute(places: list):
    # Instantiate the data problem.
    mapping = WarehouseMapping(calculate_loc2Dmatrix=True)

    map, index_to_locs = mapping.getLoc2DMapForTSP(places)

    data = create_data_model(mapping, map)

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['starts'], data['ends'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)


    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    best_route = None
    route_distance = None
    if solution:
        route_distance = print_solution(manager, routing, solution, index_to_locs)
        best_route = get_route(manager, routing, solution, index_to_locs)
    return best_route, route_distance


def printBestRoute(route, total_time):
    plan_output = 'Best route found:\n'
    for pl in route:
        plan_output += ' {} ->'.format(pl)
    plan_output = plan_output[:-3]
    plan_output += '\n Time = {:.1f}'.format(total_time)
    print(plan_output)

def TSPsolver(places: List[Place]):
    if (places is None or len(places)==0):
        return [], 0
    if (len(places) == 1):
        wm = WarehouseMapping()
        return places, wm.distanceToTime(wm.fromEntrance(places[0]))
    best_route, total_distance = findMinimalRoute(places)
    sortedPlaces = pairShelfsToBestRoute(best_route, places)
    total_time = (total_distance/PICKER_VELOCITY) + len(best_route)  # a second for each stopping point
    printBestRoute(sortedPlaces, total_time)
    return sortedPlaces, total_time

def pairShelfsToBestRoute(best_route: List[int], places : List[Place]):
    places.pop(0)
    places.pop(-1)
    def indexOfLocation(pl):
        return best_route.index(pl.location)
    places.sort(key=indexOfLocation)
    return places


if __name__ =='__main__':
    res, time = TSPsolver([Place(788, 2)])
    print(*res)
    print(time)
