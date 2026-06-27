import tkinter as tk
from pathlib import Path

from PIL import Image
from PIL import ImageTk

from optimizer import optimize_page
from storage import load_tome_by_entry
from storage import load_tome_index


APP_FOLDER = Path(__file__).resolve().parent
TOME_ICON_PATH = APP_FOLDER / "scroll.png"
PAGE_ICON_PATH = APP_FOLDER / "page.webp"

NODE_RADIUS = 34
BACKGROUND_COLOR = "#202020"
EDGE_COLOR = "#cccccc"
TOME_ICON_SIZE = (90, 90)
PAGE_ICON_SIZE = (60, 80)

NODE_COLORS = {
  "prologue": "#9ad0f5",
  "epilogue": "#c9a0ff",
  "claimed": "#7fd87f",
  "banked": "#ff7f7f",
  "unavailable": "#777777",
}


class TomeViewer:
  def __init__(self, root):
    self.root = root
    self.root.title("DBD Tome Optimizer Viewer")

    self.index_data = load_tome_index()
    self.tome_entries = self.index_data["tomes"]
    self.loaded_tomes = {}
    self.optimizer_cache = {}

    self.current_tome_entry = self.tome_entries[0]
    self.current_tome = self.load_tome(self.current_tome_entry)
    self.current_page = "1"

    self.current_result = None
    self.scaled_positions = {}
    self.book_buttons = {}
    self.page_buttons = {}
    self.tome_icon = None
    self.page_icon = None

    self.load_icons()
    self.build_gui()
    self.load_current_page()

  def load_icons(self):
    self.tome_icon = self.load_icon(
      TOME_ICON_PATH,
      TOME_ICON_SIZE,
    )
    self.page_icon = self.load_icon(
      PAGE_ICON_PATH,
      PAGE_ICON_SIZE,
    )

  def load_icon(self, image_path, size):
    if not image_path.exists():
      return None

    image = Image.open(image_path).convert("RGBA")
    image = image.resize(size, Image.LANCZOS)

    return ImageTk.PhotoImage(image)

  def build_gui(self):
    self.main_frame = tk.Frame(self.root, bg=BACKGROUND_COLOR)
    self.main_frame.pack(fill=tk.BOTH, expand=True)

    self.book_area = tk.Frame(self.main_frame, bg="#151515")
    self.book_area.pack(side=tk.TOP, fill=tk.X)

    self.book_canvas = tk.Canvas(
      self.book_area,
      bg="#151515",
      height=136,
      highlightthickness=0,
    )
    self.book_canvas.pack(side=tk.TOP, fill=tk.X)

    self.book_scrollbar = tk.Scrollbar(
      self.book_area,
      orient=tk.HORIZONTAL,
      command=self.book_canvas.xview,
    )
    self.book_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    self.book_canvas.configure(xscrollcommand=self.book_scrollbar.set)

    self.book_frame = tk.Frame(self.book_canvas, bg="#151515")
    self.book_canvas.create_window(
      (0, 0),
      window=self.book_frame,
      anchor="nw",
    )

    self.book_frame.bind("<Configure>", self.update_book_scroll_region)
    self.book_canvas.bind("<MouseWheel>", self.scroll_books)
    self.book_frame.bind("<MouseWheel>", self.scroll_books)

    self.create_book_buttons()

    self.title_label = tk.Label(
      self.main_frame,
      text="",
      bg=BACKGROUND_COLOR,
      fg="#ffffff",
      font=("Arial", 16, "bold"),
    )
    self.title_label.pack(side=tk.TOP, fill=tk.X, pady=4)

    self.canvas = tk.Canvas(
      self.main_frame,
      bg=BACKGROUND_COLOR,
      width=1200,
      height=650,
      highlightthickness=0,
    )
    self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    self.canvas.bind("<Configure>", self.redraw)

    self.info_label = tk.Label(
      self.main_frame,
      text="",
      bg=BACKGROUND_COLOR,
      fg="#ffffff",
      font=("Arial", 11),
      justify=tk.LEFT,
      anchor="w",
    )
    self.info_label.pack(side=tk.TOP, fill=tk.X, padx=8, pady=4)

    self.legend_label = tk.Label(
      self.main_frame,
      text="Blue = Prologue | Purple = Epilogue | Green = Claim | Red = Leave unclaimed",
      bg=BACKGROUND_COLOR,
      fg="#ffffff",
      font=("Arial", 10),
    )
    self.legend_label.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(0, 4))

    self.page_frame = tk.Frame(self.main_frame, bg="#151515")
    self.page_frame.pack(side=tk.BOTTOM, fill=tk.X)

    self.create_page_buttons()

  def update_book_scroll_region(self, event=None):
    self.book_canvas.configure(
      scrollregion=self.book_canvas.bbox("all"),
    )

  def scroll_books(self, event):
    if event.delta > 0:
      self.book_canvas.xview_scroll(-3, "units")
    else:
      self.book_canvas.xview_scroll(3, "units")

    return "break"

  def create_book_buttons(self):
    for child in self.book_frame.winfo_children():
      child.destroy()

    self.book_buttons = {}

    for tome_entry in self.tome_entries:
      tome_id = tome_entry["id"]
      tome_name = tome_entry["name"]
      is_selected = tome_id == self.current_tome_entry["id"]

      book_holder = tk.Frame(
        self.book_frame,
        bg="#151515",
        highlightthickness=3 if is_selected else 0,
        highlightbackground="#ffd966",
      )
      book_holder.pack(side=tk.LEFT, padx=8, pady=8)

      icon_label = tk.Label(
        book_holder,
        image=self.tome_icon,
        bg="#151515",
        cursor="hand2",
      )
      icon_label.pack()

      text_label = tk.Label(
        book_holder,
        text=tome_name,
        bg="#151515",
        fg="#ffffff",
        font=("Arial", 10, "bold"),
        cursor="hand2",
      )
      text_label.pack()

      icon_label.bind(
        "<Button-1>",
        lambda event, entry=tome_entry: self.select_tome(entry),
      )
      text_label.bind(
        "<Button-1>",
        lambda event, entry=tome_entry: self.select_tome(entry),
      )

      icon_label.bind("<MouseWheel>", self.scroll_books)
      text_label.bind("<MouseWheel>", self.scroll_books)
      book_holder.bind("<MouseWheel>", self.scroll_books)

      self.book_buttons[tome_id] = book_holder

  def create_page_buttons(self):
    for child in self.page_frame.winfo_children():
      child.destroy()

    self.page_buttons = {}

    for page_number in ["1", "2", "3", "4"]:
      is_selected = page_number == self.current_page

      page_holder = tk.Frame(
        self.page_frame,
        bg="#151515",
        highlightthickness=3 if is_selected else 0,
        highlightbackground="#ffd966",
      )
      page_holder.pack(side=tk.LEFT, expand=True, padx=8, pady=8)

      icon_label = tk.Label(
        page_holder,
        image=self.page_icon,
        bg="#151515",
        cursor="hand2",
      )
      icon_label.pack()

      text_label = tk.Label(
        page_holder,
        text=f"Page {page_number}",
        bg="#151515",
        fg="#ffffff",
        font=("Arial", 10, "bold"),
        cursor="hand2",
      )
      text_label.pack()

      icon_label.bind(
        "<Button-1>",
        lambda event, page=page_number: self.select_page(page),
      )
      text_label.bind(
        "<Button-1>",
        lambda event, page=page_number: self.select_page(page),
      )

      self.page_buttons[page_number] = page_holder

  def update_selected_controls(self):
    for tome_id, holder in self.book_buttons.items():
      holder.configure(
        highlightthickness=3 if tome_id == self.current_tome_entry["id"] else 0,
        highlightbackground="#ffd966",
      )

    for page_number, holder in self.page_buttons.items():
      holder.configure(
        highlightthickness=3 if page_number == self.current_page else 0,
        highlightbackground="#ffd966",
      )

  def load_tome(self, tome_entry):
    tome_id = tome_entry["id"]

    if tome_id not in self.loaded_tomes:
      self.loaded_tomes[tome_id] = load_tome_by_entry(tome_entry)

    return self.loaded_tomes[tome_id]

  def select_tome(self, tome_entry):
    self.current_tome_entry = tome_entry
    self.current_tome = self.load_tome(tome_entry)
    self.current_page = "1"
    self.create_book_buttons()
    self.create_page_buttons()
    self.load_current_page()

  def select_page(self, page_number):
    self.current_page = page_number
    self.create_page_buttons()
    self.load_current_page()

  def load_current_page(self):
    page_data = self.get_current_page_data()
    cache_key = (
      self.current_tome_entry["id"],
      self.current_page,
    )

    if cache_key not in self.optimizer_cache:
      self.optimizer_cache[cache_key] = optimize_page(
        page_data,
        int(self.current_page),
      )

    self.current_result = self.optimizer_cache[cache_key]

    self.title_label.configure(
      text=f"{self.current_tome_entry['name']} - Page {self.current_page}",
    )

    self.update_selected_controls()
    self.update_info_label(page_data)
    self.redraw()

  def get_current_page_data(self):
    return self.current_tome["pages"].get(
      self.current_page,
      {
        "nodes": {},
        "edges": [],
      },
    )

  def update_info_label(self, page_data):
    result = self.current_result

    if result is None:
      self.info_label.configure(text="")
      return

    if not result["valid"]:
      self.info_label.configure(
        text=f"Invalid page: {result['reason']}",
      )
      return

    info = (
      f"Banked BP: {result['banked_bp']:,} / {result['total_bp']:,}    "
      f"Claimed BP: {result['claimed_bp']:,}"
    )

    self.info_label.configure(text=info)

  def redraw(self, event=None):
    if not hasattr(self, "canvas"):
      return

    self.canvas.delete("all")

    page_data = self.get_current_page_data()
    nodes = page_data.get("nodes", {})
    edges = page_data.get("edges", [])

    if not nodes:
      self.canvas.create_text(
        self.canvas.winfo_width() / 2,
        self.canvas.winfo_height() / 2,
        text="No nodes on this page.",
        fill="#ffffff",
        font=("Arial", 16, "bold"),
      )
      return

    self.scaled_positions = self.get_scaled_positions(nodes)

    for left_id, right_id in edges:
      if left_id not in self.scaled_positions:
        continue

      if right_id not in self.scaled_positions:
        continue

      left_x, left_y = self.scaled_positions[left_id]
      right_x, right_y = self.scaled_positions[right_id]

      self.canvas.create_line(
        left_x,
        left_y,
        right_x,
        right_y,
        fill=EDGE_COLOR,
        width=3,
      )

    for node_id, node in nodes.items():
      if node_id not in self.scaled_positions:
        continue

      x, y = self.scaled_positions[node_id]
      color = self.get_node_color(node_id, node)

      self.canvas.create_oval(
        x - NODE_RADIUS,
        y - NODE_RADIUS,
        x + NODE_RADIUS,
        y + NODE_RADIUS,
        fill=color,
        outline="#ffffff",
        width=2,
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
        text=self.get_short_node_type_label(node.get("type")),
        fill="#000000",
        font=("Arial", 8),
      )

  def get_node_color(self, node_id, node):
    node_type = node.get("type")

    if node_type == "prologue":
      return NODE_COLORS["prologue"]

    if node_type == "epilogue":
      return NODE_COLORS["epilogue"]

    if self.current_result is None or not self.current_result["valid"]:
      return NODE_COLORS["unavailable"]

    if node_id in self.current_result["claimed"]:
      return NODE_COLORS["claimed"]

    if node_id in self.current_result["banked"]:
      return NODE_COLORS["banked"]

    return NODE_COLORS["unavailable"]

  def get_scaled_positions(self, nodes):
    canvas_width = max(self.canvas.winfo_width(), 200)
    canvas_height = max(self.canvas.winfo_height(), 200)

    padding = NODE_RADIUS + 30

    raw_positions = {
      node_id: (
        float(node.get("x", canvas_width / 2)),
        float(node.get("y", canvas_height / 2)),
      )
      for node_id, node in nodes.items()
    }

    min_x = min(position[0] for position in raw_positions.values())
    max_x = max(position[0] for position in raw_positions.values())
    min_y = min(position[1] for position in raw_positions.values())
    max_y = max(position[1] for position in raw_positions.values())

    graph_width = max(max_x - min_x, 1)
    graph_height = max(max_y - min_y, 1)

    available_width = max(canvas_width - padding * 2, 1)
    available_height = max(canvas_height - padding * 2, 1)

    scale = min(
      available_width / graph_width,
      available_height / graph_height,
      1.0,
    )

    scaled_width = graph_width * scale
    scaled_height = graph_height * scale

    offset_x = (canvas_width - scaled_width) / 2 - min_x * scale
    offset_y = (canvas_height - scaled_height) / 2 - min_y * scale

    scaled_positions = {}

    for node_id, position in raw_positions.items():
      x, y = position

      scaled_positions[node_id] = (
        x * scale + offset_x,
        y * scale + offset_y,
      )

    return scaled_positions

  def get_short_node_type_label(self, node_type):
    labels = {
      "prologue": "Prologue",
      "epilogue": "Epilogue",
      "normal": "Normal",
      "mastery": "Mastery",
      "glyph": "Glyph",
      "core_memory": "Memory",
    }

    return labels.get(node_type, node_type or "")


def run_viewer():
  root = tk.Tk()
  root.geometry("1300x900")
  TomeViewer(root)
  root.mainloop()


if __name__ == "__main__":
  run_viewer()
