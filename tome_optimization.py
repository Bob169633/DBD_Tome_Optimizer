from tome_viewer import run_viewer
from tome_editor import run_editor

EDIT = False
def main():
  if EDIT:
    run_editor()
  run_viewer()


if __name__ == "__main__":
  main()
