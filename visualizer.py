import matplotlib.pyplot as plt
import networkx as nx

from rewards import get_bp_reward


def get_node_label(node):
  reward = get_bp_reward(node.node_type, node.page)

  if reward <= 0:
    return node.name

  return f"{node.name}\n{reward:,} BP"


def visualize_page(nodes, graph, result, title):
  display_graph = nx.Graph()

  for node_id in nodes:
    display_graph.add_node(node_id)

  for left, neighbors in graph.items():
    for right in neighbors:
      display_graph.add_edge(left, right)

  claimed = result["claimed"]
  preserved = result["preserved"]

  colors = []

  for node_id in display_graph.nodes:
    if node_id in claimed:
      colors.append("lightcoral")
    elif node_id in preserved:
      colors.append("gold")
    else:
      colors.append("lightgray")

  labels = {
    node_id: get_node_label(node)
    for node_id, node in nodes.items()
  }

  pos = nx.spring_layout(display_graph, seed=7)

  plt.figure(figsize=(14, 9))
  nx.draw(
    display_graph,
    pos,
    labels=labels,
    node_color=colors,
    node_size=3200,
    font_size=8,
    edge_color="gray",
  )

  plt.title(title)
  plt.tight_layout()
  plt.show()