#!/usr/bin/env python3
"""Chat quality eval: asks known questions about indexed documents and
checks that expected keywords appear in the answers.

    python eval_chat.py [--api http://localhost:8000]

Add cases below; documents are matched by doc_name substring.
"""
import argparse
import json
import time
import urllib.request

CASES = [
    # (doc_name substring, question, [expected keywords, all must appear])
    ('cagpi', "Quel est le contexte de la mission ?", ['CA-GIP']),
    ('cagpi', "Quels sont les livrables attendus ?", ['Ansible', 'GitLab']),
    ('cagpi', "Quelle est la durée de la mission ?", ['2026']),
    ('cagpi', "Quelles bases de données sont concernées ?", ['Oracle', 'PostgreSQL']),
    ('cagpi', "Quels sont les projets à réaliser ?", ['Healthcheck', 'Kubernetes']),
    ('cagpi', "Quelles compétences techniques sont attendues ?", ['Ansible']),
    ('mission-test', "Quel est le budget de la mission ?", ['15']),
    ('mission-test', "Quelle est l'architecture Vault prévue ?", ['replicas']),
]


def call(api, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(api + path, data=data,
                                 headers={'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=600))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--api', default='http://localhost:8000')
    args = parser.parse_args()

    docs = call(args.api, '/api/documents')
    by_name = {}
    for d in docs:
        by_name[d['doc_name']] = d['doc_id']

    passed = 0
    for doc_sub, question, keywords in CASES:
        doc_id = next((v for k, v in by_name.items() if doc_sub in k), None)
        if not doc_id:
            print(f'SKIP  [{doc_sub}] not indexed — {question}')
            continue
        t0 = time.time()
        try:
            r = call(args.api, '/api/chat',
                     {'doc_id': doc_id, 'question': question})
            answer = r.get('answer', '')
            sources = [s['title'] for s in r.get('sources', [])]
        except Exception as e:
            answer, sources = f'<error: {e}>', []
        dt = time.time() - t0
        missing = [k for k in keywords if k.lower() not in answer.lower()]
        ok = not missing
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  [{doc_sub}] {question} ({dt:.0f}s)")
        print(f"      sources: {sources}")
        if not ok:
            print(f"      missing {missing} in: {answer[:200]!r}")
    print(f"\n{passed}/{len(CASES)} passed")


if __name__ == '__main__':
    main()
