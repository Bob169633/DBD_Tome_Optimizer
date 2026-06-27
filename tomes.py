SAMPLE_TOME = {
  "name": "Sample Tome",
  "pages": {
    1: {
      "nodes": {
        "P": {
          "name": "Prologue",
          "type": "prologue",
        },
        "A": {
          "name": "Repair Specialist",
          "type": "normal",
        },
        "B": {
          "name": "Master Survivor",
          "type": "mastery",
        },
        "C": {
          "name": "Glyph Seeker",
          "type": "glyph",
        },
        "D": {
          "name": "Bloodweb Choice",
          "type": "normal",
        },
        "E": {
          "name": "Epilogue",
          "type": "epilogue",
        },
      },
      "edges": [
        ("P", "A"),
        ("A", "B"),
        ("A", "C"),
        ("B", "E"),
        ("C", "D"),
        ("D", "E"),
      ],
    },
  },
}