"""Build and validate the standalone C038 manuscript without latexmk."""
from pathlib import Path
import shutil
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BUILD = ROOT / "tmp" / "pdfs" / "c038_standalone" / "build"
OUTPUT = ROOT / "output" / "pdf" / "c038_line_graph_pauli_matching_theorem.pdf"


def run(command, cwd=ROOT):
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=180,
    )
    if result.returncode:
        raise RuntimeError(result.stdout[-6000:] + result.stderr[-2000:])


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    args = [
        "pdflatex",
        "--disable-installer",
        "-no-shell-escape",
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-output-directory={BUILD}",
        str(HERE / "main.tex"),
    ]
    run(args)
    run(args)
    run(["python", str(HERE / "check_paper.py")])
    log = (BUILD / "main.log").read_text(encoding="utf-8", errors="replace")
    forbidden = ("Overfull", "undefined references", "multiply defined")
    found = [line for line in log.splitlines() if any(x in line for x in forbidden)]
    if found:
        raise RuntimeError("LaTeX quality checks failed:\n" + "\n".join(found))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(BUILD / "main.pdf", OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
