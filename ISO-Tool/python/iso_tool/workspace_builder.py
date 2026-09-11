"""Multi-repository build/stage orchestration for the Chimera II ISO workspace."""
from __future__ import annotations
import json, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from .github_source import prepare_source
from .build_entrypoint import build
from .boot_builder import build_spit_fire
from .image import create_iso

DEFAULT_REPOSITORIES = {
    "chimera-ii-os": "https://github.com/amerhwitat/ChimeraIIOS",
    "bizx": "https://github.com/amerhwitat/BizX",
    "bizxtreme": "https://github.com/amerhwitat/BizXtreme",
}

def _safe_id(value: str) -> str:
    return ''.join(c.lower() if c.isalnum() else '-' for c in value).strip('-') or 'repository'

def load_profiles(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))

def _stage_dir(source: Path, result: dict, root: Path, repo_id: str) -> None:
    repo_root = root / 'src' / repo_id
    repo_root.mkdir(parents=True, exist_ok=True)
    for p in source.rglob('*'):
        if not p.is_file() or '.git' in p.parts:
            continue
        dst = repo_root / p.relative_to(source)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
    for kind, key in (('executables', 'executables'), ('libraries', 'libraries'), ('boot-images', 'boot_images')):
        srcdir = Path(result['layout'][key])
        if not srcdir.exists():
            continue
        dst = root / kind / repo_id
        dst.mkdir(parents=True, exist_ok=True)
        for p in srcdir.rglob('*'):
            if p.is_file(): shutil.copy2(p, dst / p.name)

def build_workspace(repositories: dict[str, str], output: Path, compiler: str = 'auto', workers: int | None = None, log=print) -> dict:
    """Acquire, recursively build, and stage several related repositories into one ISO workspace."""
    output = Path(output).resolve()
    sources = output / 'sources'
    sources.mkdir(parents=True, exist_ok=True)
    reports = {}
    def one(item):
        repo_id, ref = item
        source = prepare_source(ref, sources / _safe_id(repo_id))
        result = build(source, output / 'repositories' / _safe_id(repo_id), compiler, log=lambda m: log(f'[{repo_id}] {m}'))
        return repo_id, source, result
    with ThreadPoolExecutor(max_workers=workers or min(4, max(1, len(repositories)))) as pool:
        futures = [pool.submit(one, item) for item in repositories.items()]
        for future in as_completed(futures):
            repo_id = 'unknown'
            try:
                repo_id, source, result = future.result()
                _stage_dir(source, result, output, _safe_id(repo_id))
                reports[repo_id] = {'status': 'built', 'source': str(source), 'result': {k: str(v) for k, v in result.items() if k != 'layout'}}
            except Exception as exc:
                reports[repo_id] = {'status': 'failed', 'error': f'{type(exc).__name__}: {exc}'}
                log(f'[{repo_id}] failed; continuing: {exc}')
    boot = output / 'boot-images' / 'spitfire' / 'first_stage.bin'
    boot.parent.mkdir(parents=True, exist_ok=True)
    boot_source = Path(__file__).resolve().parents[2] / 'boot' / 'bios' / 'first_stage.asm'
    build_spit_fire(boot_source, boot, log=log)
    staging = output / 'staging'
    staging.mkdir(parents=True, exist_ok=True)
    for name in ('src', 'executables', 'libraries', 'boot-images'):
        src = output / name
        if src.exists():
            dst = staging / ('src' if name == 'src' else {'executables':'bin','libraries':'lib','boot-images':'boot-images'}[name])
            if dst.exists(): shutil.rmtree(dst)
            shutil.copytree(src, dst)
    (staging / 'boot' / 'bios').mkdir(parents=True, exist_ok=True)
    shutil.copy2(boot, staging / 'boot' / 'bios' / 'first_stage.bin')
    (staging / 'metadata').mkdir(parents=True, exist_ok=True)
    manifest = staging / 'metadata' / 'workspace-manifest.json'
    manifest.write_text(json.dumps({'repositories': repositories, 'reports': reports, 'boot': str(boot), 'policy': 'build-and-stage compatible artifacts; preserve failures and provenance'}, indent=2), encoding='utf-8')
    iso = output / 'iso' / 'Chimera-II-Workspace.iso'
    create_iso(staging, iso, label='CHIMERA_II', profile='bios-only')
    img = output / 'img' / 'Chimera-II-Workspace.img'
    img.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(iso, img)
    return {'output': str(output), 'iso': str(iso), 'img': str(img), 'boot': str(boot), 'manifest': str(manifest), 'reports': reports}
