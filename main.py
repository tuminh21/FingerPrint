from flask import Flask, render_template, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Thay đổi giá trị này cho an toàn hơn

# Cấu hình Firebase Admin SDK
cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://tien-s-project-default-rtdb.firebaseio.com/'  # Thay your-project-id bằng ID Firebase của bạn
})

# Cấu hình Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Biểu mẫu đăng ký
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

# Biểu mẫu đăng nhập
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@app.route('/')
@login_required
def index():
    return f'Hello, {current_user.id}! <a href="/logout">Logout</a>'

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Lưu thông tin người dùng vào Firebase
        ref = db.reference('users')
        ref.child(username).set({'password': password})  # Lưu mật khẩu (khuyến nghị mã hóa mật khẩu)

        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Kiểm tra thông tin đăng nhập từ Firebase
        ref = db.reference('users')
        user_data = ref.child(username).get()
        
        if user_data and user_data['password'] == password:  # Kiểm tra mật khẩu
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/update_data', methods=['POST'])
def update_data():
    data_id = request.form['data_id']
    new_data = request.form['new_data']
    updated_at = datetime.now().isoformat()  # Thời gian hiện tại

    # Cập nhật dữ liệu trong Firestore
    db.collection('your_collection').document(data_id).update({
        'data': new_data,
        'updatedAt': updated_at
    })

    return redirect(url_for('data_list'))


@app.route('/data_list')
def data_list():
    data_ref = db.collection('your_collection').stream()
    data_list = []

    for doc in data_ref:
        doc_data = doc.to_dict()
        doc_data['updatedAt'] = datetime.fromisoformat(doc_data['updatedAt'])  # Chuyển đổi chuỗi thành datetime
        data_list.append(doc_data)

    return render_template('data_list.html', data=data_list)

if __name__ == '__main__':
    app.run(debug=True)
