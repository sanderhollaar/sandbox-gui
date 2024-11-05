#!/usr/bin/env python
import os
import json
import random
import urllib.request
from flask import Flask, render_template, session, request, send_from_directory


ISSUER = 'https://agent.dev.eduwallet.nl/sandbox/api'
ISSUER_TOKEN = 'bfOPbpdLHKLpY7GImgvnqp5mcV2jQrpF'
VERIFIER = 'https://verifier.dev.eduwallet.nl/sandbox/api'
VERIFIER_TOKEN = 'SE59wNFgsie3SiQ0DaGVp9JNI6Tp8SHL'


def randid():
    allowed_chars = 'abcdefghijklmnoprstuvwxyz1234567890'
    length = 16
    return ''.join([random.choice(allowed_chars) for n in range(length)])


app = Flask(__name__)
app.secret_key = b'secret'


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon'
    )


@app.route("/")
def landing():
    return render_template("landing.j2", tests=tests)


@app.route("/test", methods=['POST'])
def test():
    form = request.form
    session['form'] = form
    test_id = form.get('test_id')
    pin = form.get('pin')
    args = {
        'test_id': test_id,
        'pin': pin
    }

    return render_template("test.j2", **args)


@app.route("/api/get_test")
def api_get():
    form = session.get('form')
    test_id = form.get('test_id')
    test = tests[test_id]

    message = {
        "status": "success",
        # "test_id": test_id,
        "test": test,
    }

    return json.dumps(message)


@app.route("/api/pre_authorized_code")
def api_pre_authorized_code():
    form = session.get('form')
    test_id = form.get('test_id')
    test = tests[test_id]

    pre_authorized_code = randid()
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

    create_url = ISSUER + "/create-offer"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ISSUER_TOKEN}"
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


@app.route("/api/pac_status")
def pac_status():
    pac = session.get('pac')
    revoke = session.get('revoke')

    # print(revoke)

    data = {
        'id': pac
    }

    json_data = json.dumps(data).encode("utf-8")

    check_url = ISSUER + "/check-offer"

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
            "Authorization": f"Bearer {ISSUER_TOKEN}"
        }

        json_data = json.dumps(data).encode("utf-8")

        revoke_url = ISSUER + "/revoke-credential"

        req = urllib.request.Request(revoke_url, json_data, headers)
        with urllib.request.urlopen(req) as f:
            res = json.loads(f.read().decode())

        # print(res)

        status = res['state']

    return json.dumps(status)


@app.route("/api/verifier")
def verifier():
    form = session.get('form')
    test_id = form['test_id']

    test = tests[test_id]
    name = test['credential']['type']

    data = {}
    json_data = json.dumps(data).encode("utf-8")

    create_url = VERIFIER + "/create-offer/" + name

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VERIFIER_TOKEN}"
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


@app.route("/api/verifier_status")
def verifier_status():
    code = session.get('code')

    check_url = VERIFIER + f'/check-offer/{code}'

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VERIFIER_TOKEN}"
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


with open('tests.json') as data:
    tests = json.load(data)


if __name__ == "__main__":
    app.run()
