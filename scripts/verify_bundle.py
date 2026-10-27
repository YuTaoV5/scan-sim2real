#!/usr/bin/env python3
"""Offline completeness, link, syntax and accidental-secret checks."""
import ast
import json
from pathlib import Path
import re
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[1]


def main():
    required=['README.md','AGENTS.md','LICENSE','THIRD_PARTY_NOTICES.md','locks/sources.json',
              'evidence/validation.json','evidence/source-access.json','configs/calibration.template.json','configs/mission.template.yaml',
              'configs/calibration.rviz','docker/Dockerfile','.github/workflows/offline-checks.yml']
    required += ['docs/'+n for n in ['00-handoff.md','01-new-server.md','02-calibration.md',
                  '03-bag-pcd.md','04-lio-scan.md','05-moe.md','06-missions.md','07-sources.md','08-troubleshooting.md']]
    for path in required:
        if not (ROOT/path).is_file():raise ValueError('Missing '+path)
    lock=json.loads((ROOT/'locks/sources.json').read_text())
    for repo in lock['repositories']:
        if not re.fullmatch('[0-9a-f]{40}',repo['commit']):raise ValueError('Unpinned source '+repo['name'])
        if not repo['url'].startswith('https://github.com/'):raise ValueError('Unexpected source URL')
    if not re.fullmatch('[0-9a-f]{64}',lock['model']['sha256']):raise ValueError('Invalid model digest')
    access=json.loads((ROOT/'evidence/source-access.json').read_text())
    public={r['name']:r for r in access['repositories']}
    for repo in lock['repositories']:
        if public[repo['name']]['status']!='verified' or public[repo['name']]['commit']!=repo['commit']:
            raise ValueError('Public source identity unverified: '+repo['name'])
    if access['model']['status']!='verified' or access['model']['sha256']!=lock['model']['sha256']:
        raise ValueError('Model identity unverified')
    c=json.loads((ROOT/'configs/calibration.template.json').read_text())
    if c['reviewed'] or c['T_base_lidar'] is not None or c['mounting_angle_deg'] is not None:
        raise ValueError('Template contains invented measured mounting')
    state=json.loads((ROOT/'evidence/validation.json').read_text())
    if state['real_data_available'] or state['hardware_tested'] or state['ros_runtime_tested']:
        raise ValueError('Update verifier when real evidence exists; current bundle has no runtime evidence')
    files=[p for folder in ['scripts','tests','docs','references','configs','locks','evidence']
           for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    files += [ROOT/n for n in ['README.md','AGENTS.md','LICENSE','THIRD_PARTY_NOTICES.md']]
    secret_patterns=[r'-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----',
                     r'\bgh[pousr]_[A-Za-z0-9]{30,}',r'\bgithub_pat_[A-Za-z0-9_]{30,}',
                     r'https://[^\s/@:]+:[^\s/@]+@']
    for p in files:
        if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
        if p.suffix not in ('.md','.py','.sh','.json','.yaml','.yml','.rviz','.log','.txt') and p.name!='LICENSE':continue
        text=p.read_text(encoding='utf-8')
        for pattern in secret_patterns:
            if re.search(pattern,text):raise ValueError('Possible secret in '+str(p.relative_to(ROOT)))
        if p.suffix=='.md':
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',text):
                if target.startswith(('#','http:','https:','mailto:')):continue
                target=unquote(target.split('#',1)[0])
                if not (p.parent/target).exists():raise ValueError('Broken local link in '+str(p)+': '+target)
    print('Bundle checks passed: required files, fixed commits, unknown calibration, Python syntax, local links, secret patterns.')


if __name__=='__main__':main()
