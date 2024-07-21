from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
from flask_migrate import Migrate


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"  # sets database path to instance folder
db.init_app(app)   # initializes database

# Initialize Flask-Migrate
migrate = Migrate(app, db)


# CREATE TABLE
"""This creates a table with attributes. Mapped sets type and mapped_column maps column to type"""


class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)  # Changed to nullable=True
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=True)


"""This creates the table"""
with app.app_context():
    db.create_all()

# """This adds the new record to the table"""
# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# with app.app_context():
#     db.session.add(new_movie)
#     db.session.commit()

@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()  # convert ScalarResult to Python List

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=['GET', 'POST'])
def edit():
    form = RateMovieForm()    # object fo flask form is created
    movie_id = request.args.get("id")       # id of movie to be updated is retrieved
    movie1 = db.get_or_404(Movie, movie_id)   # the movie related to that id is retrieved from database
    """Changes are updated in database for that movie"""
    if form.validate_on_submit():
        movie1.rating = float(form.rating.data)
        movie1.review = form.review.data
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
    title = form1.title.data       # fetches the title of movie
    if form1.validate_on_submit():
        """Use fo api to get the data about movie"""
        response = requests.get(url=movie_url, params={"api_key": api_key, "query": title})
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form1)


@app.route("/find")
def find():
    movie_id = request.args.get("id")
    MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
    url_movie = f"https://api.themoviedb.org/3/movie/{movie_id}"
    if url_movie:

        # The language parameter is optional, if you were making the website for a different audience
        # e.g. Hindi speakers then you might choose "hi-IN"
        response = requests.get(url_movie, params={"api_key": api_key, "language": "en-US"})
        data = response.json()
        print(data)
        new_movie = Movie(
            title=data["title"],
            # The data in release_date includes month and day, we will want to get rid of.
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",

            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", id=new_movie.id))


"""Creating form to edit the movie rating"""
class RateMovieForm(FlaskForm):
    rating = StringField(u'Your rating out of 10. e.g 7.5', validators=[DataRequired()])
    review = StringField(u'Your review', validators=[DataRequired()])
    done = SubmitField('Done')


"""Form to add the new movies"""
class MovieTitle(FlaskForm):
    title = StringField(u'Movie Title')
    add = SubmitField('Add Movie')


"""API for movies list"""
movie_url = "https://api.themoviedb.org/3/search/movie"
api_key = "badc25885292f12e43fe4bacfaf597aa"


if __name__ == '__main__':
    app.run(debug=True)
