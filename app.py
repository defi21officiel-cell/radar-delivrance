import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cle-super-secrete-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///radar.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    results = db.relationship('RadarResult', backref='user', lazy=True)

class RadarResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    scores_json = db.Column(db.Text, nullable=False) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Identifiants incorrects')
    return render_template('login.html')

@app.route('/save', methods=['POST'])
@login_required
def save():
    data = request.form.to_dict()
    new_res = RadarResult(scores_json=json.dumps(data), user_id=current_user.id)
    db.session.add(new_res)
    db.session.commit()
    flash('Radar enregistré avec succès !')
    return redirect(url_for('history'))

@app.route('/history')
@login_required
def history():
    results = RadarResult.query.filter_by(user_id=current_user.id).order_by(RadarResult.date_creation.desc()).all()
    # On décode le JSON pour l'affichage
    decoded_results = []
    for r in results:
        decoded_results.append({'date': r.date_creation, 'data': json.loads(r.scores_json)})
    return render_template('history.html', results=decoded_results)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('delivrance2026', method='pbkdf2:sha256'), is_admin=True)
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
