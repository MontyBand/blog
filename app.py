# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, flash, session, redirect, url_for, jsonify
from models import db, Articulos, User, Categorias, Tag, tags
from os import getenv
# Para comprobar contraseña
from werkzeug.security import check_password_hash
# Para subir imagenes con seguridad
from werkzeug import  secure_filename
from time import time
# Para calcular el numero de articulos y redondear hacia arriba
from math import ceil

# Iniciar
app = Flask(__name__)

# Config
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = getenv('SECRET_KEY')
# Maximo tamaño de imagen permitido y tipo de archivo
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = set(['jpg', 'png'])

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route("/")
def blog_all():
    # Para ordenar los articulos
    mis_articulos = Articulos.query.order_by(Articulos.id.desc()).all()
    # Calculamos el numero maximo de paginas
    max_pags = ceil(len(mis_articulos) / 5)
    return render_template('web/blog/all.html', articulos=mis_articulos, max_pags=max_pags)

@app.route("/articulo/<int:id>/")
def blog_articulo(id):
    # Ambas formas valen
    mi_articulo = Articulos.query.get(id)
    # select * from user where id = mi_aritulo.user_id
    mi_autor = User.query.filter_by(id=mi_articulo.user_id).first()
    mi_categoria = Categorias.query.get(mi_articulo.categoria_id)
    return render_template(
        'web/blog/articulo.html',
        articulo=mi_articulo,
        autor=mi_autor.username,
        categoria=mi_categoria.name
        )

