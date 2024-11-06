#!/usr/bin/env python
import os
from flask import Flask, render_template, session, request, send_from_directory

from api.api import api, tests

app = Flask(__name__)
app.secret_key = b'secret'
app.register_blueprint(api)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'wallet.ico', mimetype='image/vnd.microsoft.icon'
    )


@app.route("/")
def landing():
    return render_template("landing.j2", tests=tests)


@app.route("/test", methods=['POST'])
def test():
    form = request.form
    session['form'] = form
    test_id = form.get('test_id')
    pin = form.get('pin', 'Off')
    args = {
        'test_id': test_id,
        'pin': pin
    }

    return render_template("test.j2", **args)


if __name__ == "__main__":
    app.run()
