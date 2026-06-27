import json
import re
from pathlib import Path


APP_FOLDER = Path(__file__).resolve().parent
TOME_DATA_FOLDER = APP_FOLDER / "tome_data"
TOME_INDEX_FILE = TOME_DATA_FOLDER / "tome_index.json"
LEGACY_ARCHIVE_FILE = APP_FOLDER / "tomes.json"


def get_empty_page():
  return {
    "nodes": {},
    "edges": [],
  }


def get_empty_tome(tome_id="tome_001", name="Tome 1", number=1):
  return {
    "id": tome_id,
    "name": name,
    "number": number,
    "pages": {
      "1": get_empty_page(),
      "2": get_empty_page(),
      "3": get_empty_page(),
      "4": get_empty_page(),
    },
  }


def get_empty_index():
  return {
    "version": 2,
    "tomes": [
      {
        "id": "tome_001",
        "name": "Tome 1",
        "number": 1,
        "file": "tome_001.json",
      },
    ],
  }


def ensure_tome_data_folder():
  TOME_DATA_FOLDER.mkdir(parents=True, exist_ok=True)


def get_tome_number_from_name(tome_name, fallback):
  match = re.search(r"(\d+)", str(tome_name))

  if match:
    return int(match.group(1))

  return fallback


def get_tome_id(number):
  return f"tome_{number:03d}"


def get_tome_file_name(tome_id):
  return f"{tome_id}.json"


def normalize_edge(edge):
  if not isinstance(edge, (list, tuple)):
    return None

  if len(edge) != 2:
    return None

  left = str(edge[0])
  right = str(edge[1])

  if left == right:
    return None

  return sorted([left, right])


def normalize_page(page_data):
  if not isinstance(page_data, dict):
    page_data = {}

  nodes = page_data.get("nodes", {})
  edges = page_data.get("edges", [])

  if not isinstance(nodes, dict):
    nodes = {}

  if not isinstance(edges, list):
    edges = []

  cleaned_nodes = {}

  for node_id, node_data in nodes.items():
    node_id = str(node_id)

    if not isinstance(node_data, dict):
      continue

    cleaned_nodes[node_id] = {
      "name": str(node_data.get("name", node_id)),
      "type": str(node_data.get("type", "normal")),
      "x": float(node_data.get("x", 100)),
      "y": float(node_data.get("y", 100)),
    }

  cleaned_edges = []

  for edge in edges:
    cleaned_edge = normalize_edge(edge)

    if cleaned_edge is None:
      continue

    if cleaned_edge[0] not in cleaned_nodes:
      continue

    if cleaned_edge[1] not in cleaned_nodes:
      continue

    if cleaned_edge not in cleaned_edges:
      cleaned_edges.append(cleaned_edge)

  return {
    "nodes": cleaned_nodes,
    "edges": cleaned_edges,
  }


def normalize_tome(tome_data, fallback_id="tome_001", fallback_name="Tome 1", fallback_number=1):
  if not isinstance(tome_data, dict):
    tome_data = {}

  tome_id = str(tome_data.get("id", fallback_id))
  name = str(tome_data.get("name", fallback_name))
  number = int(tome_data.get("number", fallback_number))

  raw_pages = tome_data.get("pages", {})

  if not isinstance(raw_pages, dict):
    raw_pages = {}

  pages = {}

  for page_number in range(1, 5):
    page_key = str(page_number)
    pages[page_key] = normalize_page(raw_pages.get(page_key, {}))

  for raw_page_key, raw_page_data in raw_pages.items():
    page_key = str(raw_page_key)

    if page_key not in pages:
      pages[page_key] = normalize_page(raw_page_data)

  return {
    "id": tome_id,
    "name": name,
    "number": number,
    "pages": pages,
  }


def sort_tome_entries(tome_entries):
  return sorted(
    tome_entries,
    key=lambda entry: (
      int(entry.get("number", 0)),
      str(entry.get("name", "")),
    ),
  )


def normalize_index(index_data):
  if not isinstance(index_data, dict):
    index_data = get_empty_index()

  index_data.setdefault("version", 2)
  raw_tomes = index_data.get("tomes", [])

  if not isinstance(raw_tomes, list):
    raw_tomes = []

  tome_entries = []
  seen_ids = set()

  for raw_entry in raw_tomes:
    if not isinstance(raw_entry, dict):
      continue

    name = str(raw_entry.get("name", "Tome"))
    number = int(raw_entry.get("number", get_tome_number_from_name(name, len(tome_entries) + 1)))
    tome_id = str(raw_entry.get("id", get_tome_id(number)))
    file_name = str(raw_entry.get("file", get_tome_file_name(tome_id)))

    if tome_id in seen_ids:
      continue

    seen_ids.add(tome_id)

    tome_entries.append(
      {
        "id": tome_id,
        "name": name,
        "number": number,
        "file": file_name,
      },
    )

  if not tome_entries:
    tome_entries = get_empty_index()["tomes"]

  return {
    "version": 2,
    "tomes": sort_tome_entries(tome_entries),
  }


