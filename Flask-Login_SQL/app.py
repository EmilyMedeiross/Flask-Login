from flask import Flask, render_template \
    , url_for, request, redirect

from flask_login import LoginManager, login_required, login_user, logout_user

from models import User, obter_conexao

from werkzeug.security import generate_password_hash, check_password_hash

login_manager = LoginManager()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'SUPERMEGADIFICIL'
login_manager.init_app(app)

# quando precisar saber qual o usuario conectado
# temos como consultar ele no banco
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def gerar_hash(matricula, email, senha):
    hashed_password = generate_password_hash(senha)
    hashed_email = generate_password_hash(email)
    INSERT = 'INSERT INTO usuarios(matricula,email,senha) VALUES (?,?,?)'
    conexao = obter_conexao()
    conexao.execute(INSERT, (matricula, hashed_email, hashed_password))
    conexao.commit()
    conexao.close()

@app.route('/')
def index():
    return render_template('index.html')
    

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        matricula = request.form['matricula']
        senha = request.form['pass']
        
        user = User.get_by_matricula(matricula)
        hash = user.senha

        if user and check_password_hash (hash, senha):
            
            login_user(user)

            return redirect(url_for('dash'))

    return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():

    if request.method == 'POST':
        matricula = request.form['matricula']
        email = request.form['email']
        senha = request.form['pass']
        gerar_hash(matricula, email, senha)
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/dash')
@login_required
def dash():

    return render_template('dash.html')


    
@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return redirect(url_for('index'))


