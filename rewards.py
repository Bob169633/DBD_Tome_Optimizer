from models import NodeType


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


def get_bp_reward(node_type, page):
  if node_type == NodeType.NORMAL:
    return NORMAL_REWARDS[page]

  if node_type in {
    NodeType.MASTERY,
    NodeType.GLYPH,
    NodeType.CORE_MEMORY,
  }:
    return HARD_REWARDS[page]

  return 0