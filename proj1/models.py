from flask_sqlalchemy import SQLAlchemy 

from datetime import datetime


db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique = True)
    pw = db.Column(db.String(50),nullable = False)
    attending =  db.relationship('Event', secondary='attending', lazy = 'dynamic' )

    passhash = db.Column(db.String(50), nullable =False)
    def __init__(self, username, pw, passhash):
        self.username = username
        self.passhash = passhash
        self.pw = pw

    def __repr__(self):
        return '<Person %r>' % self.username 

attending = db.Table('attending',
    db.Column('userid', db.Integer, db.ForeignKey('user.id')),
    db.Column('eventid', db.Integer, db.ForeignKey('event.id'))
#association table named follows
#joins is when we pull data out of SQL and put it together based on how it related to each other

)

class Event (db.Model):
    title = db.Column(db.String(120),nullable = False)
    description = db.Column(db.String(200))
    startdatetime = db.Column(db.String(120),nullable = False)
    enddatetime = db.Column(db.String(120),nullable = False)
    id = db.Column(db.Integer, primary_key = True)
    host = db.Column(db.Integer, db.ForeignKey('user.id'))

    #attendees = db.relationship('Userprof', backref = 'event', lazy = 'dynamic')
  
    def __init__(self, title, description, startdatetime, enddatetime, host):
        self.title = title
        self.description = description
        self.startdatetime = startdatetime
        self.enddatetime = enddatetime
        self.host = host
    
    def __repr__(self):
        return '<Event %r' % self.title

    # persid = db.relationship('Userprof', backref = db.backref('attending', lazy = 'dynamic'))
    #hosting = db.relationship('Event', backref='userprof', lazy = 'dynamic' )

