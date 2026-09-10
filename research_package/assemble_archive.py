"""Assemble a local scientific archive, with explicit exclusions and hashes."""
import hashlib
import json
import shutil
from pathlib import Path
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parent.parent
HERE=ROOT/'research_package'
OUT=ROOT/'output/research_packages'


def write_json(path, value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def include(path):
    rel=path.relative_to(ROOT)
    if any(p in {'tmp','__pycache__','.pytest_cache','.git'} for p in rel.parts):
        return False
    if path.name in {'active_job.json','safe_runner.lock','resource_monitor.csv','archive_summary.json','package_manifest.json'}:
        return False
    if path.suffix in {'.pyc','.aux','.fls','.fdb_latexmk','.out','.synctex','.gz','.zip'}:
        return False
    if path.suffix=='.log' and rel.parts[:2]!=('research_package','results'):
        return False
    return path.is_file()


def main():
    validation=json.loads((HERE/'results/validation.json').read_text())
    readiness=json.loads((HERE/'results/readiness.json').read_text())
    if not (validation['complete'] and validation['all_passed'] and readiness['complete']):
        raise RuntimeError('Cannot package unfinished or failed checks')
    branches=[]
    for directory in sorted((ROOT/'experiments').iterdir()):
        if not directory.is_dir() or directory.name.startswith('_'):
            continue
        files=[p for p in directory.rglob('*') if include(p)]
        reports=[str(p.relative_to(ROOT)).replace('\\','/') for p in files
                 if p.suffix=='.md' and any(t in p.name for t in ('REPORT','README','THEORY','THEOREM','AUDIT','GATE'))]
        results=ROOT/'results'/directory.name
        if results.exists():
            reports += [str(p.relative_to(ROOT)).replace('\\','/') for p in results.rglob('*.md') if include(p)]
        branches.append(dict(branch=directory.name,source_files=len(files),reports=sorted(reports)))
    write_json(HERE/'branch_inventory.json',dict(branch_count=len(branches),branches=branches))
    selected=set()
    for name in ('experiments','results','prior_work','research_package','output/pdf/prepared_20260910'):
        selected.update(p for p in (ROOT/name).rglob('*') if include(p))
    selected.update(p for p in ROOT.iterdir() if p.is_file() and include(p))
    required=sum(p.stat().st_size for p in selected)+64*1024*1024
    if shutil.disk_usage(ROOT).free < required:
        raise RuntimeError('Insufficient disk space for safe archive creation; no archive written')
    records=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(selected)]
    base=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    manifest=dict(base_commit=base,working_tree_snapshot=True,uploaded=False,
        complete_self_contained_reproduction=False,
        exclusions=['Caches and runtime state','Git metadata','Third-party submodule working trees',
                    'Dense 24q reference arrays not present in this checkout; see exact_references.json'],
        files=records)
    write_json(HERE/'package_manifest.json',manifest)
    selected.add(HERE/'package_manifest.json')
    OUT.mkdir(parents=True,exist_ok=True)
    archive=OUT/'quantum_research_package_20260910_final.zip'
    temporary=archive.with_suffix('.zip.tmp')
    if temporary.exists():
        temporary.unlink()
    with ZipFile(temporary,'x',compression=ZIP_DEFLATED,compresslevel=6) as z:
        for path in sorted(selected):
            z.write(path,path.relative_to(ROOT).as_posix())
    with ZipFile(temporary) as z:
        if z.testzip() is not None:
            raise RuntimeError('ZIP CRC validation failed')
        for record in records:
            with z.open(record['path']) as stream:
                if hashlib.file_digest(stream,'sha256').hexdigest()!=record['sha256']:
                    raise RuntimeError(f'Archived hash mismatch: {record["path"]}')
    temporary.replace(archive)
    summary=dict(archive=archive.relative_to(ROOT).as_posix(),bytes=archive.stat().st_size,
        sha256=sha(archive),files=len(selected),branches=len(branches),crc_verified=True,
        all_archived_hashes_verified=True,uploaded=False)
    write_json(HERE/'archive_summary.json',summary)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
