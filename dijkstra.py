from future_builtins import zip
from operator import itemgetter
from collections import defaultdict
from heapdict import heapdict

def identity(value):
    """
    Identity mapping of single argument.
    """

    return value

def make_graph(source, edge_factory=identity):
    """
    Make graph out of list of edges.

    :param source: list of tuples in form of (from, to, *payload)
    :param edge_factory: factory for edge attributes
    :returns: adjacency list
    
    Example:
        >>> make_graph([(1, 2, 10), (2, 3, 15), (1, 3, 30)])
        defaultdict(<type 'list'>, {1: [(2, 10), (3, 30)], 2: [(3, 15)]})

        >>> from collections import namedtuple
        >>> EdgeAttrs = namedtuple('EdgeAttrs', 'time distance mode')
        >>> make_graph([(1, 2, 10, 0.4, 'WALK'), (2, 3, 30, 15, 'BUS'), (1, 3, 15, 30, 'TRAIN')], edge_factory=EdgeAttrs) 
        defaultdict(<type 'list'>, {1: [(2, EdgeAttrs(time=10, distance=0.4, mode='WALK')), (3, EdgeAttrs(time=15, distance=30, mode='TRAIN'))], 2: [(3, EdgeAttrs(time=30, distance=15, mode='BUS'))]})
    """
    graph = defaultdict(list)
    
    for edge in source:
        left, right = edge[:2]
        payload = edge_factory(*edge[2:])
        graph[left].append((right, payload))
        
    return graph
    
def reverse_graph(source):
    """
    Reverse direction of graph.

    :param source: adjacency list of graph
    
    Example:
        >>> reverse_graph(make_graph([(1, 2, 10), (2, 3, 15), (1, 3, 30)]))
        defaultdict(<type 'list'>, {2: [(1, 10)], 3: [(1, 30), (2, 15)]})
    """
    reversed = defaultdict(list)
    
    for left, edges in source.items():
        for right, payload in edges:
            reversed[right].append((left, payload))
            
    return reversed
    
def dijkstra_kernel(graph, start, previous, cost_fn):
    """
    Generator for dijkstra search.

    Each iteration yields visited node id and cost to reach it from start node.

    :param graph: adjacency list of graph
    :param start: start node id
    :param previous: dictionary for storing settled nodes
    :param cost_fn: cost function applied for each edge, must be stateless
    """

    queue = heapdict({start: 0.0})
    previous.update({start: (None, 0.0, None)})
    while queue:
        left, cost = queue.popitem()
        yield left, cost
       
        for right, payload in graph.get(left, []):
            alt_cost = cost + cost_fn(payload)
            
            # if there was no cost associated or cost is lower
            if right not in previous or alt_cost < previous[right][1]:
                queue[right] = alt_cost
                previous[right] = (left, alt_cost, payload)

def backtrack(previous, start):
    """
    Collect edges visited by dijkstra kernel.

    :param previous: dictionary of settled nodes
    :param start: node id to start backtracking from
    :returns: reversed list of edges

    Example:
        >>> list(backtrack({3: (2, 25, 15), 2: (1, 10, 10), 1: (None, 0.0, None)}, 3))
        [(2, 3, 15), (1, 2, 10)]
    """
    left = start
    while True:
        right, _, payload = previous[left]
        if right is None:
            break
        yield right, left, payload
        left = right

def just_ids(source):
    """
    Convert dijkstra result to contain only node ids.

    :param source: (cost, edges) tuple returned by dijkstra search

    Example:
        >>> just_ids((25.0, [(1, 2, 10.0), (2, 3, 15.0)]))
        (25.0, [1, 2, 3])
    """
    cost, edges = source
    if not len(edges):
        return (cost, [])
    result = [left for left, right, _ in edges]
    result.append(right)
    return (cost, result)

def dijkstra(graph, start, end, cost_fn=identity):
    """
    Dijkstra search on directed graph.

    :param graph: adjacency list of graph
    :param start: node to start search at
    :param end: final node
    :param cost_fn: cost function applied on edges

    Example:
        >>> graph = make_graph([(1, 2, 10.0), (2, 3, 15.0), (1, 3, 30.0)])
        >>> dijkstra(graph, 1, 3)
        (25.0, [(1, 2, 10.0), (2, 3, 15.0)])
    """
    previous = {}
    
    # keep visiting nodes till search is finished
    for id, cost in dijkstra_kernel(graph, start, previous, cost_fn):
        if id == end:
            break

    # if end node was reached
    if id == end:
        edges = list(backtrack(previous, id))
        edges.reverse()
        return (cost, edges)

def bidirect_dijkstra(graph, start, end, bwd_graph = None, cost_fn=identity):
    """
    Bidirectional dijkstra search on directed graph.

    Search from both start and end of the graph reducing search space substantially.

    :param graph: adjacency list of graph
    :param start: node to start search at
    :param end: final node
    :param bwd_graph: reversed graph for backward search
    :param cost_fn: cost function applied on edges

    Example:    
        >>> graph = make_graph([(1, 2, 10.0), (2, 3, 15.0), (1, 3, 30.0)])
        >>> bidirect_dijkstra(graph, 1, 3)
        (25.0, [(1, 2, 10.0), (2, 3, 15.0)])
    """
    
    fwd_previous = {}
    bwd_previous = {}
    
    fwd_kernel = dijkstra_kernel(graph, start, fwd_previous, cost_fn)
    bwd_kernel = dijkstra_kernel(reverse_graph(graph), end, bwd_previous, cost_fn)
    
    intersection = None
    cost = float('inf')
    
    # helper for finding intersection candidate
    def check_intersects(id, previous):
        if id in previous:
            alt_cost = fwd_previous[id][1] + bwd_previous[id][1]
            if alt_cost < cost:
                return (id, alt_cost)
        return (None, float('inf'))
    
    for fwd, bwd in zip(fwd_kernel, bwd_kernel): 
        # check if there is better intersection
        intersection, cost = min((intersection, cost), check_intersects(fwd[0], bwd_previous), check_intersects(bwd[0], fwd_previous), key=itemgetter(1))
        
        # stop searching if current path is not improved
        if cost < fwd[1] + bwd[1]:
            break
    
    # if shortest path was found
    if intersection is not None:
        edges = list(backtrack(fwd_previous, intersection))
        edges.reverse()
        edges.extend((right, left, payload) for left, right, payload in backtrack(bwd_previous, intersection))
        
        return (cost, edges)
