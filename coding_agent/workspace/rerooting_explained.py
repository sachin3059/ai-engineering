#!/usr/bin/env python3
"""
rerooting_explained.py

A self-contained script that explains the rerooting (re-rooting) technique for tree dynamic programming
and demonstrates it with two clear examples:

1) Sum of distances from each node to all other nodes.
   - Returns for every node the sum of distances to all nodes in the tree.
   - Uses pair values (sum_distances, size_of_subtree) as the DP state.

2) Eccentricity (maximum distance from each node to any node).
   - Returns for every node the maximum distance to any node in the tree (i.e. eccentricity).
   - Uses a single integer DP state (max distance downwards).

The script implements a generic rerooting template (higher-order): you provide
- identity: the neutral element for merging child contributions
- merge(a, b): how to combine two child contributions
- add_edge(child_contribution): how a child's contribution changes when seen from the parent across the connecting edge
- finalize(node_value): optional post-processing for the node's final answer

Then it runs the two examples on a sample tree and prints results.

Run: python3 rerooting_explained.py
"""

import sys
sys.setrecursionlimit(10000)

# Generic rerooting implementation ------------------------------------------------
class Rerooting:
    def __init__(self, n, edges):
        self.n = n
        self.g = [[] for _ in range(n)]
        for u, v in edges:
            self.g[u].append(v)
            self.g[v].append(u)

    def run(self, identity, merge, add_edge, finalize=None):
        """
        identity: neutral element for merge
        merge: function(a, b) -> merged value of child contributions
        add_edge: function(child_value) -> contribution seen at parent when crossing the edge
        finalize: optional function(node_value) -> final answer for node
        Returns: list of final answers for each node (length n)
        """
        n = self.n
        g = self.g

        down = [None] * n  # contribution from subtree rooted at node (children only)

        def dfs1(u, p):
            # compute down[u]
            cur = identity
            for v in g[u]:
                if v == p:
                    continue
                dfs1(v, u)
                cur = merge(cur, add_edge(down[v]))
            down[u] = cur

        dfs1(0, -1)

        ans = [None] * n

        def dfs2(u, p, up_value):
            # gather all contributions: children's add_edge(down[v]) and up_value
            children = [v for v in g[u] if v != p]
            m = len(children)

            vals = [None] * (m + 1)  # we'll place children's contributions
            for i, v in enumerate(children):
                vals[i] = add_edge(down[v])
            vals[m] = up_value

            # prefix and suffix merges to compute combined contributions excluding one child
            prefix = [identity] * (m + 2)
            for i in range(m):
                prefix[i + 1] = merge(prefix[i], vals[i])
            suffix = [identity] * (m + 2)
            for i in range(m - 1, -1, -1):
                suffix[i] = merge(vals[i], suffix[i + 1])

            total = merge(prefix[m], vals[m])

            # finalize answer for u
            if finalize is None:
                ans[u] = total
            else:
                ans[u] = finalize(total)

            # pass to children their 'up' value
            for i, v in enumerate(children):
                # combine contributions of all other children and up_value
                without_v = merge(prefix[i], suffix[i + 1])
                up_for_v = add_edge(without_v)
                dfs2(v, u, up_for_v)

        # initial up_value for root is identity
        dfs2(0, -1, identity)
        return ans

# Example 1: Sum of distances to all other nodes ----------------------------------
# We keep DP state as a pair: (sum_distances_to_nodes_in_subtree, size_of_subtree)
# For a child-subtree with state (s, sz), when it becomes seen from the parent,
# all nodes in that child-subtree are 1 further away, so contribution becomes (s + sz, sz).

def example_sum_of_distances(n, edges):
    rer = Rerooting(n, edges)

    identity = (0, 0)  # (sum, size)

    def merge(a, b):
        return (a[0] + b[0], a[1] + b[1])

    def add_edge(child):
        # child is (sum, size) from child's subtree
        return (child[0] + child[1], child[1])

    def finalize(node_value):
        # node_value is (sum_of_distances_from_node_to_all_nodes, total_size)
        # total_size should be n
        return node_value[0]

    return rer.run(identity, merge, add_edge, finalize)

