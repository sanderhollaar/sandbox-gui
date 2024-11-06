#!/usr/bin/env python
import json

with open('tests/tests.json') as data:
    tests = json.load(data)

for k, v in tests.items():
    credential = v['credential']
    with open(f'tests/{credential}') as data:
        cred = json.load(data)
        v['credential'] = cred

with open('config.json') as data:
    config = json.load(data)
