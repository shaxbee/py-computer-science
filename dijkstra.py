from future_builtins import zip
from operator import itemgetter
from collections import defaultdict
from heapq import heappush, heappop

def identity(value):
    return value

def make_graph(source, edge_factory=identity):
    """
    Make graph out of (from, to, *attributes) tuples using edge_factory.

    :param edge_factory: factory for edge attributes
    
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
    Reverse direction of graph
    
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
    queue = [(0.0, start)]
    previous.update({start: (None, 0.0, None)})
    while queue:
        cost, left = heappop(queue)
        yield left, cost
       
        for right, payload in graph.get(left, []):
            alt_cost = cost + cost_fn(payload)
            
            # if there was no cost associated or cost is lower
            if right not in previous or alt_cost < previous[right][1]:
                heappush(queue, (alt_cost, right))
                previous[right] = (left, alt_cost, payload)

def backtrack(previous, start):
    """
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
    cost, edges = source
    if not len(edges):
        return (cost, [])
    result = [left for left, right, _ in edges]
    result.append(right)
    return (cost, result)

def dijkstra(graph, start, end, cost_fn=identity):
    """
    >>> graph = make_graph([(1, 2, 10), (2, 3, 15), (1, 3, 30)])
    >>> just_ids(dijkstra(graph, 1, 3))
    (25.0, [1, 2, 3])
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

def bidirect_dijkstra(graph, start, end, cost_fn=identity):
    """
    >>> graph = make_graph([(1, 2, 10.0), (2, 3, 15.0), (1, 3, 30.0)])
    >>> just_ids(bidirect_dijkstra(graph, 1, 3))
    (25.0, [1, 2, 3])
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
