#!/usr/bin/env python
import json
import urllib.request

from flask import Blueprint, session

from api import tests, config
from lib import utils

api = Blueprint("api", __name__, url_prefix="/api")


@api.route("/get_test")
def api_get():
    form = session.get('form')
    test_id = form.get('test_id')
    test = tests[test_id]

    message = {
        "status": "success",
        "test": test,
    }

    return json.dumps(message)


@api.route("/pre_authorized_code")
def api_pre_authorized_code():
    form = session.get('form')
    test_id = form.get('test_id')
    test = tests[test_id]

    pre_authorized_code = utils.randid()
    data = {
        'credentials': [test['credential']['type']],
        'grants': {
            'urn:ietf:params:oauth:grant-type:pre-authorized_code': {
                'pre-authorized_code': pre_authorized_code,
            },
        },
        'credentialDataSupplierInput': test['credential']['claims'],
    }

    if test['options'].get('tx_code', None):
        data['grants']['urn:ietf:params:oauth:grant-type:pre-authorized_code']['tx_code'] = True

    json_data = json.dumps(data).encode("utf-8")

    create_url = config['issuer'] + "/create-offer"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['issuer_token']}"
    }

    req = urllib.request.Request(create_url, json_data, headers)
    with urllib.request.urlopen(req) as f:
        res = json.loads(f.read().decode())

    # print(res)

    qr_uri = res['uri']
    pin = res.get('txCode')

    message = {
        "status": "success",
        # "test_id": test_id,
        "test": test,
        "qr_uri": qr_uri,
        "pin": pin,
        # "pac": pre_authorized_code,
        "data": data
    }

    session['revoke'] = test['options'].get('revoke', False)
    session['pac'] = pre_authorized_code

    return json.dumps(message)


@api.route("/pac_status")
def pac_status():
    pac = session.get('pac')
    revoke = session.get('revoke')

    # print(revoke)

    data = {
        'id': pac
    }

    json_data = json.dumps(data).encode("utf-8")

    check_url = config['issuer'] + "/check-offer"

    headers = {
        "Content-Type": "application/json",
    }

    req = urllib.request.Request(check_url, json_data, headers)
    with urllib.request.urlopen(req) as f:
        res = json.loads(f.read().decode())

    # print(res)

    status = res['status']

    if status == 'CREDENTIAL_ISSUED' and revoke:
        uuid = res['uuid']
        data = {
            "uuid": uuid,
            "state": 'revoke'
            # list: <optional URI of a specific statuslist for which to set/unset the status>
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['issuer_token']}"
        }

        json_data = json.dumps(data).encode("utf-8")

        revoke_url = config['issuer'] + "/revoke-credential"

        req = urllib.request.Request(revoke_url, json_data, headers)
        with urllib.request.urlopen(req) as f:
            res = json.loads(f.read().decode())

        # print(res)

        status = res['state']

    return json.dumps(status)


@api.route("/verifier")
def verifier():
    form = session.get('form')
    test_id = form['test_id']

    test = tests[test_id]
    name = test['credential']['type']

    data = {}
    json_data = json.dumps(data).encode("utf-8")

    create_url = config['verifier'] + "/create-offer/" + name

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['verifier_token']}"
    }

    req = urllib.request.Request(create_url, json_data, headers)
    with urllib.request.urlopen(req) as f:
        res = json.loads(f.read().decode())

    # print(res)

    qr_uri = res['requestUri']
    check_uri = res['checkUri']
    code = check_uri.split("/")[-1]

    message = {
        "status": "success",
        # "test_id": test_id,
        "test": test,
        "qr_uri": qr_uri,
        # "code": code
    }

    session['code'] = code

    return json.dumps(message)


@api.route("/verifier_status")
def verifier_status():
    code = session.get('code')

    check_url = config['verifier'] + f'/check-offer/{code}'

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['verifier_token']}"
    }

    req = urllib.request.Request(check_url, None, headers)
    with urllib.request.urlopen(req) as f:
        res = json.loads(f.read().decode())

    # print(res)

    status = res['status']
    result = res.get('result')

    message = {
        "status": status,
        "result": result
    }

    return json.dumps(message)
