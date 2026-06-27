from dataclasses import dataclass
from enum import Enum


class NodeType(Enum):
  PROLOGUE = "prologue"
  EPILOGUE = "epilogue"
  NORMAL = "normal"
  MASTERY = "mastery"
  GLYPH = "glyph"
  CORE_MEMORY = "core_memory"


@dataclass(frozen=True)
class TomeNode:
  node_id: str
  name: str
  node_type: NodeType
  page: int

  @property
  def is_challenge(self):
    return self.node_type not in {
      NodeType.PROLOGUE,
      NodeType.EPILOGUE,
    }