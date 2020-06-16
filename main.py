'''
Title: Final Project for CS493
Author: Taekyoung Kim
CS493-2020Spring
'''

from google.cloud import datastore
from flask import Flask, request, render_template, abort
from requests_oauthlib import OAuth2Session
import json
from google.oauth2 import id_token
from google.auth import crypt
from google.auth import jwt
from google.auth.transport import requests
import constants
import shelf
import product

import os 
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.register_blueprint(shelf.bp)
app.register_blueprint(product.bp)
client = datastore.Client()

# These should be copied from an OAuth2 Credential section at
# https://console.cloud.google.com/apis/credentials
client_id = "572611850973-tfrgfbf0k74j7tkprtffut7fsk4tpv9i.apps.googleusercontent.com"
client_secret = "wqnOY2WRwSHrPklqLvzm3hH3"

# This is the page that you will use to decode and collect the info from
# the Google authentication flow
#redirect_uri = 'http://127.0.0.1:8080/oauth'
redirect_uri = 'https://final-cs493-kimtaeky.wl.r.appspot.com/oauth'

# These let us get basic info to identify a user and not much else
# they are part of the Google People API
scope = ['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile', 'openid']
oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)

@app.errorhandler(405)
def method_not_allowed(e):
    return ({"Error":"Method not recognized"}, 405)

@app.route('/')
def index():
    authorization_url, state = oauth.authorization_url('https://accounts.google.com/o/oauth2/auth', access_type="offline", prompt="select_account")
    return render_template('home.html', authorization_url = authorization_url)
    #return "Please navigate to /shelves and products to use this API for Final Project!"

@app.route('/oauth')
def oauthroute():
    token = oauth.fetch_token(
        'https://accounts.google.com/o/oauth2/token',
        authorization_response=request.url,
        client_secret=client_secret)
    req = requests.Request()

    id_info = id_token.verify_oauth2_token( 
    token['id_token'], req, client_id)
    token_id = token['id_token']
    u_id = id_info['sub']
    #return "Your JWT is: %s" % token['id_token']
    #store user info in the entity of user!
    que = client.query(kind=constants.user).add_filter('user_id', '=', id_info["sub"])
    res = list(que.fetch())
    msg = "You are already in the user data! Here is your new token which has a new expiration date."
    if not res:
        new_user = datastore.entity.Entity(key=client.key(constants.user))
        #new_user.update({"user_id": id_info["sub"], "email": id_info["email"], "expiration": id_info["exp"]})
        new_user.update({"user_id": id_info["sub"], "email": id_info["email"], "iss": id_info["iss"]})
        client.put(new_user)
        msg ="Now You just successfully added to the user data! Here is a Token."
    '''
    else:
        for e in res:
            e['expiration'] = id_info["exp"]
            client.put(e)
        msg = "You are already in the user data! Here is your new token which has a new expiration date."
    '''
    return render_template('display.html', msg = msg, token_id=token_id, u_id=u_id)


# JWT matches the email associated to the resource being accessed.
# http://127.0.0.1:8080/verify-jwt?jwt=YourToken_JWT
@app.route('/verify-jwt')
def verify():
    req = requests.Request()

    id_info = id_token.verify_oauth2_token( 
    request.args['jwt'], req, client_id)

    return repr(id_info) + "<br><br> the user is: " + id_info['email']

@app.route('/users', methods=['GET'])
def get_users():
    if request.method == 'GET':
        query = client.query(kind=constants.user)
        results = list(query.fetch())
        for e in results:
            e["id"] = e.key.id
            e["self"] = request.url+"/"+str(e["id"])

        accept_handle = str(request.accept_mimetypes)
        if not accept_handle:
            return ({"Error": "Not Acceptable."}, 406)

        if accept_handle == "application/json":
            return (json.dumps(results, sort_keys = True, indent=4), 200)
        else:
            return ({"Error": "Not Acceptable."}, 406)
    else:
        abort(405)
'''
 Below is not required for the final project, but I want to add this.
'''   
@app.route('/users/<user_id>/products', methods=['GET'])
def get_boats(user_id):
    auth_header = request.headers.get('Authorization')
    owner_sub=''

    if auth_header:
        auth_token = auth_header.split(" ")[1]
    else:
        auth_token =''     
    try:
        req = requests.Request()
        id_info = id_token.verify_oauth2_token(auth_token, req, client_id)
        owner_sub = id_info['sub']
    except:
        return ({"Error":"Missing or Invalid JWT"}, 401)
    
    accept_handle = str(request.accept_mimetypes)
    if not accept_handle:
        return ({"Error": "Not Acceptable."}, 406)

    if request.method == 'GET':

        que = client.query(kind=constants.product).add_filter('owner', '=', owner_sub)
        res = list(que.fetch())
        boat_list = []
        if accept_handle == "application/json":
            if res:
                for e in res:
                    e["id"] = e.key.id
                    boat_list.append(e)
                return (json.dumps(boat_list, indent=4, sort_keys=True), 200)
            else:
                return (json.dumps([]), 200)
        else:
                return ({"Error": "Not Acceptable."}, 406)

    else:
        abort(405)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)