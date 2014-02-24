from collections import deque
from itertools import takewhile

def breadth_first_kernel(graph, start):
    """
    Breadth first iterator over graph.

    Yields subseqent node identifiers from graph without repetitions.

    :param graph: Adjacency list of graph
    :param start: Start node identifier
    """
    queue = deque([start])
    visited = {start}

    while len(queue):
        source = queue.popleft()
        yield source

        for target in graph.get(source, []):
            if target not in visited:
                visited.add(target)
                queue.append(target)

def breadth_first_search(graph, start, search):
	"""
	Breadth first search for node identifier.

	Yields node identifiers till node is located.

	:param graph: Adjacency list of graph
	:param start: Start node identifier
	:param search: Search node identifier

	Example:
		>>> list(breadth_first_search({1: [2, 3], 2: [3, 5], 3: [4]}, 1, 4))
		[1, 2, 3, 5, 4]
	"""
	for node_id in breadth_first_kernel(graph, start):
		yield node_id

		if node_id == search:
			break
