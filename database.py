# To replace
db_username = "Database_Username"
db_password = "Database_Password"
hostname = "Host_Name"
db_name = "Database_Name"
# To replace


from flask_sqlalchemy import SQLAlchemy


wait_name = 'WAIT_NAME'
SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{db_username}:{db_password}@{hostname}/{db_name}"
db = SQLAlchemy()


class Task(db.Model):
    __tablename__ = "tasks"

    task_id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('users.chat_id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.Integer)


class User(db.Model):
    __tablename__ = "users"

    chat_id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(100), nullable=False, default=wait_name)
    total = db.Column(db.Boolean, default=True, nullable=False)
    dif = db.Column(db.Boolean, default=False, nullable=False)
    due = db.Column(db.Boolean, default=False, nullable=False)
    calendar = db.Column(db.String(10))
    timezone = db.Column(db.String(100), default=None)
    date_joined = db.Column(db.DateTime, nullable=False)
