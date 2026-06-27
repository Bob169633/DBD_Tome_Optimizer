from collections import defaultdict


NORMAL_REWARDS = {
  1: 15000,
  2: 25000,
  3: 30000,
  4: 45000,
}

HARD_REWARDS = {
  1: 25000,
  2: 35000,
  3: 50000,
  4: 60000,
}

CHALLENGE_TYPES = {
  "normal",
  "mastery",
  "glyph",
  "core_memory",
}


def get_bp_reward(node_type, page_number):
  if node_type == "normal":
    return NORMAL_REWARDS.get(page_number, 0)

  if node_type in {"mastery", "glyph", "core_memory"}:
    return HARD_REWARDS.get(page_number, 0)

  return 0


def build_graph(page_data):
  graph = defaultdict(set)
  nodes = page_data.get("nodes", {})

  for node_id in nodes:
    graph[node_id]

  for edge in page_data.get("edges", []):
    if len(edge) != 2:
      continue

    left, right = edge

    if left not in nodes or right not in nodes:
      continue

    graph[left].add(right)
    graph[right].add(left)

  return graph


def find_nodes_by_type(nodes, node_type):
  return [
    node_id
    for node_id, node in nodes.items()
    if node.get("type") == node_type
  ]


def get_reachable_nodes(graph, claimed_nodes):
  reachable = set(claimed_nodes)

  for node_id in claimed_nodes:
    reachable.update(graph[node_id])

  return reachable


def get_total_challenge_bp(nodes, page_number):
  total = 0

  for node in nodes.values():
    total += get_bp_reward(
      node.get("type"),
      page_number,
    )

  return total


def get_claimed_bp(nodes, claimed_nodes, page_number):
  total = 0

  for node_id in claimed_nodes:
    if node_id not in nodes:
      continue

    total += get_bp_reward(
      nodes[node_id].get("type"),
      page_number,
    )

  return total


def get_claimed_challenge_count(nodes, claimed_nodes):
  total = 0

  for node_id in claimed_nodes:
    if node_id not in nodes:
      continue

    if nodes[node_id].get("type") in CHALLENGE_TYPES:
      total += 1

  return total


def get_challenge_nodes(nodes):
  return {
    node_id
    for node_id, node in nodes.items()
    if node.get("type") in CHALLENGE_TYPES
  }


def prune_unneeded_page_4_epilogues(nodes, graph, claimed_nodes, all_nodes, epilogues):
  pruned_claimed_nodes = set(claimed_nodes)

  changed = True

  while changed:
    changed = False

    for epilogue in epilogues:
      if epilogue not in pruned_claimed_nodes:
        continue

      test_claimed_nodes = set(pruned_claimed_nodes)
      test_claimed_nodes.remove(epilogue)

      reachable_nodes = get_reachable_nodes(
        graph,
        test_claimed_nodes,
      )

      if all_nodes.issubset(reachable_nodes) and any(test_epilogue in reachable_nodes for test_epilogue in epilogues):
        pruned_claimed_nodes = test_claimed_nodes
        changed = True
        break

  return pruned_claimed_nodes


def optimize_page(page_data, page_number):
  nodes = page_data.get("nodes", {})
  graph = build_graph(page_data)

  prologues = find_nodes_by_type(nodes, "prologue")
  epilogues = find_nodes_by_type(nodes, "epilogue")

  total_bp = get_total_challenge_bp(nodes, page_number)

  if not prologues or not epilogues:
    return {
      "valid": False,
      "reason": "Page must have at least one Prologue and at least one Epilogue.",
      "claimed": set(),
      "banked": set(),
      "visited": set(),
      "claimed_bp": 0,
      "banked_bp": 0,
      "total_bp": total_bp,
    }

  all_nodes = set(nodes.keys())
  challenge_nodes = get_challenge_nodes(nodes)
  best_result = None
  seen = set()

  def search(claimed_nodes):
    nonlocal best_result

    state = frozenset(claimed_nodes)

    if state in seen:
      return

    seen.add(state)

    reachable_nodes = get_reachable_nodes(graph, claimed_nodes)

    if all_nodes.issubset(reachable_nodes) and any(epilogue in reachable_nodes for epilogue in epilogues):
      final_claimed_nodes = set(claimed_nodes)

      if page_number == 4:
        final_claimed_nodes = prune_unneeded_page_4_epilogues(
          nodes,
          graph,
          final_claimed_nodes,
          all_nodes,
          epilogues,
        )

      claimed_bp = get_claimed_bp(
        nodes,
        final_claimed_nodes,
        page_number,
      )

      banked_nodes = challenge_nodes - final_claimed_nodes
      banked_bp = total_bp - claimed_bp

      result = {
        "valid": True,
        "reason": "",
        "claimed": final_claimed_nodes,
        "banked": banked_nodes,
        "visited": set(all_nodes),
        "claimed_bp": claimed_bp,
        "banked_bp": banked_bp,
        "total_bp": total_bp,
      }

      if best_result is None:
        best_result = result
        return

      result_claimed_count = get_claimed_challenge_count(
        nodes,
        result["claimed"],
      )
      best_claimed_count = get_claimed_challenge_count(
        nodes,
        best_result["claimed"],
      )

      if claimed_bp < best_result["claimed_bp"]:
        best_result = result
      elif claimed_bp == best_result["claimed_bp"] and result_claimed_count < best_claimed_count:
        best_result = result

      return

    claimable_nodes = reachable_nodes - claimed_nodes

    for node_id in sorted(claimable_nodes):
      node_type = nodes[node_id].get("type")

      if node_type == "prologue":
        continue

      search(claimed_nodes | {node_id})

  search(set(prologues))

  if best_result is None:
    return {
      "valid": False,
      "reason": "No valid claim route can visit every node and reach an Epilogue.",
      "claimed": set(),
      "banked": set(),
      "visited": set(),
      "claimed_bp": 0,
      "banked_bp": 0,
      "total_bp": total_bp,
    }

  return best_result
