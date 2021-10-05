#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
#from sqlalchemy import SQLAlchemy
from sqlalchemy import and_
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from config import *
from flask_migrate import Migrate
import sys

#app = Flask(__name__) 
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#db = SQLAlchemy(app)

app = Flask(__name__)
app.config.from_object('config')
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
  start_time = db.Column(db.DateTime, nullable=False)
  image_link = db.Column(db.String)

  def __repr__(self):
    return f'<Show ID: {self.id}, Artist ID: {self.artist_id}, Venue ID: {self.venue_id}>'

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    genres = db.Column(db.ARRAY(db.String), nullable=False)  #array of strings
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    past_shows = db.relationship('Show', backref='parent_venue_past', lazy=True, collection_class=list, cascade='save-update')
    past_shows_count = db.Column(db.Integer)
    upcoming_shows = db.relationship('Show', backref='parent_venue_upcoming', lazy=True, collection_class=list, cascade='save-update')
    upcoming_shows_count = db.Column(db.Integer)

    def __repr__(self):
      return f'<Venue ID: {self.id}, Venue name: {self.name}>'


    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), nullable=False)  #array of strings
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120), nullable=True)
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500)) #What type of venue are they seeking
    #past_shows = db.Column(db.ARRAY(db.Integer), nullable=False) #array of show ids -> relation with Shows table
    past_shows = db.relationship('Show', backref='parent_artist_past', lazy=True, collection_class=list, cascade='save-update')
    past_shows_count = db.Column(db.Integer)
    upcoming_shows = db.relationship('Show', backref='parent_artist_upcoming', lazy=True, collection_class=list, cascade='save-update')
    upcoming_shows_count = db.Column(db.Integer)

    def __repr__(self):
      return f'<Artist ID: {self.id}, Artist name: {self.name}>'


    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  venues = Venue.query.all()
  # Areas is a list of dictionaries, each dictionary holds the entires: city, state, venues(array)
  areas = [] 
  for v in venues:
    # Find the index of the area that matches this venue from areas list:
    area_not_found = True
    for a in areas:
      if a["city"] == v.city and a["state"] == v.state:
        a["venues"].append(v)
        area_not_found = False
    
    if area_not_found:
      new_area = {
                    "city": v.city,
                    "state": v.state,
                    "venues": [v]
                  }
      areas.append(new_area)
  print(areas)
  return render_template('pages/venues.html', areas = areas)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response={
    "count": 1,
    "data": [{
      "id": 2,
      "name": "The Dueling Pianos Bar",
      "num_upcoming_shows": 0,
    }]
  }
  db.session.add_all(response)
  db.session.commit()
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  
  venues = Venue.query.all()

  data = list(filter(lambda d: d.id == venue_id, venues))[0]

  # Update past and upcoming show count for this venue before displaying to user
  #past shows will never become upcoming
  # upcoming shows might become past
  # so, we need to go through the upcoming shows list to find if any of them already happened in the past,
  # if so, then, move the show from the upcoming list to the past list
  # the counts are the sizes of both lists
  for show in data.upcoming_shows:
    show_time = datetime.strptime(str(show.start_time), "%Y-%m-%d %H:%M:%S")
    if datetime.now > show_time:
      data.upcoming_shows.remove(show)
      data.past_shows.add(show)
  data.past_shows_count = len(data.past_shows)
  data.upcoming_shows_count = len(data.upcoming_shows)
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try:
    form = VenueForm()
    # TODO: insert form data as a new Venue record in the db, instead
    venue = Venue(name=form.name.data, 
                  city=form.city.data, 
                  state=form.state.data, 
                  address=form.address.data, 
                  phone=form.phone.data, 
                  image_link=form.image_link.data,
                  website="www.any.com",
                  genres=form.genres.data, 
                  facebook_link=form.facebook_link.data,
                  seeking_talent=True, #form.seeking_talent.data,
                  seeking_description="" #form.seeking_description.data
                  )
  
    
    # TODO: modify data to be the data object returned from db insertion
    data = db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('Venue ' + form.name.data + ', ' + form.city.data + ' was successfully listed!')

  except:
    error = True
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    print(sys.exc_info())

  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  return render_template('pages/artists.html', artists=Artist.query.all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # # search for "band" should return "The Wild Sax Band".
  # keywords=request.form.get('search_term', '')
  # print('\nSEARCH_KEYWORDS:'+keywords)
  # query = Artist.query.filter(Artist.name.ilike(keywords))
  # '''response={
  #   "count": 1,
  #   "data": [{
  #     "id": 4,
  #     "name": "Guns N Petals",
  #     "num_upcoming_shows": 0,
  #   }]
  # }'''
  # print(query)
  # response = db.session.execute(query)

  search_query = request.form["search_term"]
  print('\nSEARCH_KEYWORDS:'+ search_query)
  query = db.session.query(
          Artist.name
      ).filter(
          and_(
              Artist.name.like("%"+search_query+"%")
          )
      ).order_by(Artist.name.asc())

  response = db.session.execute(query)

  print("SEARCH ARTIST Returned: ")
  print(response)
  return render_template('pages/search_artists.html', results=response, search_term=search_query)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  artists=Artist.query.all()
  data = list(filter(lambda d: d.id == artist_id, artists))[0]
  print(data)
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  try:
    form = ArtistForm()
    # TODO: modify data to be the data object returned from db insertion
    artist = Artist(name=form.name.data, 
                    city=form.city.data, 
                    state=form.state.data, 
                    phone=form.phone.data, 
                    image_link=form.image_link.data,
                    website="www.any.com",
                    genres=form.genres.data, 
                    facebook_link=form.facebook_link.data,
                    seeking_venue=True, #form.seeking_venue.data,
                    seeking_description="dance sing comedy" #form.seeking_description.data
                    )

    data = db.session.add(artist)
    db.session.commit()
    # on successful db insert, flash success
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('Artist ' + form.name.data + ', ' + form.city.data + ' was successfully listed!')

  except:
    error = True
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    print(sys.exc_info())

  finally:
    db.session.close()
  
  return render_template('pages/home.html')


"""
error = False
  try:
    form = VenueForm()
    # TODO: insert form data as a new Venue record in the db, instead
    venue = Venue(name=form.name.data, 
                  city=form.city.data, 
                  state=form.state.data, 
                  address=form.address.data, 
                  phone=form.phone.data, 
                  image_link=form.image_link.data,
                  website="www.any.com",
                  genres=form.genres.data, 
                  facebook_link=form.facebook_link.data,
                  seeking_talent=True, #form.seeking_talent.data,
                  seeking_description="" #form.seeking_description.data
                  )
  
    
    # TODO: modify data to be the data object returned from db insertion
    data = db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('Venue ' + form.name.data + ', ' + form.city.data + ' was successfully listed!')

  except:
    error = True
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    print(sys.exc_info())

  finally:
    db.session.close()
"""

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  # Retrieve list of shows:
  shows = Show.query.all()
  result = []
  # Set artist and venue names:
  artists = Artist.query.all()
  venues = Venue.query.all()

  for show in shows:
    x = {} # temp dictionary to hold each show's info and retrieve the names of the artist and venue in it
    x["artist_id"] = show.artist_id
    x["venue_id"] = show.venue_id
    x["start_time"] = show.start_time
    x["image_link"] = show.image_link
    x["artist_name"] = list(filter(lambda d: d.id == show.artist_id, artists))[0].name
    x["venue_name"] = list(filter(lambda d: d.id == show.venue_id, venues))[0].name
    artist_image = list(filter(lambda d: d.id == show.artist_id, artists))[0].image_link
    x["artist_image_link"] = artist_image
    result.append(x)

  print(result)

  return render_template('pages/shows.html', shows=result)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False
  try:
    form = ShowForm()
    show = Show(artist_id = form.artist_id.data,
                venue_id = form.venue_id.data,
                start_time = form.start_time.data,
                image_link = form.image_link.data)
    data = db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    error = True
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occured. Could not add the show.')
    print(sys.exc_info())
  finally:
    db.session.close()
  return render_template('pages/home.html')    


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