def load_json(file_path):
  file_path = Path(file_path)

  with file_path.open("r", encoding="utf-8") as file:
    return json.load(file)


def save_json(file_path, data):
  file_path = Path(file_path)
  file_path.parent.mkdir(parents=True, exist_ok=True)

  with file_path.open("w", encoding="utf-8") as file:
    json.dump(data, file, indent=2)


def load_tome_index():
  ensure_storage_setup()

  if not TOME_INDEX_FILE.exists():
    index_data = get_empty_index()
    save_tome_index(index_data)
    return index_data

  return normalize_index(load_json(TOME_INDEX_FILE))


def save_tome_index(index_data):
  ensure_tome_data_folder()
  save_json(TOME_INDEX_FILE, normalize_index(index_data))


def get_tome_path(tome_entry):
  return TOME_DATA_FOLDER / tome_entry["file"]


def load_tome_by_entry(tome_entry):
  ensure_storage_setup()

  tome_path = get_tome_path(tome_entry)

  if not tome_path.exists():
    tome_data = get_empty_tome(
      tome_entry["id"],
      tome_entry["name"],
      tome_entry["number"],
    )
    save_tome(tome_entry, tome_data)
    return tome_data

  return normalize_tome(
    load_json(tome_path),
    tome_entry["id"],
    tome_entry["name"],
    tome_entry["number"],
  )


def save_tome(tome_entry, tome_data):
  normalized_tome = normalize_tome(
    tome_data,
    tome_entry["id"],
    tome_entry["name"],
    tome_entry["number"],
  )
  save_json(get_tome_path(tome_entry), normalized_tome)


def get_next_tome_entry(index_data):
  existing_numbers = [
    int(entry.get("number", 0))
    for entry in index_data.get("tomes", [])
  ]

  number = 1

  while number in existing_numbers:
    number += 1

  tome_id = get_tome_id(number)

  return {
    "id": tome_id,
    "name": f"Tome {number}",
    "number": number,
    "file": get_tome_file_name(tome_id),
  }


def add_new_tome(index_data):
  index_data = normalize_index(index_data)
  tome_entry = get_next_tome_entry(index_data)
  index_data["tomes"].append(tome_entry)
  index_data["tomes"] = sort_tome_entries(index_data["tomes"])

  save_tome_index(index_data)
  save_tome(
    tome_entry,
    get_empty_tome(
      tome_entry["id"],
      tome_entry["name"],
      tome_entry["number"],
    ),
  )

  return tome_entry, index_data


def migrate_legacy_archive_to_tome_files(archive_data):
  if not isinstance(archive_data, dict):
    return get_empty_index()

  raw_tomes = archive_data.get("tomes", {})

  if not isinstance(raw_tomes, dict):
    return get_empty_index()

  ensure_tome_data_folder()
  index_data = {
    "version": 2,
    "tomes": [],
  }

  for fallback_number, (tome_name, tome_data) in enumerate(raw_tomes.items(), start=1):
    number = get_tome_number_from_name(tome_name, fallback_number)
    tome_id = get_tome_id(number)
    file_name = get_tome_file_name(tome_id)

    tome_entry = {
      "id": tome_id,
      "name": str(tome_name),
      "number": number,
      "file": file_name,
    }

    normalized_tome = normalize_tome(
      {
        "id": tome_id,
        "name": str(tome_name),
        "number": number,
        "pages": tome_data.get("pages", {}) if isinstance(tome_data, dict) else {},
      },
      tome_id,
      str(tome_name),
      number,
    )

    index_data["tomes"].append(tome_entry)
    save_tome(tome_entry, normalized_tome)

  index_data = normalize_index(index_data)
  save_tome_index(index_data)

  return index_data


def ensure_storage_setup():
  ensure_tome_data_folder()

  if TOME_INDEX_FILE.exists():
    return

  if LEGACY_ARCHIVE_FILE.exists():
    migrate_legacy_archive_to_tome_files(load_json(LEGACY_ARCHIVE_FILE))
    return

  index_data = get_empty_index()
  save_tome_index(index_data)
  save_tome(index_data["tomes"][0], get_empty_tome())


# Backward-compatible helpers for older imports.
def get_empty_archive():
  tome = get_empty_tome()

  return {
    "tomes": {
      tome["name"]: {
        "pages": tome["pages"],
      },
    },
  }


def load_archive_from_json(file_path):
  return migrate_legacy_archive_to_tome_files(load_json(file_path))


def save_archive_to_json(file_path, archive_data):
  index_data = migrate_legacy_archive_to_tome_files(archive_data)
  save_tome_index(index_data)
