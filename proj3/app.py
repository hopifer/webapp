from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash, jsonify, make_response, request,  _app_ctx_stack
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import asc
from datetime import datetime
import json

app = Flask(__name__)
items = []


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config.from_object(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #here to silence deprecation warning
app.secret_key = 'development key'

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique = True)
    pw = db.Column(db.String(50),nullable = False)
    inside =  db.relationship('Chatroom', secondary='inside', lazy = 'dynamic' )
    def __init__(self, username, pw):
        self.username = username
        self.pw = pw

    def __repr__(self):
        return '<Person %r>' % self.username

inside = db.Table('inside',
    db.Column('userid', db.Integer, db.ForeignKey('user.id')),
    db.Column('chatid', db.Integer, db.ForeignKey('chatroom.id'))
#association table named follows
#joins is when we pull data out of SQL and put it together based on how it related to each other

)
class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(50))
    sender = db.Column(db.Integer, db.ForeignKey('user.username'))
    def __init__(self, text,sender):
        self.text = text
        self.sender = sender

    def __repr__(self):
        return self.text
sent = db.Table('sent',
    db.Column('messagesid', db.Integer, db.ForeignKey('messages.id')),
    db.Column('chatid', db.Integer, db.ForeignKey('chatroom.id'))
#association table named follows
#joins is when we pull data out of SQL and put it together based on how it related to each other

)
class Chatroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable = False)
    host = db.Column(db.Integer, db.ForeignKey('user.id'))
    sent = db.relationship('Messages', secondary='sent', lazy = 'dynamic' )
    def __init__(self, title, host):
        self.title = title
        self.host = host

    def __repr__(self):
        return '<Chatroom %r>' % self.title



db.init_app(app)
@app.cli.command('initdb')
def initdb_command(): #initializes the database
    db.drop_all()
    db.create_all()



@app.before_request #runs before any request 
def before_request():
	g.user = None #sets global value in application to none 
	#user is defined inside of g and it is reset each time 
	
	if 'id' in session: #how to procest from the requests
		#so if we do have a user that is loged in we will put it into the g.user
		g.user = User.query.filter_by(id=session['id']).first()
@app.route('/')
def home():
	  
	return render_template('homepage.html')
	

def signedin(username):
    ret = User.query.filter_by(username=username).first()
    return ret.id if ret else None



@app.route('/register', methods = ['GET', 'POST'])
def signup():
    error = None
    
    if request.method == 'POST':
        if not request.form['username']:
            error = 'Must enter a username.'
        elif not request.form['password']:
            error = 'Must enter a password.'
        elif signedin(request.form['username']) is not None:
            error = 'Must enter a unique username' # is in the user names
        else:
             
            co = User(request.form['username'], request.form['password'])
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
        elif user.pw != request.form['password']:
            error = 'Bad password'
        else:
            session['id'] = user.id
            return redirect(url_for('lobby'))

    return render_template('login.html', error = error)

@app.route('/lobby')
def lobby():
    if g.user is None:
        return render_template("homepage.html")
    return render_template('main.html', chatrooms = Chatroom.query.order_by(asc(Chatroom.id)).all(), hostrooms =Chatroom.query.filter(Chatroom.host == session['id']).order_by(asc(Chatroom.title)).all())



@app.route("/chat", methods=['GET','POST'])
def makechat():
    if g.user is None:
        return render_template("homepage.html")
    error = None
    if request.method == 'POST':
        if not request.form['Title']:
            error = 'Must enter a title.'
        else:
            chatroom = Chatroom(request.form['Title'],host = session['id'])
            #message = Messages("first!", "joe")
            db.session.add(chatroom)
            db.session.commit()
           # db.session.add(message)
            #Chatroom.query.filter_by(title=chatroom.title).first().sent.append(message)
            db.session.commit()
            
            #pass data usibg json to javascript anf set java interval an interval 
            return render_template('main.html', chatrooms = Chatroom.query.order_by(asc(Chatroom.id)).all(), hostrooms =Chatroom.query.filter(Chatroom.host == session['id']).order_by(asc(Chatroom.title)).all())

    
    return render_template('newchat.html',error = error)
				
@app.route("/chatty/<chatroomname>", methods=['GET','POST'])
def chatty(chatroomname):
  
    error = None
    chatt = getChatroom(chatroomname)
    if chatt is None:
        error = "This chat no longer exists."
        return render_template('main.html', chatrooms = Chatroom.query.order_by(asc(Chatroom.id)).all(), hostrooms =Chatroom.query.filter(Chatroom.host == session['id']).order_by(asc(Chatroom.title)).all())
    if request.method == 'POST':
        message = Messages(request.form['messagey'], g.user.username)
        db.session.add(message)
        Chatroom.query.filter_by(title=chatt.title).first().sent.append(message)
        db.session.commit() 
    messagers = Chatroom.query.filter_by(title=chatt.title).first().sent
    thislist = []
    for i in messagers:
        thislist.append(i.text)
    return json.dumps(thislist)
    
@app.route("/chatting/<chatroomname>", methods= ['GET','POST'])
def chatting(chatroomname):
    error = None
    chatt = getChatroom(chatroomname)
    if chatt is None:
        error = "This chat no longer exists."
    return render_template("chat.html", messengers = Chatroom.query.filter_by(title=chatt.title).first().sent,chatroommy = chatroomname, error = error)
def getChatroom(chatroomname):
    return Chatroom.query.filter_by(title=chatroomname).first()

@app.route("/updatechat/<chatroomname>", methods=["POST"])
def add(chatroomname):
    if request.method == 'POST':
        newMessage = Messages(request.form["two"] + ": " + request.form["one"], request.form["two"])
        db.session.add(newMessage)
        Chatroom.query.filter_by(title=chatroomname).first().sent.append(newMessage)
        
        db.session.commit() 
    return ""

    

@app.route("/guestbook")
def guestbook():
    return render_template("guestbook.html")
@app.route("/guestbook/create-entry", methods=["POST"])
def create_entry():

    req = request.get_json()

    print(req)

    res = make_response(jsonify({"message": "OK"}), 200)

    return res


@app.route('/logout')
def logout():
	session.pop('id', None)
	return redirect(url_for('home'))

@app.route('/delete/<chatroomname>')
def delete(chatroomname):

    
    todelete = Chatroom.query.filter(Chatroom.title == chatroomname).first()
    deletable = Chatroom.query.filter_by(host=session['id']).all()
    if todelete in deletable:
        db.session.delete(todelete)
        db.session.commit()
        return render_template('main.html', chatrooms = Chatroom.query.order_by(asc(Chatroom.id)).all(), hostrooms =Chatroom.query.filter(Chatroom.host == session['id']).order_by(asc(Chatroom.title)).all())

     
    
    return render_template('main.html', chatrooms = Chatroom.query.order_by(asc(Chatroom.id)).all(), hostrooms =Chatroom.query.filter(Chatroom.host == session['id']).order_by(asc(Chatroom.title)).all())

if __name__ == '__main__':
    app.run(debug = True)


