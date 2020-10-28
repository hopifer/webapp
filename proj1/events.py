from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash, _app_ctx_stack

app = Flask(__name__)
from models import db, User, Event
from datetime import datetime
from sqlalchemy import asc
from werkzeug.security import check_password_hash, generate_password_hash
# above is for password security
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config.from_object(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #here to silence deprecation warning
app.secret_key = 'development key'



db.init_app(app)
@app.cli.command('initdb')
def initdb_command(): #initializes the database
    db.drop_all()

    db.create_all() #creates based in models we picked above

@app.before_request #runs before any request 
def before_request():
	g.user = None #sets global value in application to none 
	#user is defined inside of g and it is reset each time 
	
	if 'id' in session: #how to procest from the requests
		#so if we do have a user that is loged in we will put it into the g.user
		g.user = User.query.filter_by(id=session['id']).first()

def signedin(username):
    ret = User.query.filter_by(username=username).first()
    return ret.id if ret else None



@app.route('/')
def home():
	  
	return render_template('homepage.html', events=Event.query.order_by(asc(Event.startdatetime)).all())
	


@app.route('/private')
def priv():
	#make seperate list of attending events, and remove the ones attending from the public ones! 

    attendevents = User.query.filter_by(id = session['id']).first().attending.order_by(asc(Event.startdatetime)).all()
   
    return render_template('homepage.html', events=Event.query.filter(Event.host != session['id']).order_by(asc(Event.startdatetime)).all(), myevents=Event.query.filter(Event.host == session['id']).order_by(asc(Event.startdatetime)).all(), attendingevents = attendevents)




@app.route('/register', methods = ['GET', 'POST'])
def signup():
    error = None
    if g.user:
        return redirect(url_for('home'))
    if request.method == 'POST':
        if not request.form['username']:
            error = 'Must enter a username.'
        elif not request.form['password']:
            error = 'Must enter a password.'
        elif signedin(request.form['username']) is not None:
	        error = 'Username is taken.'
        else:
            hashi = generate_password_hash(request.form['password'])
            co = User(request.form['username'], request.form['password'], hashi)
            db.session.add(co)
            db.session.commit()
            flash('You are signed up!')
            return redirect(url_for('login'))
    
    return render_template('register.html',error = error)
@app.route('/login', methods = ['GET', 'POST'])
def login():
   
    error = None
    if request.method == 'POST':
        user  = User.query.filter_by(username = request.form['username']).first()

        if user is None:
            error = 'No username associated'
        elif not check_password_hash(user.passhash, request.form['password']):
            error = 'Bad password'
        else:
            session['id'] = user.id
            return redirect(url_for('priv'))

    return render_template('login.html', error = error)
    



@app.route('/event', methods=['GET','POST'])
def addevent():
    error = None
    if request.method == 'POST':
        if not request.form['Title']:
            error = 'Must enter a title.'
        elif not request.form['start']:
            error = 'Must enter a start date/time.'
        elif signedin(request.form['end']) is not None:
	        error = 'Must enter an end date/time.'
        else:
            startt = datetime.strptime(request.form['start'], '%Y-%m-%dT%H:%M')
            endt = datetime.strptime(request.form['end'], '%Y-%m-%dT%H:%M')
            event = Event(request.form['Title'], request.form['description'], startt, endt, session['id'])
            db.session.add(event)
            
            db.session.commit()
            
            return redirect(url_for('priv'))

    
    return render_template('addevent.html',error = error)
@app.route('/<eventid>/attend')
def attend(eventid):
    event = Event.query.filter_by(id = eventid).first()
    User.query.filter_by(id=session['id']).first().attending.append(event)
    db.session.commit()
    return redirect(url_for('priv'))
    

@app.route('/delete', methods=['GET','POST'])
def deleteevent():
    error = None
    if request.method == 'POST':
        event = Event.query.filter(Event.title == request.form['Title']).first()
        events = Event.query.filter_by(host=session['id']).all()
        if events is None:
            error = 'You have no events'
        if not request.form['Title']:
            error = 'Must enter a title of event to delete'
            
        elif event is None:
            error = 'No event with that title'

        else:
            
            db.session.delete(event)
            db.session.commit()
            return redirect(url_for('priv'))

    
    return render_template('cancelevent.html',error = error)



@app.route('/logout')
def logout():
	session.pop('id', None)
	return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug = True)
