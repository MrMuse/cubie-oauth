from flask import Flask, redirect, url_for, session, request, jsonify, abort
from flask_oauthlib.client import OAuth

import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'
# DEBUG=1 python oauth2_client.py



def create_client(application):
    oauth = OAuth(application)

    remote = oauth.remote_app(
        'dev',
        consumer_key='dev',
        consumer_secret='dev',
        request_token_params={'scope': 'email'},
        base_url='https://server-cubie.herokuapp.com/api/',
        request_token_url=None,
        access_token_method='POST',
        access_token_url='https://server-cubie.herokuapp.com/oauth/token',
        authorize_url='https://server-cubie.herokuapp.com/oauth/authorize'
    )

    @application.route('/')
    def index():
        if 'dev_token' in session:
            ret = remote.get('email')
            return jsonify(ret.data)
        return redirect(url_for('login'))

    @application.route('/login')
    def login():
        return remote.authorize(callback=url_for('authorized', _external=True))

    @application.route('/logout')
    def logout():
        session.pop('dev_token', None)
        return redirect(url_for('index'))

    @application.route('/authorized')
    def authorized():
        resp = remote.authorized_response()
        if resp is None:
            return 'Access denied: error=%s' % (
                request.args['error']
            )
        if isinstance(resp, dict) and 'access_token' in resp:
            session['dev_token'] = (resp['access_token'], '')
            return jsonify(resp)
        return str(resp)

    @application.route('/client')
    def client_method():
        ret = remote.get("client")
        if ret.status not in (200, 201):
            return abort(ret.status)
        return ret.raw_data

    @application.route('/address')
    def address():
        ret = remote.get('address/hangzhou')
        if ret.status not in (200, 201):
            return ret.raw_data, ret.status
        return ret.raw_data

    @application.route('/method/<name>')
    def method(name):
        func = getattr(remote, name)
        ret = func('method')
        return ret.raw_data

    @remote.tokengetter
    def get_oauth_token():
        return session.get('dev_token')

    return remote


if __name__ == '__main__':
    application = Flask("cubie-oauth-client")
    application.debug = False
    application.secret_key = 'production'
    create_client(application)
    application.run()
