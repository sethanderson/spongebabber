from datetime import datetime
from app import app, db, spongebobify, limiter, oauth
from app.models import LogRequest, User
from flask import jsonify, render_template, redirect, url_for, json, request, session
from config import Config

# Database helpers
def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        return instance

def get_user_rate_limit():
    if(session['id'] is None):
        return "10/day"
    else:
        return User.query.filter_by(id=session['id']).first().requests_per_day

def get_number_of_requests_today(user_id = None):
    if(user_id is None):
        return 10
    else:
        todays_datetime = datetime(datetime.today().year, datetime.today().month, datetime.today().day)
        number_of_requests = User.query.filter_by(id=user_id).first().requests_per_day
        number_of_requests_today = LogRequest.query.filter(LogRequest.timestamp >= todays_datetime).filter_by(user_id=user_id).count()
        return number_of_requests - number_of_requests_today

# Routes
@app.route("/")
def home():
    print(session)
    return render_template("home.html")


@app.route("/recent")
def recent():
    sponges = LogRequest.query.order_by(LogRequest.timestamp.desc())
    return render_template("recent.html", title="Recent Sponges", sponges=sponges)


@app.route("/api/recent")
@app.route("/api/recent/<int:page>")
def api_recent(page=None):
    if page is None:
        page = 10
    sponges = LogRequest.query.order_by(LogRequest.timestamp.desc()).limit(page)
    return jsonify(sponges=LogRequest.serialize_list(sponges))


@app.route("/spongebobify/", methods=["POST"])
@app.route("/spongebobify/<textToSponge>", methods=["GET", "POST"])
@limiter.limit(get_user_rate_limit)
def spongebobify_there(textToSponge=None):
    content_type = request.headers.get("Content-Type")
    if content_type == "application/json":
        # Initialize image settings
        imageOverride = "https://i.imgur.com/XbXj7M4.jpg"
        textXPos = 28
        textYPos = 280
        targetWidthRatio = 0.6
        spongeTheText = True

        # Load json data
        data = json.loads(request.data)
        textToSponge = data["textToSponge"]

        if data["imageOverride"]:
            imageOverride = data["imageOverride"]
        if data["textXPos"]:
            textXPos = int(data["textXPos"])
        if data["textYPos"]:
            textYPos = int(data["textYPos"])
        if data["targetWidthRatio"]:
            targetWidthRatio = float(data["targetWidthRatio"])
        if data["spongeTheText"]:
            spongeTheText = True
        else:
            spongeTheText = False

        #Create the image to return
        encoded_image = spongebobify.create_image(
            textToSponge,
            "https://github.com/matthurtado/spongebabber/blob/main/app/static/impact.ttf?raw=true",
            imageOverride,
            textXPos,
            textYPos,
            targetWidthRatio,
            spongeTheText,
        )
        if spongeTheText:
            textToSponge = spongebobify.spongebobify(textToSponge)
        log_request = LogRequest(
            text=textToSponge,
            text_x_pos=textXPos,
            text_y_pos=textYPos,
            target_width_ratio=targetWidthRatio,
            sponge_the_text=spongeTheText,
            ip_address=request.remote_addr,
            timestamp=datetime.now(),
            user_id=session.get('id') or None
        )
        db.session.add(log_request)
        db.session.commit()
        return encoded_image.decode("utf-8")
    else:
        return "Content-Type not supported!"

@app.route('/google/')
def google():
    GOOGLE_CLIENT_ID = Config.GOOGLE_CLIENT_ID
    GOOGLE_CLIENT_SECRET = Config.GOOGLE_CLIENT_SECRET

    CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url=CONF_URL,
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

    # Redirect to google_auth function
    redirect_uri = url_for('google_auth', _external=True)
    print(redirect_uri)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/google/auth/')
def google_auth():
    token = oauth.google.authorize_access_token()
    user = token.get('userinfo')
    if user:
        session['user'] = user
        
        user_db = get_or_create(db.session, User, email=user['email'])
        if(user_db.last_login is None):
            user_db.email = user['email']
            user_db.name = user['name']
            user_db.last_login = datetime.now()
            user_db.num_of_requests = 50
            db.session.commit()
        else:
            user_db.last_login = datetime.now()
            db.session.commit()
        session['is_admin'] = user_db.is_admin or False
        session['id'] = user_db.id
        session['requests_per_day'] = user_db.requests_per_day
    return redirect('/')

@app.route('/logout/')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/account/')
def account():
    if 'user' in session:
        user = session['user']
        session['remaining_requests_per_day'] = get_number_of_requests_today(session['id'])
        return render_template('account.html', user=user)
    else:
        return redirect('/')