@app.route("/admin/login/", methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        my_user = User.query.filter_by(email=request.form['email']).first()
        # Comprobar si correo existe en base de datos y si su contraseña es cierta
        if my_user and check_password_hash(my_user.password, request.form['password']):
            flash('Bienvenido', 'success')
            session['id'] = my_user.id
            return redirect(url_for('admin_articulos'))
        else:
            flash('Tu email o password no son correctos')
    return render_template('web/admin/login.html')

@app.route('/admin/articulos/')
def admin_articulos():
    # Protegemos nuestra pagina
    if 'id' not in session:
        flash('No tienes acceso', 'danger')
        return redirect(url_for('blog_all'))
    # Obtenemos todos los articulos
    articulos = Articulos.query.order_by(Articulos.id.desc()).all()
    return render_template('web/admin/articulos.html', articulos=articulos)

@app.route('/admin/articulos/nuevo', methods=['GET', 'POST'])
def admin_nuevo_articulo():
    # Protegemos nuestra pagina
    if 'id' not in session:
        flash('No tienes acceso', 'danger')
        return redirect(url_for('blog_all'))
    
    # Recogemos los datos del formulario
    if request.method == 'POST':
        titulo = request.form['titulo']
        contenido = request.form['contenido']
        categoria = request.form['categoria']
        # Para recoger varios tags de un select2
        mis_tags = request.form.getlist('tags')
        usuario = session['id']
        # Guardamos en BD
        nuevo_articulo = Articulos()
        nuevo_articulo.title = titulo
        nuevo_articulo.text = contenido
        nuevo_articulo.categoria_id = categoria
        nuevo_articulo.user_id = usuario
        # Guardamos los tags - many to many - n a n
        for tag in mis_tags:
            mi_temp_tag = Tag.query.get(tag)
            nuevo_articulo.tags.append(mi_temp_tag)
        # Guardamos imagen (que no tenga el mismo nombre)
        try:
            f = request.files['portada']
            nombre = str(int(time())) + f.filename
            f.save('static/uploads/' + secure_filename(nombre))
            nuevo_articulo.portada = nombre
        except:
            flash('No se ha subido la imagen de portada', 'danger')
        # Ejecutamos SQL
        db.session.add(nuevo_articulo)
        db.session.commit()
        # Mostramos una información al usuario
        flash('Articulo creado', 'success')

    # Obtengo las categorias
    categorias = Categorias.query.all()
    # Obtengo los tags
    tags = Tag.query.all()

    return render_template('web/admin/nuevo_articulo.html', categorias=categorias, tags=tags)

@app.route('/admin/articulos/actualizar/<int:id>', methods=['GET', 'POST'])
def admin_actualizar_articulo(id):
    # Protegemos nuestra pagina
    if 'id' not in session:
        flash('No tienes acceso', 'danger')
        return redirect(url_for('blog_all'))

    # Obtenemos el articulo
    mi_articulo = Articulos.query.get(id)
    
    # Recogemos los datos del formulario
    if request.method == 'POST':
        titulo = request.form['titulo']
        contenido = request.form['contenido']
        categoria = request.form['categoria']
        # Para recoger varios tags de un select2
        mis_tags = request.form.getlist('tags')
        usuario = session['id']
        # Guardamos en BD
        mi_articulo.title = titulo
        mi_articulo.text = contenido
        mi_articulo.categoria_id = categoria
        mi_articulo.user_id = usuario
        # Guardamos los tags - many to many - n a n
        for tag in mis_tags:
            mi_temp_tag = Tag.query.get(tag)
            mi_articulo.tags.append(mi_temp_tag)
        # Guardamos imagen (que no tenga el mismo nombre)
        try:
            f = request.files['portada']
            if f.filename:
                nombre = str(int(time())) + f.filename
                f.save('static/uploads/' + secure_filename(nombre))
                mi_articulo.portada = nombre
        except:
            flash('No se ha subido la imagen de portada', 'danger')
        # Ejecutamos SQL
        db.session.add(mi_articulo)
        db.session.commit()
        # Mostramos una información al usuario
        flash('Articulo actualizado', 'success')

    # Obtengo las categorias
    categorias = Categorias.query.all()
    # Obtengo los tags
    tags = Tag.query.all()

    return render_template(
        'web/admin/actualizar_articulo.html',
        categorias=categorias,
        tags=tags,
        articulo=mi_articulo
        )

@app.route('/articulo/borrar', methods=['POST'])
def borrar_articulo():
    if request.method == 'POST':
        # Obtenemos la id
        articulo_id_borrar = int(request.form['articulo-borrar'])
        # Borramos de la base de datos
        Articulos.query.filter_by(id=articulo_id_borrar).delete()
        db.session.commit()
        flash('Articulo borrado', 'success')

    return redirect(url_for('admin_articulos'))

@app.route('/admin/categorias')
def admin_categorias():
    # Protegemos nuestra pagina
    if 'id' not in session:
        flash('No tienes acceso', 'danger')
        return redirect(url_for('blog_all'))
    # Obtenemos todas las categorias
    categorias = Categorias.query.order_by(Categorias.id.desc()).all()
    return render_template('web/admin/categorias.html', categorias=categorias)

@app.route('/admin/categorias/nueva', methods=['GET', 'POST'])
def admin_nueva_categoria():
    # Protegemos nuestra pagina
    if 'id' not in session:
        flash('No tienes acceso', 'danger')
        return redirect(url_for('blog_all'))
    # Recogemos los datos del formulario
    if request.method == 'POST':
        nom_categoria = request.form['categoria']
        # Guardamos en BD
        nueva_categoria = Categorias()
        nueva_categoria.name = nom_categoria
        # Ejecutamos SQL
        db.session.add(nueva_categoria)
        db.session.commit()
        # Mostramos una información al usuario
        flash('Categoria creada', 'success')
        return redirect(url_for('admin_categorias'))
    
    return render_template('web/admin/nueva_categoria.html')

@app.route('/categoria/borrar', methods=['POST'])
def borrar_categoria():
    if request.method == 'POST':
        # Obtenemos la id
        categoria_id_borrar = int(request.form['categoria-borrar'])
        # Borramos de la base de datos
        Categorias.query.filter_by(id=categoria_id_borrar).delete()
        db.session.commit()
        # Marcamos la categoria por defecto para los articulos
        articulos = Articulos.query.filter_by(categoria_id=categoria_id_borrar).all()
        for articulo in articulos:
            articulo.categoria = Categorias.query.first()
            db.session.add(articulo)
        db.session.commit()

        flash('Categoria borrada', 'success')

    return redirect(url_for('admin_categorias'))

@app.route('/categoria/editar/<int:id>', methods=['GET', 'POST'])
def editar_categoria(id):
    # Consultamos en la BD
    mi_categoria = Categorias.query.get(id)

    if request.method == 'POST':
        # Actualizo en la base de datos
        nombre = request.form['categoria']
        mi_categoria.name = nombre
        db.session.add(mi_categoria)
        db.session.commit()
        # Informo
        flash('Categoria actualizada', 'success')
        # Redirecciono
        return redirect(url_for('admin_categorias'))

    # Renderizamos html
    return render_template('web/admin/editar_categoria.html', categoria=mi_categoria)

@app.route('/admin/tags')
def admin_tags():
    # Protegemos nuestra pagina
    if 'id' not in session:
        flash('No tienes acceso', 'danger')
        return redirect(url_for('blog_all'))
    # Obtenemos todas las tags
    tags = Tag.query.order_by(Tag.id.desc()).all()
    return render_template('web/admin/tags.html', tags=tags)

@app.route('/admin/tag/nuevo', methods=['GET', 'POST'])
def admin_nuevo_tag():
    # Protegemos nuestra pagina
    if 'id' not in session:
        flash('No tienes acceso', 'danger')
        return redirect(url_for('blog_all'))
    # Recogemos los datos del formulario
    if request.method == 'POST':
        nom_tag = request.form['tag']
        # Guardamos en BD
        nuevo_tag = Tag()
        nuevo_tag.name = nom_tag
        # Ejecutamos SQL
        db.session.add(nuevo_tag)
        db.session.commit()
        # Mostramos una información al usuario
        flash('Tag creado', 'success')
        return redirect(url_for('admin_tags'))
    
    return render_template('web/admin/nuevo_tag.html')

@app.route('/tag/editar/<int:id>', methods=['GET', 'POST'])
def editar_tag(id):
    # Consultamos en la BD
    mi_tag = Tag.query.get(id)

    if request.method == 'POST':
        # Actualizo en la base de datos
        nombre = request.form['tag']
        mi_tag.name = nombre
        db.session.add(mi_tag)
        db.session.commit()
        # Informo
        flash('Tag actualizado', 'success')
        # Redirecciono
        return redirect(url_for('admin_tags'))

@app.route('/tag/borrar', methods=['POST'])
def borrar_tag():
    if request.method == 'POST':
        # Obtenemos la id
        tag_id_borrar = int(request.form['tag-borrar'])
        # Borramos de la base de datos
        Tag.query.filter_by(id=tag_id_borrar).delete()
        db.session.commit()

        flash('Categoria borrada', 'success')

    return redirect(url_for('admin_tags'))


@app.route('/logout')
def logout():
    session.pop('id', None)
    flash('Sesion cerrada con éxito', 'success')
    return redirect(url_for('blog_all')) 

@app.route('/buscar')
def buscar():
    if request.args.get('q'):
        q = request.args.get('q')
        # Para filtros de las palabras que contienen la busqueda (ilike sin molestar las mayusculas)
        mis_resultados = Articulos.query.filter(Articulos.title.ilike(f'%{q}%')).all()
        return render_template(
            'web/blog/busqueda.html',
            resultados=mis_resultados,
            num_resultados=len(mis_resultados),
            busqueda=q
        )
    else:
        # Si no hay busqueda redireccionamos al blog
        return redirect(url_for('admin_tags'))

@app.route('/api/articulos/<int:pag>')
def api_articulos(pag):
    num_articulos_max = 5
    mis_articulos = Articulos.query.offset((pag - 1) * num_articulos_max).limit(num_articulos_max).all()
    # Convertimos un resultado de models a JSON
    dict_resultados = {}
    for articulo in mis_articulos:
        # Obtenemos la ruta de la portada
        portada = ''
        if articulo.portada:
            portada = url_for('static', filename='uploads/' + articulo.portada)
        # Creamos diccionario
        dict_resultados[articulo.id] = {
            'id': articulo.id,
            'title': articulo.title,
            'text': articulo.text[1:100],
            'portada': portada
        }
    return jsonify(dict_resultados)

if __name__ == '__main__':
    app.run()