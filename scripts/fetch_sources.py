#!/usr/bin/env python3
"""Fetch exact source commits; never reset an existing checkout or dirty files."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--with-rob2nav', action='store_true')
    p.add_argument('--with-unitree-sdk', action='store_true')
    args = p.parse_args()
    lock = json.loads((ROOT/'locks/sources.json').read_text())
    selected = [r for r in lock['repositories'] if r['default'] or
                (args.with_rob2nav and r['name']=='rob2nav') or
                (args.with_unitree_sdk and r['name']=='unitree_sdk2_python')]
    sources = ROOT/'sources'; sources.mkdir(exist_ok=True)
    for repo in selected:
        dest = sources/repo['name']
        if dest.exists():
            if not (dest/'.git').exists():
                raise RuntimeError('Existing non-git directory: '+str(dest))
            if git(dest, 'rev-parse', 'HEAD') != repo['commit']:
                raise RuntimeError('Existing checkout differs; inspect manually: '+str(dest))
            if git(dest, 'status', '--porcelain'):
                raise RuntimeError('Checkout modified; inspect generated config or local work: '+str(dest))
            print('Verified existing', repo['name'], repo['commit']); continue
        subprocess.run(['git', 'clone', '--filter=blob:none', '--no-checkout', repo['url'], str(dest)],check=True)
        if repo.get('sparse_directories'):
            subprocess.run(['git','-C',str(dest),'sparse-checkout','set','--cone',*repo['sparse_directories']],check=True)
        subprocess.run(['git','-C',str(dest),'checkout','--detach',repo['commit']],check=True)
        subprocess.run(['git','-C',str(dest),'submodule','update','--init','--recursive'],check=True)
        if git(dest,'rev-parse','HEAD') != repo['commit']: raise RuntimeError('Pin mismatch')
    if args.with_rob2nav:
        model = sources/'rob2nav'/lock['model']['path']
        actual = hashlib.sha256(model.read_bytes()).hexdigest()
        if actual != lock['model']['sha256']:
            raise RuntimeError('MoE SHA256 mismatch (also check Git LFS pointers): '+str(model))
        print('Verified MoE SHA256',actual)


if __name__=='__main__': main()
