"""Build and quality-check the QAOA manuscript and supplement."""

from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "output" / "pdf"
DOCUMENTS = (
    ("main.tex", "qaoa_mps_rank_certification_manuscript"),
    ("supplement.tex", "qaoa_mps_rank_certification_supplement"),
)


def run(command: list[str]) -> None:
    result = subprocess.run(
        command,
        cwd=HERE,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=180,
    )
    if result.returncode:
        raise RuntimeError(result.stdout[-6000:] + result.stderr[-2000:])


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for source, jobname in DOCUMENTS:
        command = [
            "pdflatex",
            "--disable-installer",
            "-no-shell-escape",
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-jobname={jobname}",
            f"-output-directory={OUTPUT}",
            source,
        ]
        run(command)
        run(command)
        log = (OUTPUT / f"{jobname}.log").read_text(
            encoding="utf-8", errors="replace"
        )
        forbidden = (
            "Overfull",
            "undefined references",
            "multiply defined",
            "LaTeX Warning: Citation",
        )
        found = [line for line in log.splitlines() if any(x in line for x in forbidden)]
        if found:
            raise RuntimeError(
                f"LaTeX quality checks failed for {source}:\n" + "\n".join(found)
            )
        print(OUTPUT / f"{jobname}.pdf")


if __name__ == "__main__":
    main()
