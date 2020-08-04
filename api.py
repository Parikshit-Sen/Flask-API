from flask import Flask,request,jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column,Integer,Float,String
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message
import os
app=Flask(__name__)
basedir=os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(basedir,'planets.db')
app.config['JWT_SECRET_KEY']='super-secret'
app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = '2c3837d715aa21'
app.config['MAIL_PASSWORD'] = 'c38ae43e478216'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
jwt=JWTManager(app)
@app.route('/<string:name>/<int:age>')
def hello(name:str, age:int):
    #name=request.args.get('name')
    #age=request.args.get('age')
    return jsonify(message=name+" "+str(age))
db=SQLAlchemy(app)
ma=Marshmallow(app)
mail=Mail(app)
@app.cli.command('db_create')
def db_create():
    db.create_all()
    print("Database Created")

@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print("Database Dropped")

@app.cli.command('db_seed')
def db_seed():
    mercury=Planet(planet_name="Mercury",planet_type="Class B",home_star="Sol",mass=3.258e23,radius=1516, distance=35.98e6)
    venus=Planet(planet_name="Venus",planet_type="Class K",home_star="Sol",mass=4.867e24,radius=3760, distance=67.24e6)
    db.session.add(mercury)
    db.session.add(venus)

    test_user=User(first_name="William", last_name="Herschel",email="test@test.com",password="Password")
    db.session.add(test_user)
    db.session.commit()


@app.route("/planets",methods=['GET'])
def planets():
    planets_list=Planet.query.all()
    result=planets_schema.dump(planets_list)
    return jsonify(result)

@app.route("/users",methods=['GET'])
def users():
    users_list=User.query.all()
    result=users_schema.dump(users_list)
    return jsonify(result)


@app.route('/register',methods=['POST'])
@jwt_required
def register():
    email=request.form['email']
    test=User.query.filter_by(email=email).first()
    if test:
        return jsonify("Email already exists")
    else:
        first_name=request.form['first_name']
        last_name=request.form['last_name']
        password=request.form['password']
        user=User(first_name=first_name,last_name=last_name,email=email,password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify("User created successfully"),201

@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email=request.json['email']
        password=request.json['password']
    else:
        email=request.form['email']
        password=request.form['password']

    test=User.query.filter_by(email=email,password=password).first()
    if test:
        access_token=create_access_token(identity=email)
        return jsonify(message="Login Successful",access_token=access_token)
    else:
        return jsonify("Wrong email or password")

@app.route('/retrieve_password/<string:email>',methods=['GET'])
def retrieve_password(email:str):
    test=User.query.filter_by(email=email).first()
    if test:
        msg=Message('Your planetary password is'+test.password,sender="admin@planetary.com",recipients=['email'])
        mail.send(msg)
        return jsonify("Password sent to "+email)
    else:
        return jsonify("That email doesn't exist")

class User(db.Model):
    __tablename__='users'
    id=Column(Integer, primary_key=True)
    first_name=Column(String)
    last_name=Column(String)
    email=Column(String, unique=True)
    password=Column(String)

class Planet(db.Model):
    __tablename__="planets"
    planet_id=Column(Integer, primary_key=True)
    planet_name=Column(String)
    planet_type=Column(String)
    home_star=Column(String)
    mass=Column(Float)
    radius=Column(Float)
    distance=Column(Float)

class UserSchema(ma.Schema):
    class Meta:
        fields=('id','first_name','last_name','email','password')

class PlanetSchema(ma.Schema):
    class Meta:
        fields=('planet_id','planet_name','planet_type','home_star','mass','radius','distance')

user_schema=UserSchema()
users_schema=UserSchema(many=True)

planet_schema=PlanetSchema()
planets_schema=PlanetSchema(many=True)
if __name__ == "__main__":
    app.run(debug=True)