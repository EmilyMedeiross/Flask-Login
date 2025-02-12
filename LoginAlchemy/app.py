from flask import Flask, url_for, redirect, render_template, request, flash
from flask_login import UserMixin, LoginManager, login_user, current_user, logout_user, login_required
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase, Session
from sqlalchemy import create_engine, String, ForeignKey, Column, Integer, Table, DateTime
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Instalar requirements -> pip install -r requirements.txt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fs3w8d#39e*&9'

engine = create_engine("sqlite:///banco.db")
session = Session(bind=engine)

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return Usuario.find(id=user_id)

login_manager.init_app(app)

class Base(DeclarativeBase):
    pass

# -------- Tabelas ---------

locacao_livros = Table(
    'locacao_livros',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('usuario_id', Integer, ForeignKey('usuarios.id')),
    Column('livro_id', Integer, ForeignKey('livros.id')),
    Column('data_locacao', DateTime, default=datetime.now),
    Column('data_devolucao', DateTime)
)

class Usuario(Base, UserMixin):
    __tablename__ = 'usuarios'
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(nullable=False)
    senha: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)

    livros_adicionados = relationship('Livro', back_populates='usuario')  # Livros adicionados pelo usuário
    livros_locados = relationship('Livro', secondary=locacao_livros, back_populates='usuarios_locadores')  # Livros emprestados ao usuário

    @classmethod
    def find(cls, **kwargs):
        if 'nome' in kwargs:
            return session.query(cls).filter_by(nome=kwargs['nome']).first()
        elif 'id' in kwargs:
            return session.query(cls).filter_by(id=kwargs['id']).first()

    @classmethod
    def gerar_hash(cls, nome, senha, email):
        hashed_password = generate_password_hash(senha)
        return cls(nome=nome, senha=hashed_password, email=email)

class Livro(Base, UserMixin):
    __tablename__ = 'livros'
    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(nullable=False)
    autor: Mapped[str] = mapped_column(nullable=False)
    editora: Mapped[str] = mapped_column(nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey('usuarios.id'))  # Quem adicionou o livro

    usuario = relationship('Usuario', back_populates='livros_adicionados')  # Relação com o usuário que adicionou
    usuarios_locadores = relationship('Usuario', secondary=locacao_livros, back_populates='livros_locados')  # Relação de empréstimos

with app.app_context():
    Base.metadata.create_all(bind=engine)  # Cria as tabelas

# ---------- Rotas ---------

@app.route('/')
def index():
    user = current_user  # recupera o usuário logado
    if user.is_authenticated:
        return render_template('index.html', nome=user.nome)
    else:
        return render_template('index.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        email = request.form['email']
        novo_user = Usuario.gerar_hash(nome=nome, senha=senha, email=email)
        session.add(novo_user)
        session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        user = session.query(Usuario).filter(Usuario.email == email).first()

        if not user:
            print('O usuário nao foi encontrado!')
            flash('Usuário não encontrado', 'error')
            return redirect(url_for('login'))

        if check_password_hash(user.senha, senha):
            print('Você está logado!')
            login_user(user)
            user = current_user
            return redirect(url_for('register_books'))

        else:
            print("Senha incorreta! Tente novamente")
            flash('Senha incorreta. Tente novamente.', 'error')
            return render_template('login.html', email=email)

    return render_template('login.html')


@app.route('/register_books', methods=['POST', 'GET'])
@login_required
def register_books():
    if request.method == 'POST':
        titulo = request.form['titulo']
        autor = request.form['autor']
        editora = request.form['editora']

        livro_existente = session.query(Livro).filter_by(titulo=titulo).first()
        if livro_existente:
            flash('Livro já cadastrado!', 'error')
            return redirect(url_for('register_books'))

        new_book = Livro(titulo=titulo, autor=autor, editora=editora, usuario_id=current_user.id)

        session.add(new_book)
        session.commit()
        flash('Livro cadastrado com sucesso!', 'success')
        return redirect(url_for('list_books'))

    return render_template('register_books.html')

@app.route('/list_books', methods=['POST', 'GET'])
@login_required
def list_books():
    livros = session.query(Livro).all()
    return render_template('list_books.html', livros=livros)

@app.route('/locar_livro/<int:livro_id>', methods=['POST'])
@login_required
def locar_livro(livro_id):

    livro = session.query(Livro).filter_by(id=livro_id).first()
    if not livro:
        flash('Livro não encontrado!', 'error')
        return redirect(url_for('list_books'))

    # Faz uma consulta na tabela de associação locacao_livros para ver se esse livro já foi emprestado
    locacao_existente = session.query(locacao_livros).filter_by(livro_id=livro_id, data_devolucao=None).first() 
    if locacao_existente:
        flash('Este livro já está emprestado!', 'error')
        return redirect(url_for('list_books'))

    # Cria um novo registro de locação na tabela 
    locacao = locacao_livros.insert().values(
        usuario_id=current_user.id,
        livro_id=livro_id,
        data_locacao=datetime.now()
    )
    session.execute(locacao)
    session.commit()

    flash(f'Livro "{livro.titulo}" emprestado com sucesso!', 'success')
    return redirect(url_for('list_books'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)