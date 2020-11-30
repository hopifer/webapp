from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash, jsonify, make_response, request,  _app_ctx_stack
from flask_sqlalchemy import SQLAlchemy 
from flask_restful import Api, Resource, reqparse, fields, abort, marshal_with
from sqlalchemy import asc
from datetime import datetime
import json
import requests
from datetime import date





app = Flask(__name__)
api = Api(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config.from_object(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #here to silence deprecation warning
app.secret_key = 'development key'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique = True)
    pw = db.Column(db.String(50),nullable = False)
  
    def __init__(self, username, pw):
        self.username = username
        self.pw = pw

    def __repr__(self):
        return '<Person %r>' % self.username




class Cat(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    budgetname = db.Column(db.String(50))
    budgetamount = db.Column(db.Integer)

    spender = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __init__(self, budgetname, budgetamount, spender):
        self.budgetname = budgetname
        self.budgetamount = budgetamount
        self.spender = spender
    def subtract(self, dollar):
        self.budgetamount = self.budgetamount - int(dollar)
    def add(self, dollar):
        self.budgetamount = self.budgetamount + int(dollar)
    
    def __repr__(self):
        return '<Cat %r' % self.budgetname




#each user should have budget catergories as well as purchases
class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name_of_purchase = db.Column(db.String(50))
    amount = db.Column(db.Integer)
    spender = db.Column(db.Integer, db.ForeignKey('user.id'))
    budget = db.Column(db.String)
    date = db.Column(db.String(50))

    #FIX THIS TO BE THE DATE OBJECT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    def __init__(self, name_of_purchase, amount, date, spender,budget):
        self.name_of_purchase = name_of_purchase
        self.amount = amount
        self.spender = spender
        self.date = date
        self.budget = budget
    def updateBudg(self, newbudget):
        self.budget = newbudget
     
    def __repr__(self):
        return '<Purchase %r' % self.name_of_purchase


@app.before_request #runs before any request 
def before_request():
	g.user = None #sets global value in application to none 
	#user is defined inside of g and it is reset each time 
	
	if 'id' in session: #how to procest from the requests
		#so if we do have a user that is loged in we will put it into the g.user
		g.user = User.query.filter_by(id=session['id']).first()


categories = {}
cat_put_args = reqparse.RequestParser()
cat_put_args.add_argument("budgetname", type = str, help = "Name of the budget category")
cat_put_args.add_argument("budgetamount", type = int, help = "Amount of budget left")
cat_put_args.add_argument("spender", type = int, help = "User id of spender")



resource_fields = {
    'id': fields.Integer,
    'budgetname' : fields.String,
    'budgetamount' : fields.Integer,
    'spender' : fields.Integer
}



class Category(Resource):
    @marshal_with(resource_fields)
    def get(self):
        result = Cat.query.filter_by(spender = session['id']).all()
        if not result:
            return render_template('budget.html', cats = None)

        return result

    @marshal_with(resource_fields)
    def post(self):
        args = cat_put_args.parse_args()
        cat = Cat(budgetname=args['budgetname'],budgetamount = args['budgetamount'],spender=args['spender'])
        db.session.add(cat)
        db.session.commit()
        return  {"id": cat.id, "budgetname": args['budgetname'], "budgetamount": args['budgetamount'], "spender": session['id']}
        ###############################################

class CategoryD(Resource):
        def get(self, category_id):
        
            result = Cat.query.filter_by(id = category_id).first()
            
            if not result:
                abort(401, message = "cannot find a category with that id")
            #####del 
            db.session.delete(result)
            purchases = Purchase.query.filter_by(budget = result.budgetname).all()
            for item in purchases:
                item.updateBudg("Unknown")
                updatetot = Cat.query.filter_by(budgetname = "Unknown").first()
                updatetot.add(item.amount)
            db.session.commit()
            return redirect(url_for('addbudget'))




api.add_resource(Category, "/cat")
api.add_resource(CategoryD, "/cat/<int:category_id>")


purchases = {}
pur_put_args = reqparse.RequestParser()
pur_put_args.add_argument("name_of_purchase", type = str, help = "Name of the purchase")
pur_put_args.add_argument("amount", type = int, help = "Amount of the purchase")
pur_put_args.add_argument("date", type = str, help = "Date of the purchase")
pur_put_args.add_argument("spender", type = int, help = "User id of spender")
pur_put_args.add_argument("budget", type = str, help = "Budget of purchase")


resource_fields = {
    'id': fields.Integer,
    'name_of_purchase' : fields.String,
    'amount' : fields.Integer,
    
    'date' : fields.String,
    'spender' : fields.Integer,
    'budget' : fields.String

}



class Pur(Resource):
    @marshal_with(resource_fields)
    def get(self):
        result = Purchase.query.filter_by(spender = session['id']).all()
        if not result:
            return render_template('purchase.html')

        return result

    @marshal_with(resource_fields)
    def post(self):
        args = pur_put_args.parse_args()
        purc = Purchase(name_of_purchase=args['name_of_purchase'],amount = args['amount'],date=args['date'],spender=args['spender'],budget=args['budget'])
        db.session.add(purc)

        db.session.commit()
        return  {"id": purc.id, "name_of_purchase": args['name_of_purchase'], "amount": args['amount'], "date": args['date'], "spender": session['id'], "budget": args['budget']}
        ###############################################




api.add_resource(Pur, "/purchase")




db.init_app(app)
@app.cli.command('initdb')
def initdb_command(): #initializes the database
    db.drop_all()
    db.create_all()


#test = User("test4", "test2")
#db.session.add(test)
#db.session.commit()
#testcat = Cat("FunBudget", 100, test.id)
#db.session.add(testcat)
#db.session.commit()

def signedin(username):
    ret = User.query.filter_by(username=username).first()
    return ret.id if ret else None

@app.route('/')
def main():
    return redirect(url_for('addbudget'))
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
            uncat = Cat("Unknown",0,co.id)
            db.session.add(uncat)
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
            return redirect(url_for('login'))

    return render_template('login.html', error = error)
@app.route('/cats', methods=['GET','POST'])
def addbudget():
    error = None
    if request.method == 'POST':
        if not request.form['budgetname']:
            error = 'Must enter a budget name.'
        elif not request.form['budgetamount']:
            error = 'Must enter a budget amount.'
        else:
            
            cats = Cat(request.form['budgetname'], request.form['budgetamount'],session['id'])
            db.session.add(cats)
            
            db.session.commit()
            
            return redirect(url_for('addbudget'))
    return render_template('budget.html', error = error)

@app.route('/purchases', methods=['GET','POST'])
def addpurchase():
    error = None
    today = date.today()
    if request.method == 'POST':
        a=today.strftime("%d/%m/%Y")
        a=a.split('/')[1]

        day = request.form['date']
        day = day.split('/')[0]

        if not request.form['name_of_purchase']:
            error = 'Must enter a purchase name.'
        elif not request.form['amount']:
            error = 'Must enter an amount.'
        elif Cat.query.filter_by(budgetname = request.form['budget']).first() is None:
            error = "There is no budget with that name."
        elif day != a:
            error = "That purchase is not for the current month and will not be considered with current budgets."
        else:
            
            purch = Purchase(request.form['name_of_purchase'], request.form['amount'],request.form['date'],session['id'],request.form['budget'])
            if request.form['budget']!="Unknown":
                updatetot = Cat.query.filter_by(budgetname = request.form['budget']).first()
                updatetot.subtract(request.form['amount'])

            else:
                updatetot = Cat.query.filter_by(budgetname = request.form['budget']).first()
                updatetot.add(request.form['amount'])
            db.session.add(purch)
            
            db.session.commit()
            
            return redirect(url_for('addpurchase'))
    return render_template('purchase.html', error = error)

@app.route('/logout')
def logout():
	session.pop('id', None)
	return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)