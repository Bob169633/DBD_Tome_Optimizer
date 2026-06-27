import math
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from storage import add_new_tome
from storage import load_tome_by_entry
from storage import load_tome_index
from storage import save_tome


NODE_RADIUS = 34
ANGLE_SNAP_DEGREES = 45
MIN_LAYOUT_RADIUS = 120
MIN_NODE_SPACING = 130
CANVAS_NODE_PADDING = NODE_RADIUS + 10

NODE_COLORS = {
  "prologue": "#9ad0f5",
  "epilogue": "#c9a0ff",
  "normal": "#dddddd",
  "mastery": "#ffb347",
  "glyph": "#7fd8be",
  "core_memory": "#f7a8c4",
}


class TomePageEditor:
  def __init__(self, root):
    self.root = root
    self.root.title("DBD Tome Page Editor")

    self.index_data = load_tome_index()
    self.tome_entries = self.index_data["tomes"]
    self.loaded_tomes = {}

    self.current_tome_entry = self.tome_entries[0]
    self.current_tome = self.load_tome(self.current_tome_entry)
    self.tome_name = self.current_tome_entry["name"]
    self.page_number = 1

    self.nodes = self.current_tome["pages"][str(self.page_number)]["nodes"]
    self.edges = self.current_tome["pages"][str(self.page_number)]["edges"]

    self.selected_node = None
    self.dragging_node = None
    self.last_mouse_x = None
    self.last_mouse_y = None

    self.build_gui()
    self.root.after(0, self.redraw)

  def build_gui(self):
    self.main_frame = tk.Frame(self.root)
    self.main_frame.pack(fill=tk.BOTH, expand=True)

    self.toolbar = tk.Frame(self.main_frame)
    self.toolbar.pack(side=tk.TOP, fill=tk.X)

    tk.Label(self.toolbar, text="Tome:").pack(side=tk.LEFT, padx=4)

    self.tome_var = tk.StringVar(value=self.tome_name)
    self.tome_dropdown = ttk.Combobox(
      self.toolbar,
      textvariable=self.tome_var,
      values=self.get_tome_names(),
      state="readonly",
      width=16,
    )
    self.tome_dropdown.pack(side=tk.LEFT, padx=4)
    self.tome_dropdown.bind("<<ComboboxSelected>>", self.change_tome)

    self.add_tome_button = tk.Button(
      self.toolbar,
      text="Add Tome",
      command=self.add_tome,
    )
    self.add_tome_button.pack(side=tk.LEFT, padx=4)

    tk.Label(self.toolbar, text="Page:").pack(side=tk.LEFT, padx=4)

    self.page_var = tk.StringVar(value=str(self.page_number))
    self.page_dropdown = ttk.Combobox(
      self.toolbar,
      textvariable=self.page_var,
      values=self.get_page_values_for_current_tome(),
      state="readonly",
      width=4,
    )
    self.page_dropdown.pack(side=tk.LEFT, padx=4)
    self.page_dropdown.bind("<<ComboboxSelected>>", self.change_page)

    self.node_type_var = tk.StringVar(value="normal")

    tk.Label(self.toolbar, text="Node Type:").pack(side=tk.LEFT, padx=4)

    self.node_type_dropdown = ttk.Combobox(
      self.toolbar,
      textvariable=self.node_type_var,
      values=[
        "prologue",
        "epilogue",
        "normal",
        "mastery",
        "glyph",
        "core_memory",
      ],
      state="readonly",
      width=14,
    )
    self.node_type_dropdown.pack(side=tk.LEFT, padx=4)

    self.delete_node_button = tk.Button(
      self.toolbar,
      text="Delete Selected",
      command=self.delete_selected_node,
    )
    self.delete_node_button.pack(side=tk.LEFT, padx=4)

    self.clear_selection_button = tk.Button(
      self.toolbar,
      text="Clear Selection",
      command=self.clear_selection,
    )
    self.clear_selection_button.pack(side=tk.LEFT, padx=4)

    self.save_button = tk.Button(
      self.toolbar,
      text="Save Page",
      command=self.save_page,
    )
    self.save_button.pack(side=tk.LEFT, padx=4)

    self.canvas = tk.Canvas(
      self.main_frame,
      bg="#202020",
      width=1200,
      height=750,
    )
    self.canvas.pack(fill=tk.BOTH, expand=True)

    self.canvas.bind("<Button-1>", self.canvas_click)
    self.canvas.bind("<B1-Motion>", self.canvas_drag)
    self.canvas.bind("<ButtonRelease-1>", self.canvas_release)
    self.canvas.bind("<Motion>", self.track_mouse)

    self.root.bind_all("<KeyPress>", self.handle_node_keybind)

  def load_tome(self, tome_entry):
    tome_id = tome_entry["id"]

    if tome_id not in self.loaded_tomes:
      self.loaded_tomes[tome_id] = load_tome_by_entry(tome_entry)

    return self.loaded_tomes[tome_id]

  def get_tome_names(self):
    return [entry["name"] for entry in self.tome_entries]

  def get_tome_entry_by_name(self, tome_name):
    for entry in self.tome_entries:
      if entry["name"] == tome_name:
        return entry

    return self.tome_entries[0]

  def sync_current_page(self):
    page_key = str(self.page_number)
    self.current_tome["pages"][page_key]["nodes"] = self.nodes
    self.current_tome["pages"][page_key]["edges"] = self.edges

  def refresh_tome_dropdown(self):
    self.tome_dropdown["values"] = self.get_tome_names()
    self.tome_var.set(self.tome_name)

  def change_tome(self, event=None):
    self.sync_current_page()

    self.current_tome_entry = self.get_tome_entry_by_name(self.tome_var.get())
    self.current_tome = self.load_tome(self.current_tome_entry)
    self.tome_name = self.current_tome_entry["name"]

    page_values = self.get_page_values_for_current_tome()
    self.page_number = int(page_values[0])
    self.page_var.set(page_values[0])
    self.page_dropdown["values"] = page_values

    page_key = str(self.page_number)
    self.nodes = self.current_tome["pages"][page_key]["nodes"]
    self.edges = self.current_tome["pages"][page_key]["edges"]

    self.selected_node = None
    self.dragging_node = None
    self.redraw()

  def change_page(self, event=None):
    self.sync_current_page()

    self.page_number = int(self.page_var.get())
    page_key = str(self.page_number)

    self.nodes = self.current_tome["pages"][page_key]["nodes"]
    self.edges = self.current_tome["pages"][page_key]["edges"]

    self.selected_node = None
    self.dragging_node = None
    self.redraw()

  def add_tome(self):
    self.sync_current_page()
    self.current_tome_entry, self.index_data = add_new_tome(self.index_data)
    self.tome_entries = self.index_data["tomes"]
    self.current_tome = self.load_tome(self.current_tome_entry)
    self.tome_name = self.current_tome_entry["name"]

    self.refresh_tome_dropdown()

    self.page_number = 1
    self.page_var.set("1")
    self.page_dropdown["values"] = self.get_page_values_for_current_tome()

    self.nodes = self.current_tome["pages"]["1"]["nodes"]
    self.edges = self.current_tome["pages"]["1"]["edges"]

    self.selected_node = None
    self.dragging_node = None
    self.redraw()

  def handle_node_keybind(self, event):
    key = event.keysym

    key_map = {
      "1": "prologue",
      "2": "normal",
      "3": "mastery",
      "4": "epilogue",
      "5": "glyph",
      "6": "core_memory",
    }

    clear_map = {
      "9": self.clear_all_edges,
      "0": self.clear_all_nodes,
    }

    layout_map = {
      "8": self.center_and_snap_graph,
    }

    clear_action = clear_map.get(key)

    if clear_action is not None:
      return clear_action()

    layout_action = layout_map.get(key)

    if layout_action is not None:
      return layout_action()

    node_type = key_map.get(key)

    if node_type is not None:
      self.create_node(node_type)
      return "break"

    return

  def create_node(self, node_type):
    previous_selected_node = self.selected_node
    node_id = self.get_next_node_id(node_type)
    node_name = self.get_default_node_name(node_type, node_id)
    x, y = self.get_new_node_position()

    self.nodes[node_id] = {
      "name": node_name,
      "type": node_type,
      "x": x,
      "y": y,
    }

    if previous_selected_node is not None and previous_selected_node in self.nodes:
      edge = sorted([previous_selected_node, node_id])

      if edge not in self.edges:
        self.edges.append(edge)

    self.selected_node = node_id
    self.dragging_node = None
    self.sync_current_page()
    self.redraw()

  def get_next_node_id(self, node_type):
    base_map = {
      "prologue": "P",
      "epilogue": "E",
      "normal": "N",
      "mastery": "M",
      "glyph": "G",
      "core_memory": "C",
    }
    base_id = base_map.get(node_type, "N")

    if base_id not in self.nodes:
      return base_id

    counter = 2 if node_type in {"prologue", "epilogue"} else 1

    while f"{base_id}{counter}" in self.nodes:
      counter += 1

    return f"{base_id}{counter}"

  def get_default_node_name(self, node_type, node_id):
    display_names = {
      "prologue": "Prologue",
      "epilogue": "Epilogue",
      "normal": "Normal Challenge",
      "mastery": "Mastery Challenge",
      "glyph": "Glyph Challenge",
      "core_memory": "Core Memory Challenge",
    }

    return f"{display_names.get(node_type, 'Challenge')} {node_id}"

  def get_new_node_position(self):
    if self.last_mouse_x is not None and self.last_mouse_y is not None:
      return self.last_mouse_x, self.last_mouse_y

    self.canvas.update_idletasks()

    return (
      max(self.canvas.winfo_width() // 2, 100),
      max(self.canvas.winfo_height() // 2, 100),
    )

  def track_mouse(self, event):
    self.last_mouse_x = event.x
    self.last_mouse_y = event.y

  def canvas_click(self, event):
    clicked_node = self.find_node_at(event.x, event.y)

    if clicked_node is None:
      self.clear_selection()
      return

    self.dragging_node = clicked_node

    if self.selected_node is None:
      self.selected_node = clicked_node
    elif self.selected_node == clicked_node:
      self.selected_node = None
    else:
      self.toggle_edge(self.selected_node, clicked_node)
      self.selected_node = clicked_node

    self.sync_current_page()
    self.redraw()

  def canvas_drag(self, event):
    if self.dragging_node is None:
      return

    self.nodes[self.dragging_node]["x"] = event.x
    self.nodes[self.dragging_node]["y"] = event.y

    self.sync_current_page()
    self.redraw()

  def canvas_release(self, event):
    self.dragging_node = None

  def find_node_at(self, x, y):
    for node_id, node in self.nodes.items():
      dx = x - node["x"]
      dy = y - node["y"]

      if dx * dx + dy * dy <= NODE_RADIUS * NODE_RADIUS:
        return node_id

    return None

  def toggle_edge(self, left, right):
    if left == right:
      return

    edge = sorted([left, right])

    if edge in self.edges:
      self.edges.remove(edge)
    else:
      self.edges.append(edge)

  def delete_selected_node(self):
    if self.selected_node is None:
      return

    node_id = self.selected_node
    del self.nodes[node_id]

    self.edges = [
      edge
      for edge in self.edges
      if node_id not in edge
    ]

    self.selected_node = None
    self.sync_current_page()
    self.redraw()

  def clear_selection(self):
    self.selected_node = None
    self.dragging_node = None
    self.redraw()

  def clear_all_edges(self):
    self.edges.clear()
    self.selected_node = None
    self.dragging_node = None
    self.sync_current_page()
    self.redraw()
    return "break"

  def clear_all_nodes(self):
    self.nodes.clear()
    self.edges.clear()
    self.selected_node = None
    self.dragging_node = None
    self.sync_current_page()
    self.redraw()
    return "break"

  def center_and_snap_graph(self, event=None):
    if not self.nodes:
      return "break"

    self.canvas.update_idletasks()

    center_x = self.canvas.winfo_width() / 2
    center_y = self.canvas.winfo_height() / 2

    old_positions = {
      node_id: (node["x"], node["y"])
      for node_id, node in self.nodes.items()
    }

    min_x = min(position[0] for position in old_positions.values())
    max_x = max(position[0] for position in old_positions.values())
    min_y = min(position[1] for position in old_positions.values())
    max_y = max(position[1] for position in old_positions.values())
    graph_center_x = (min_x + max_x) / 2
    graph_center_y = (min_y + max_y) / 2

    new_positions = {}

    for node_id, position in old_positions.items():
      dx = position[0] - graph_center_x
      dy = position[1] - graph_center_y
      distance = max(math.hypot(dx, dy), MIN_LAYOUT_RADIUS)
      angle = self.snap_angle(math.degrees(math.atan2(dy, dx)))
      radians = math.radians(angle)

      new_positions[node_id] = (
        center_x + math.cos(radians) * distance,
        center_y + math.sin(radians) * distance,
      )

    for _ in range(20):
      moved = self.enforce_minimum_node_spacing(new_positions)
      self.keep_nodes_inside_canvas(new_positions)

      if not moved:
        break

    for node_id, position in new_positions.items():
      self.nodes[node_id]["x"] = position[0]
      self.nodes[node_id]["y"] = position[1]

    self.selected_node = None
    self.dragging_node = None
    self.sync_current_page()
    self.redraw()

    return "break"

  def snap_angle(self, angle):
    normalized_angle = angle % 360
    valid_angles = [0, 45, 90, 135, 180, 225, 270, 315]
    major_angles = [0, 90, 180, 270]

    closest_major_angle = min(
      major_angles,
      key=lambda valid_angle: self.get_angle_difference(normalized_angle, valid_angle),
    )

    if self.get_angle_difference(normalized_angle, closest_major_angle) <= 30:
      return closest_major_angle

    return min(
      valid_angles,
      key=lambda valid_angle: self.get_angle_difference(normalized_angle, valid_angle),
    )

  def get_angle_difference(self, left_angle, right_angle):
    return abs((left_angle - right_angle + 180) % 360 - 180)

  def enforce_minimum_node_spacing(self, new_positions):
    node_ids = list(new_positions.keys())
    moved_any_node = False

    for left_index in range(len(node_ids)):
      for right_index in range(left_index + 1, len(node_ids)):
        left_id = node_ids[left_index]
        right_id = node_ids[right_index]
        left_x, left_y = new_positions[left_id]
        right_x, right_y = new_positions[right_id]
        dx = right_x - left_x
        dy = right_y - left_y
        distance = math.hypot(dx, dy)

        if distance >= MIN_NODE_SPACING:
          continue

        if distance == 0:
          dx = 1
          dy = 0
          distance = 1

        overlap = MIN_NODE_SPACING - distance
        push_x = dx / distance * overlap / 2
        push_y = dy / distance * overlap / 2

        new_positions[left_id] = (
          left_x - push_x,
          left_y - push_y,
        )
        new_positions[right_id] = (
          right_x + push_x,
          right_y + push_y,
        )
        moved_any_node = True

    return moved_any_node

  def keep_nodes_inside_canvas(self, new_positions):
    canvas_width = self.canvas.winfo_width()
    canvas_height = self.canvas.winfo_height()

    for node_id, position in new_positions.items():
      x, y = position

      new_positions[node_id] = (
        min(max(x, CANVAS_NODE_PADDING), canvas_width - CANVAS_NODE_PADDING),
        min(max(y, CANVAS_NODE_PADDING), canvas_height - CANVAS_NODE_PADDING),
      )

  def get_short_node_type_label(self, node_type):
    labels = {
      "prologue": "Prologue",
      "epilogue": "Epilogue",
      "normal": "Normal",
      "mastery": "Mastery",
      "glyph": "Glyph",
      "core_memory": "Memory",
    }

    return labels.get(node_type, node_type)

  def get_page_values_for_current_tome(self):
    page_keys = list(self.current_tome["pages"].keys())

    return sorted(
      page_keys,
      key=lambda page_key: int(page_key) if str(page_key).isdigit() else str(page_key),
    )

  def redraw(self):
    self.canvas.delete("all")

    for left, right in self.edges:
      if left not in self.nodes or right not in self.nodes:
        continue

      left_node = self.nodes[left]
      right_node = self.nodes[right]

      self.canvas.create_line(
        left_node["x"],
        left_node["y"],
        right_node["x"],
        right_node["y"],
        fill="#cccccc",
        width=3,
      )

    for node_id, node in self.nodes.items():
      x = node["x"]
      y = node["y"]
      color = NODE_COLORS.get(node["type"], "#dddddd")
      outline = "#ffffff"
      width = 2

      if node_id == self.selected_node:
        outline = "#ffff00"
        width = 5

      self.canvas.create_oval(
        x - NODE_RADIUS,
        y - NODE_RADIUS,
        x + NODE_RADIUS,
        y + NODE_RADIUS,
        fill=color,
        outline=outline,
        width=width,
      )

      self.canvas.create_text(
        x,
        y - 7,
        text=node_id,
        fill="#000000",
        font=("Arial", 11, "bold"),
      )

      self.canvas.create_text(
        x,
        y + 10,
        text=self.get_short_node_type_label(node["type"]),
        fill="#000000",
        font=("Arial", 8),
      )

  def validate_page(self):
    incomplete_pages = []

    self.sync_current_page()

    for tome_entry in self.tome_entries:
      tome_data = self.load_tome(tome_entry)
      tome_name = tome_entry["name"]

      for page_number in range(1, 5):
        page_key = str(page_number)
        page_data = tome_data["pages"][page_key]
        nodes = page_data["nodes"]
        if len(nodes) == 0:
          continue

        prologues = [
          node_id
          for node_id, node in nodes.items()
          if node["type"] == "prologue"
        ]

        epilogues = [
          node_id
          for node_id, node in nodes.items()
          if node["type"] == "epilogue"
        ]

        if len(prologues) == 0 or len(epilogues) == 0:
          incomplete_pages.append(f"{tome_name} Page {page_number}")

    if incomplete_pages:
      return messagebox.askyesno(
        "Incomplete Tome Archive",
        "Some pages may be incomplete:\n"
        + "\n".join(incomplete_pages)
        + "\n\nSave anyway?",
      )

    return True

  def save_page(self):
    if not self.validate_page():
      return

    self.sync_current_page()
    save_tome(self.current_tome_entry, self.current_tome)


def run_editor():
  root = tk.Tk()
  root.geometry("1300x850")
  TomePageEditor(root)
  root.mainloop()


if __name__ == "__main__":
  run_editor()