# Example 2: Eccentricity (max distance to any node) ------------------------------
# DP state: maximum distance downwards into the subtree (0 for leaf).
# Merge is max, add_edge increases distance by 1 when crossing the edge.

def example_eccentricity(n, edges):
    rer = Rerooting(n, edges)

    NEG = -10**9
    identity = NEG

    def merge(a, b):
        return a if a > b else b

    def add_edge(child):
        # if child is NEG (no contribution), keep NEG
        if child == NEG:
            return NEG
        return child + 1

    def finalize(node_value):
        # node_value may be NEG iff there are no nodes -- not possible here; ensure non-negative
        return max(0, node_value)

    return rer.run(identity, merge, add_edge, finalize)

# Utility: build a simple sample tree for demonstration ---------------------------
def sample_tree_edges():
    # Let's build a tree of 9 nodes with varied shape for demonstration.
    # Edges (0-indexed):
    edges = [
        (0, 1), (0, 2),
        (1, 3), (1, 4),
        (2, 5),
        (5, 6), (5, 7), (7, 8)
    ]
    n = 9
    return n, edges

# Main: run examples and print explanations & results -----------------------------
if __name__ == '__main__':
    print('\nRerooting / Re-rooting DP: explanation and examples')
    print('---------------------------------------------------\n')

    print('Short explanation:')
    print(' - Many tree DP problems compute values for a fixed root ("down" values).')
    print(' - Rerooting efficiently computes the answer for every possible root by reusing
subtree results and propagating "up" contributions.')
    print(' - Key idea: for a node, combine contributions of all incident parts (each child subtree
and the parent-side part). Then when moving the root to a child, compute what the new
parent-side contribution for that child would be by combining all other parts.\n')

    n, edges = sample_tree_edges()
    print(f'Using a sample tree with n={n} and edges:')
    for u, v in edges:
        print(f'  {u} - {v}')
    print()

    print('Example 1: Sum of distances from each node to all other nodes')
    sumd = example_sum_of_distances(n, edges)
    print('Result (node: sum of distances to all nodes):')
    for i, val in enumerate(sumd):
        print(f'  {i}: {val}')
    print('\nSanity check: node 0 (a relatively central node) should have a relatively small sum;')
    print('node 8 (a deep leaf) should have a larger sum.')

    print('\nExample 2: Eccentricity (max distance from each node to any node)')
    ecc = example_eccentricity(n, edges)
    print('Result (node: eccentricity):')
    for i, val in enumerate(ecc):
        print(f'  {i}: {val}')
    print('\nNote: Eccentricity of a node equals the maximum distance from that node to any node;')
    print('the tree diameter endpoints will have the maximal eccentricity in the tree.\n')

    # Extra: show how answers correspond: find diameter endpoints by naive BFS to cross-check
    from collections import deque

    def bfs_farthest(start):
        q = deque([start])
        dist = [-1] * n
        dist[start] = 0
        while q:
            u = q.popleft()
            for v in range(n):
                pass

    # We'll implement a correct BFS using adjacency list
    g = [[] for _ in range(n)]
    for u, v in edges:
        g[u].append(v)
        g[v].append(u)

    def bfs(start):
        q = deque([start])
        dist = [-1] * n
        dist[start] = 0
        while q:
            u = q.popleft()
            for v in g[u]:
                if dist[v] == -1:
                    dist[v] = dist[u] + 1
                    q.append(v)
        far = max(range(n), key=lambda x: dist[x])
        return far, dist

    a, dista = bfs(0)
    b, dista = bfs(a)
    diameter = dista[b]
    print(f'Computed tree diameter length (by two BFS) = {diameter}')
    print('Eccentricities (from rerooting) should be <= diameter and endpoints have value == diameter')
    print(f'Max eccentricity found in rerooting = {max(ecc)}')

    print('\nEnd of demonstration. You can adapt the generic Rerooting class to many problems by\n')
    print('providing appropriate merge/add_edge/finalize functions for your DP state and transitions.')
