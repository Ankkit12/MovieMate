import os
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

# Secret key (use environment in production)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

Bootstrap5(app)

# ---------------- DATABASE CONFIG ---------------- #

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

database_url = os.environ.get("DATABASE_URL")

# Safety check (avoids crash if not set)
if not database_url:
    raise ValueError("DATABASE_URL is not set in environment variables")

# Fix postgres:// issue if present
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

db.init_app(app)

# ---------------- TABLE ---------------- #

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
    db.create_all()

# ---------------- ROUTES ---------------- #

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
        movie1.review = form.review.data[:500]
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("edit.html", form=form, movie=movie1)


@app.route("/delete")
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

        try:
            response = requests.get(
                url=movie_url,
                params={"api_key": api_key, "query": title},
                timeout=10
            )

            data = response.json()

            # Safe validation to prevent KeyError
            if "results" not in data:
                return f"TMDB API Error: {data}"

            return render_template("select.html", options=data["results"])

        except Exception as e:
            return f"API Request Failed: {str(e)}"

    return render_template("add.html", form=form1)


@app.route("/find")
def find():
    movie_id = request.args.get("id")
    MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
    url_movie = f"https://api.themoviedb.org/3/movie/{movie_id}"

    try:
        response = requests.get(
            url_movie,
            params={"api_key": api_key, "language": "en-US"},
            timeout=10
        )

        data = response.json()

        if "title" not in data:
            return f"TMDB API Error: {data}"

        title = data["title"][:500]
        description = data.get("overview", "")[:500]
        img_url = f"{MOVIE_DB_IMAGE_URL}{data.get('poster_path', '')}"[:500]

        new_movie = Movie(
            title=title,
            year=int(data["release_date"].split("-")[0]) if data.get("release_date") else None,
            img_url=img_url,
            description=description
        )

        db.session.add(new_movie)
        db.session.commit()

        return redirect(url_for("edit", id=new_movie.id))

    except Exception as e:
        return f"API Request Failed: {str(e)}"


# ---------------- FORMS ---------------- #

class RateMovieForm(FlaskForm):
    rating = StringField(
        'Your rating out of 10. e.g 7.5',
        validators=[DataRequired(), Length(max=4)]
    )
    review = StringField(
        'Your review',
        validators=[DataRequired(), Length(max=500)]
    )
    done = SubmitField('Done')


class MovieTitle(FlaskForm):
    title = StringField(
        'Movie Title',
        validators=[DataRequired(), Length(max=500)]
    )
    add = SubmitField('Add Movie')


# ---------------- API CONFIG ---------------- #

movie_url = "https://api.themoviedb.org/3/search/movie"

# Use environment variable OR fallback to your existing key
api_key = os.environ.get("TMDB_API_KEY", "badc25885292f12e43fe4bacfaf597aa")


# ---------------- LOCAL RUN ---------------- #

if __name__ == '__main__':
    app.run(debug=True)
