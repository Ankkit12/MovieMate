from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

# CREATE DB
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://movies_db_naye_user:eiEsSQXtQOKR2BwntAaXhTtvfu1UCvbA@dpg-cqjbtm0gph6c7394voj0-a/movies_db_naye"
db.init_app(app)

# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500), unique=True)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(500), nullable=True)
    img_url: Mapped[str] = mapped_column(String(500), nullable=True)

with app.app_context():
    db.drop_all()
    db.create_all()

@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)

@app.route("/edit", methods=['GET', 'POST'])
def edit():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie1 = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie1.rating = float(form.rating.data)
        movie1.review = form.review.data[:500]  # Truncate review to 500 characters
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, movie=movie1)

@app.route("/delete", methods=['GET', 'POST'])
def delete():
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/add", methods=['GET', 'POST'])
def add():
    form1 = MovieTitle()
    if form1.validate_on_submit():
        title = form1.title.data
        response = requests.get(url=movie_url, params={"api_key": api_key, "query": title})
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form1)

@app.route("/find")
def find():
    movie_id = request.args.get("id")
    MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
    url_movie = f"https://api.themoviedb.org/3/movie/{movie_id}"
    response = requests.get(url_movie, params={"api_key": api_key, "language": "en-US"})
    data = response.json()

    # Ensure the data lengths are within the defined limits
    title = data["title"][:500]  # Truncate title to 500 characters
    description = data["overview"][:500]  # Truncate description to 500 characters
    img_url = f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}"[:500]  # Truncate img_url to 500 characters

    new_movie = Movie(
        title=title,
        year=int(data["release_date"].split("-")[0]),
        img_url=img_url,
        description=description
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for("edit", id=new_movie.id))

class RateMovieForm(FlaskForm):
    rating = StringField(u'Your rating out of 10. e.g 7.5', validators=[DataRequired(), Length(max=4)])
    review = StringField(u'Your review', validators=[DataRequired(), Length(max=500)])
    done = SubmitField('Done')

class MovieTitle(FlaskForm):
    title = StringField(u'Movie Title', validators=[DataRequired(), Length(max=500)])
    add = SubmitField('Add Movie')

movie_url = "https://api.themoviedb.org/3/search/movie"
api_key = "badc25885292f12e43fe4bacfaf597aa"

if __name__ == '__main__':
    app.run(debug=True)
