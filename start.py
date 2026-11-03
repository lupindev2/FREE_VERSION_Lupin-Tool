from pathlib import Path
import runpy


if __name__ == "__main__":
    intro = Path(__file__).resolve().parent / "main" / "main.py"
    runpy.run_path(str(intro), run_name="__main__")