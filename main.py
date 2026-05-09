from flask import Flask, render_template, redirect, url_for, jsonify
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
from flask_ckeditor.utils import cleanify
from datetime import date
import os

app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY 
app.config['CKEDITOR_PKG_TYPE'] = 'standard'
Bootstrap5(app)
CKEditor(app)

class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLE
class BlogPost(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

class BlogForm(FlaskForm):
    title = StringField('Blog Post Title',validators=[DataRequired()])
    subtitle = StringField('Subtitle', validators=[DataRequired()])
    name = StringField('Your Name', validators=[DataRequired()])
    url = StringField('Blog Image URL', validators=[DataRequired(), URL(message="Please enter a valid URL")])
    content = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")
    

with app.app_context():
    db.create_all()


@app.route('/')
def get_all_posts():
    posts = db.session.execute(db.select(BlogPost)).scalars().all()
    return render_template("index.html", all_posts=posts)

@app.route('/<post_id>')
def show_post(post_id):
    requested_post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar_one_or_none()
    if requested_post is None:
        return jsonify({"error": "Post not found"})
    return render_template("post.html", post=requested_post)



@app.route('/new-post', methods=["GET", "POST"])
def add_new_post():
    form = BlogForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data, #type: ignore
            subtitle=form.subtitle.data,    #type: ignore
            author=form.name.data,  #type: ignore
            img_url=form.url.data, #type: ignore
            body=cleanify(form.content.data), #type: ignore
            date=date.today().strftime("%B %d, %Y") #type: ignore
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route('/edit-post/<post_id>', methods=["GET", "POST"])
def edit_post(post_id: int):
    post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar_one_or_none()
    if post is None:
        return jsonify({"error": "Post not found"})
    form = BlogForm(
        title=post.title,
        subtitle=post.subtitle,
        name=post.author,
        url=post.img_url,
        content=post.body
    )
    if form.validate_on_submit():
        post.title = form.title.data #type: ignore
        post.subtitle = form.subtitle.data #type: ignore
        post.author = form.name.data #type: ignore
        post.img_url = form.url.data #type: ignore
        post.body = cleanify(form.content.data) #type: ignore
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=form, is_edit=True)


@app.route('/delete-post/<post_id>')
def delete_post(post_id: int):
    post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar_one_or_none()
    if post is None:
        return jsonify({"error": "Post not found"})
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("get_all_posts"))

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True, port=5003)
