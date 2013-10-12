from collections import namedtuple
from functools import partial
from heapq import heappush, heappop

edge_cost = namedtuple('edge_cost', 'id cost')
                
def add_edge(graph, left, right, cost):
    if left not in graph:
        graph[left] = []
    
    graph[left].append(edge_cost(id = right, cost = cost))
                
def make_graph(source):
    """
    >>> make_graph([(1, 2, 10), (2, 3, 15), (1, 3, 30)])
    {1: [edge_cost(id=2, cost=10), edge_cost(id=3, cost=30)], 2: [edge_cost(id=3, cost=15)]}
    """
    graph = {}
    
    for entry in source:
        add_edge(graph, *entry)
        
    return graph
    
def reverse_graph(source):
    """
    >>> reverse_graph(make_graph([(1, 2, 10), (2, 3, 15), (1, 3, 30)]))
    {2: [edge_cost(id=1, cost=10)], 3: [edge_cost(id=1, cost=30), edge_cost(id=2, cost=15)]}
    """
    reversed = {}
    
    for left, edges in source.items():
        for right, cost in edges:
            add_edge(reversed, right, left, cost)
            
    return reversed
    
def dijkstra_kernel(graph, start, end, previous):
    queue = [(0.0, start)]
    while queue:
        cost, id = heappop(queue)
        yield edge_cost(id = id, cost = cost)
        
        if id == end:
            return
      
        for neighbour in graph[id]:
            alt_cost = cost + neighbour.cost
            
            # if there was no cost associated or cost is lower
            if id not in previous or alt_cost < previous[neighbour.id].cost:
                heappush(queue, (alt_cost, neighbour.id))
                previous[neighbour.id] = edge_cost(id = id, cost = alt_cost)

def backtrack(previous, id):
    """
    >>> list(backtrack({3: edge_cost(id=2, cost=15), 2: edge_cost(id=1, cost=10)}, 3))
    [3, 2, 1]
    """
    yield id
    while id in previous:
        id = previous[id].id
        yield id

def dijkstra(graph, start, end):
    """
    >>> graph = make_graph([(1, 2, 10), (2, 3, 15), (1, 3, 30)])
    >>> dijkstra(graph, 1, 3)
    (25.0, [1, 2, 3])
    """
    previous = {}
    
    # keep visiting nodes till search is finished
    for id, cost in dijkstra_kernel(graph, start, end, previous):
        pass

    # if end node was reached
    if id == end:
        path = list(backtrack(previous, id))
        path.reverse()
        return (cost, path)

def bidirect_dijkstra(graph, start, end):
    """
    >>> graph = make_graph([(1, 2, 10), (2, 3, 15), (1, 3, 30)])
    >>> bidirect_dijkstra(graph, 1, 3)
    (25.0, [1, 2, 3])
    """
    
    fwd_previous = {}
    bwd_previous = {}
    
    fwd_kernel = dijkstra_kernel(graph, start, end, fwd_previous)
    bwd_kernel = dijkstra_kernel(reverse_graph(graph), end, start, bwd_previous)
    
    def check_intersects(id, previous, cost):
        if id in previous:
            alt_cost = fwd_previous[id].cost + bwd_previous[id].cost
            if alt_cost < cost:
                return (id, alt_cost)
    
    intersection = None
    cost = float('inf')
    
    for fwd, bwd in zip(fwd_kernel, bwd_kernel):
        # break if any search reached target
        #if fwd.id == end or bwd.id == start:
        #    break
        
        # check if there is better intersection
        intersection, cost = \
            check_intersects(fwd.id, bwd_previous, cost) or \
            check_intersects(bwd.id, fwd_previous, cost) or \
            (intersection, cost)
        
        # stop searching if current path is not improved
        if cost < fwd.cost + bwd.cost:
            break
    
    # if shortest path was found
    if intersection is not None:
        path = list(backtrack(fwd_previous, intersection))[1:]
        path.reverse()
        path.extend(backtrack(bwd_previous, intersection))
        
        return (cost, path)