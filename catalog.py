from flask import Flask, render_template, request, redirect, jsonify, url_for
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Sport, SportItem, User
engine = create_engine('sqlite:///sportsitems.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

#NEW IMPORTS FOR AUTH
from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Sports Items Application"
LOGIN = """
<a class="navbar-text navbar-right" href="/login"><button class="btn btn-default-navbar-btn">Login</button></a>
"""
LOGOUT = """
<a class="navbar-text navbar-right" href="/gdisconnect"><button class="btn btn-default-navbar-btn">Logout</button></a>
"""
ADDITEM = """
<a href="/add">Add Item</a>
"""
EDITDELETE = """
<p><a href="/%s/edit">Edit </a>|<a href="/%s/delete"> Delete</a></p>
"""


@app.route('/')
@app.route('/catalog')
def home_page():
    sports = session.query(Sport).all()
    items = session.query(SportItem).all()
    if 'username' in login_session:
        return render_template('catalog.html', addItem=ADDITEM, login=LOGOUT, categories=sports, items=items)
    else:
        return render_template('catalog.html', login=LOGIN, categories=sports, items=items)


@app.route('/catalog/<string:cat>/items')
def items(cat):
    sports = session.query(Sport).all()
    sport = session.query(Sport).filter_by(name=cat).one()
    items = session.query(SportItem).filter_by(sport=sport)
    if 'username' in login_session:
        return render_template('sport.html', login=LOGOUT, categories=sports, sport=sport.name, items=items)
    else:
        return render_template('sport.html', login=LOGIN, categories=sports, sport=sport.name, items=items)


@app.route('/catalog/<string:cat>/<string:item>')
def item(cat, item):
    directory = "catalog/%s/%s" % (cat, item)
    link = EDITDELETE % (directory, directory)
    sport = session.query(Sport).filter_by(name=cat).one()
    sport_item = session.query(SportItem).filter_by(sport=sport, name=item).one()

    if 'username' in login_session:
        return render_template('item.html', edit=link, login=LOGOUT, name=sport.name, item=sport_item)
    else:
        return render_template('item.html', login=LOGIN, name=sport.name, item=sport_item)


@app.route('/login')
def showLogin():
    state = "".join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    #Checks to see if login originated from our site
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    #Obtain authorization code
    code = request.data

    try:
        #Try to get credentials from oauth
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = ' application/json'
        return response

    # Check with google that the access token is correct.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    #Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    userID = getUserID(login_session['email'])
    if not userID:
        userID = createUser(login_session)
    login_session['user_id'] = userID

    print "done!"
    response = make_response(json.dumps('Welcome %s' % login_session['username']), 200)
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/gdisconnect')
def gdisconnect():
    #Only disconnect a connected user.
    credentials = login_session['credentials']

    if credentials is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
         #Reset the user's sesson
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        # For whatever reason, the given token was invalid.
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/catalog/<string:cat>/<string:item>/edit', methods=['GET', 'POST'])
def edit_item(cat, item):
    if 'username' in login_session:
        sport = session.query(Sport).filter_by(name=cat).one()
        sport_item = session.query(SportItem).filter_by(sport=sport, name=item).one()
        if request.method == 'POST':
            sport_item.name = request.form['name']
            sport_item.description = request.form['description']
            return redirect(url_for('home_page'))
        else:
            return render_template('edit.html', item=sport_item)
    else:
        return redirect(url_for('showLogin'))


@app.route('/catalog/<string:cat>/<string:item>/delete', methods=['GET', 'POST'])
def delete_item(cat, item):
    if 'username' in login_session:
        if request.method == 'POST':
            sport = session.query(Sport).filter_by(name=cat).one()
            sport_item = session.query(SportItem).filter_by(sport=sport, name=item).one()
            session.delete(sport_item)
            session.commit()
            return redirect(url_for('home_page'))
        else:
            return render_template('delete.html', item=item)
    else:
        return redirect(url_for('showLogin'))


@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if 'username' in login_session:
        sports = session.query(Sport).all()
        if request.method == 'POST':
            cat = request.form['sport']
            sport = session.query(Sport).filter_by(name=cat).one()
            sports_item = SportItem(sport=sport,
                                    name=request.form['name'],
                                    sport_id=sport.id,
                                    description=request.form['description'])

            session.add(sports_item)
            session.commit()
            return redirect(url_for('home_page'))
        else:
            return render_template('add.html', sports=sports)
    else:
        return redirect(url_for('showLogin'))


@app.route('/catalog.json')
def catalog_json():
    sportsitems = session.query(SportItem).all()
    return jsonify(items=[item.serialize for item in sportsitems])


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):

    newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


if __name__ == '__main__':
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
