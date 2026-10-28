#!/usr/bin/env python3
"""Read-only, pinned-source mounting inventory. Never certifies or writes calibration."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def git_blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def source_file(root, relative):
    if Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise ValueError('Unsafe source path')
    path = (Path(root)/relative).resolve()
    try:
        path.relative_to(Path(root).resolve())
    except ValueError:
        raise ValueError('Source leaves checkout')
    return path


def inspect_sources(roots, commits, expected_blobs, inventory, identity_method='git_checkout'):
    """expected_blobs maps (repository, path) to a Git blob id from the pinned tree."""
    report = dict(schema=1, scope='source identity and change-point locations only',
        identity_method=identity_method, commits=commits, calibration_known=False,
        ros_runtime_tested=False, hardware_tested=False, upstream_patches_applied=False,
        files=[], changes=[], errors=[])
    cache = {}
    for change in inventory['changes']:
        row = dict(id=change['id'], scope=change['scope'], title=change['title'],
            implementation_status=change['implementation_status'], locations=[])
        for location in change['sources']:
            repo, relative = location['repository'], location['path']
            key = (repo, relative)
            if key not in cache:
                try:
                    path = source_file(roots[repo], relative)
                    data = path.read_bytes()
                    expected = expected_blobs.get(key)
                    verified = expected is not None and git_blob(data) == expected
                    if repo != 'bundle' and not verified:
                        raise ValueError('File differs from pinned Git tree: '+repo+'/'+relative)
                    cache[key] = data.decode('utf-8').splitlines()
                    report['files'].append(dict(repository=repo, path=relative,
                        sha256=hashlib.sha256(data).hexdigest(), git_blob_sha1=git_blob(data),
                        pinned_blob_verified=verified if repo != 'bundle' else None))
                except (OSError, ValueError, KeyError) as exc:
                    cache[key] = []
                    report['errors'].append(dict(id=change['id'], reason=str(exc)))
            lines = [i for i, text in enumerate(cache[key], 1) if location['anchor'] in text]
            if not lines:
                report['errors'].append(dict(id=change['id'], reason='Source anchor missing: '+repo+'/'+relative))
            row['locations'].append(dict(repository=repo, path=relative, lines=lines))
        row['source_located'] = all(x['lines'] for x in row['locations'])
        report['changes'].append(row)
    report['source_audit_passed'] = not report['errors']
    report['note'] = ('Located anchors and original file hashes are not proof that a patch, '
                      'ROS build, sensor measurement or robot task has passed.')
    return report


def checkout_identities(roots, inventory, pins):
    commits, blobs = {}, {}
    for repo in ('scan', 'lio', 'livox_driver'):
        head = subprocess.check_output(['git', '-C', str(roots[repo]), 'rev-parse', 'HEAD'], text=True).strip()
        if head != pins[repo]:
            raise ValueError('Checkout version differs from locks/sources.json: '+repo)
        commits[repo] = head
    for change in inventory['changes']:
        for location in change['sources']:
            repo, relative = location['repository'], location['path']
            source_file(roots[repo], relative)
            if repo != 'bundle':
                blobs[(repo, relative)] = subprocess.check_output(
                    ['git', '-C', str(roots[repo]), 'rev-parse', commits[repo]+':'+relative], text=True).strip()
    return commits, blobs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('scan', 'lio', 'livox-driver'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT/'generated/mounting-source-audit.json')
    args = parser.parse_args()
    roots = dict(scan=args.scan, lio=args.lio, livox_driver=args.livox_driver, bundle=ROOT)
    inventory = json.loads((ROOT/'configs/mounting-change-checklist.json').read_text(encoding='utf-8'))
    lock = json.loads((ROOT/'locks/sources.json').read_text(encoding='utf-8'))
    pins = {entry['name']: entry['commit'] for entry in lock['repositories']}
    commits, blobs = checkout_identities(roots, inventory, pins)
    report = inspect_sources(roots, commits, blobs, inventory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Source audit:', 'passed' if report['source_audit_passed'] else 'FAILED',
          '| change points:', len(report['changes']), '| report:', args.output)
    raise SystemExit(0 if report['source_audit_passed'] else 1)


if __name__ == '__main__':
    main()
