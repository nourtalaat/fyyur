#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
from sys import exc_info

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['DEBUG'] = True
app.config['ENV'] = 'development'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# OK TODO: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:postgres@localhost:5432/fyyur'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking = db.Column(db.Boolean, nullable=False, default=True)
    seeking_desc = db.Column(db.String())
    website = db.Column(db.String())
    genres = db.Column(db.String())
    shows = db.relationship('Show', backref='venue', cascade="all, delete")

    def __repr__(self):
      return f"<Venue {self.id}, {self.name}, {self.city}>"

    # OK TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking = db.Column(db.Boolean, nullable=False, default=True)
    seeking_desc = db.Column(db.String())
    website = db.Column(db.String())
    shows = db.relationship('Show', backref='artist', cascade="all, delete")

    # OK TODO: implement any missing fields, as a database migration using Flask-Migrate

# OK TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
  __tablename__ = 'shows'

  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('artists.id', ondelete='cascade'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('venues.id', ondelete='cascade'), nullable=False)
  dt = db.Column(db.DateTime(), nullable=False)


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
  # OK TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  
  rawvenues = db.session.query(Venue).order_by(Venue.city).all()
  # logic to maintain the data structure
  venues = []
  for rawvenue in rawvenues:
    venue = {
      'city': rawvenue.city,
      'state': rawvenue.state,
      'id': rawvenue.id,
      'name': rawvenue.name,
      'num_upcoming_shows': len(rawvenue.shows)
    }
    if len(venues) == 0:
      venues.append(
        {
          'city': venue['city'],
          'state': venue['state'],
          'venues': []
        }
      )
      venues[0]['venues'].append(
        {
          'id': venue['id'],
          'name': venue['name'],
          'num_upcoming_shows': venue['num_upcoming_shows']
        }
      )
    else:
      create = False
      for vc in venues:
        if vc['city'] == venue['city']:
          create = True
          vc['venues'].append(
            {
              'id': venue['id'],
              'name': venue['name'],
              'num_upcoming_shows': venue['num_upcoming_shows']
            }
          )
      if not create:
        venues.append(
          {
            'city': venue['city'],
            'state': venue['state'],
            'venues': []
          }
        )
        vc = venues[len(venues)-1]
        vc['venues'].append(
          {
            'id': venue['id'],
            'name': venue['name'],
            'num_upcoming_shows': venue['num_upcoming_shows']
          }
        )

  
  return render_template('pages/venues.html', areas=venues)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  
  # .lower() on both the search term and the DB retrieved name to ensure the search is case-insensitive
  squery = request.form.get('search_term').lower()
  venues = Venue.query.all()
  response = {
    'count': 0,
    'data': []
  }
  for venue in venues:
    if squery in venue.name.lower():
      response['count'] += 1
      response['data'].append(
        {
          'id': venue.id,
          'name': venue.name,
          'num_upcoming_shows': len(venue.shows)
        }
      )
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>', methods=['GET'])
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  # try:
  venue = Venue.query.get(venue_id)
  shows = {
    'past_shows': [],
    'upcoming_shows': []
  }
  for show in venue.shows:
    artist = Artist.query.get(show.artist_id)
    key = ''
    if show.dt > datetime.now():
      key = 'upcoming_shows'
    else:
      key = 'past_shows'
    shows[key].append(
      {
        'artist_id': artist.id,
        'artist_name': artist.name,
        'artist_image_link': artist.image_link,
        'start_time': str(show.dt)
      }
    )
  genres = venue.genres[1:len(venue.genres)-1].split(',')

  response = {
    "id": venue.id,
    "name": venue.name,
    "genres": genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.city,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking,
    "seeking_description": venue.seeking_desc,
    "image_link": venue.image_link,
    "past_shows": shows['past_shows'],
    "upcoming_shows": shows['upcoming_shows'],
    "past_shows_count": len(shows['past_shows']),
    "upcoming_shows_count": len(shows['upcoming_shows']),
  }
  return render_template('pages/show_venue.html', venue=response)
  # except:
  #   flash(f"Venue with ID {venue_id} does not exist")
  #   return redirect(url_for('venues'))

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    data = request.form
    # data validation logic
    if data['city'].isalpha() and data['state'].isalpha() and data['phone'].isnumeric():
      facebook_link = None
      # quick solution instead of using regex
      if "www.facebook.com/" in data['facebook_link']:
        facebook_link = data['facebook_link']
      else:
        facebook_link = None
      venue = Venue(name=data['name'], city=data['city'], state=data['state'], address=data['address'], phone=data['phone'],
      genres=request.form.getlist('genres'), facebook_link=facebook_link, seeking=True, seeking_desc='Currently seeking talented performers!')
      db.session.add(venue)
      db.session.commit()
      flash('Venue ' + data['name'] + ' was successfully listed!')
    else:
      raise Exception('invalid data')
  except:
    db.session.rollback()
    print(exc_info())
    flash('An error occurred. Venue could not be listed.')
  finally:
    db.session.close()
    return render_template('pages/home.html')

  # OK TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  # on successful db insert, flash success
  # OK TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/

@app.route('/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # OK TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  success = False
  try:
    count = Venue.query.filter_by(id=venue_id).delete()
    if count == 1:
      success = True
      db.session.commit()
      flash(f'Venue with ID {venue_id} deleted successfully!')
      #return redirect(url_for('venues'))
  except:
    flash('Venue could not be deleted')
    db.session.rollback()
    #return redirect(url_for('show_venue', venue_id=venue_id))
  finally:
    db.session.close()
    return json.dumps({'success':success}), 200, {'ContentType':'application/json'} 

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # OK TODO: replace with real data returned from querying the database
  rawartists = Artist.query.all()
  data = []
  for rawartist in rawartists:
    data.append(
      {
        'id': rawartist.id,
        'name': rawartist.name
      }
    )
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # OK TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  
  # .lower() on both the search term and the DB retrieved name to ensure the search is case-insensitive
  squery = request.form.get('search_term').lower()
  artists = Artist.query.all()
  response = {
    'count': 0,
    'data': []
  }
  for artist in artists:
    if squery in artist.name.lower():
      response['count'] += 1
      response['data'].append(
        {
          'id': artist.id,
          'name': artist.name,
          'num_upcoming_shows': len(artist.shows)
        }
      )
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # OK TODO: replace with real venue data from the venues table, using venue_id
  try:
    artist = Artist.query.get(artist_id)
    shows = {
      'past_shows': [],
      'upcoming_shows': []
    }
    for show in artist.shows:
      venue = Venue.query.get(show.venue_id)
      key = ''
      if show.dt > datetime.now():
        key = 'upcoming_shows'
      else:
        key = 'past_shows'
      shows[key].append(
        {
          'venue_id': venue.id,
          'venue_name': venue.name,
          'venue_image_link': venue.image_link,
          'start_time': str(show.dt)
        }
      )
    genres = artist.genres[1:len(artist.genres)-1].split(',')

    response = {
      "id": artist.id,
      "name": artist.name,
      "genres": genres,
      "city": artist.city,
      "state": artist.city,
      "phone": artist.phone,
      "website": artist.website,
      "facebook_link": artist.facebook_link,
      "seeking_talent": artist.seeking,
      "seeking_description": artist.seeking_desc,
      "image_link": artist.image_link,
      "past_shows": shows['past_shows'],
      "upcoming_shows": shows['upcoming_shows'],
      "past_shows_count": len(shows['past_shows']),
      "upcoming_shows_count": len(shows['upcoming_shows']),
    }
    
    return render_template('pages/show_artist.html', artist=response)
  except:
    flash(f'Artist with ID {artist_id} does not exist')
    return redirect(url_for('artists'))

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # TODO: populate form with fields from artist with ID <artist_id>
  form = ArtistForm()
  try:
    data = Artist.query.get(artist_id)
    artist = {
      'id': data.id,
      'name': data.name,
      'genres': data.genres,
      'city': data.city,
      'state': data.state,
      'phone': data.phone,
      'website': data.website,
      'facebook_link': data.facebook_link,
      'seeking_venue': data.seeking,
      'seeking_description': data.seeking_desc,
      'image_link': data.image_link
    }
    return render_template('forms/edit_artist.html', form=form, artist=artist)
  except:
    flash(f'Artist with ID {artist_id} was not found.')
    return redirect(url_for('artists'))

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    data = request.form
    genres = request.form.getlist('genres')
    artist = Artist.query.get(artist_id)
    # data validation logic
    if data['city'].isalpha() and data['state'].isalpha() and data['phone'].isnumeric():
      artist.name = data['name']
      artist.city = data['city']
      artist.state = data['state']
      artist.phone = data['phone']
    else:
      raise Exception('invalid data')
    artist.genres = genres
    # quick solution instead of using regex
    if "www.facebook.com/" in data['facebook_link']:
      artist.facebook_link = data['facebook_link']
    else:
      artist.facebook_link = None
    db.session.commit()
    flash(f'Artist {artist.name} has been updated successfuly!')
  except:
    flash('Artist could not be updated')
    db.session.rollback()

  db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # OK TODO: populate form with values from venue with ID <venue_id>
  form = VenueForm()
  try:
    data = Venue.query.get(venue_id)
    venue = {
      'id': data.id,
      'name': data.name,
      'genres': data.genres,
      'address': data.address,
      'city': data.city,
      'state': data.state,
      'phone': data.phone,
      'website': data.website,
      'facebook_link': data.facebook_link,
      'seeking_talent': data.seeking,
      'seeking_description': data.seeking_desc,
      'image_link': data.image_link
    }
    return render_template('forms/edit_venue.html', form=form, venue=venue)
  except:
    flash(f'Venue with ID {venue_id} was not found.')
    return redirect(url_for('venues'))

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # OK TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  try:
    data = request.form
    genres = request.form.getlist('genres')
    venue = Venue.query.get(venue_id)
    # data validation logic
    if data['city'].isalpha() and data['state'].isalpha() and data['phone'].isnumeric():
      venue.name = data['name']
      venue.city = data['city']
      venue.state = data['state']
      venue.address = data['address']
      venue.phone = data['phone']
      venue.genres = genres
    else:
      raise Exception('invalid data')
    # quick solution instead of using regex
    if "www.facebook.com/" in data['facebook_link']:
      venue.facebook_link = data['facebook_link']
    else:
      venue.facebook_link = None
    flash(f'Venue {venue.name} has been updated successfuly!')
    db.session.commit()
  except:
    flash('Venue could not be updated')
    db.session.rollback()

  db.session.close()
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
  # OK TODO: insert form data as a new Venue record in the db, instead
  # OK TODO: modify data to be the data object returned from db insertion
  try:
    data = request.form
    genres = request.form.getlist('genres')
    # data validation logic
    if data['city'].isalpha() and data['state'].isalpha() and data['phone'].isnumeric():
      facebook_link = None
      # quick solution instead of using regex
      if "www.facebook.com/" in data['facebook_link']:
        facebook_link = data['facebook_link']
      else:
        facebook_link = None
      artist = Artist(name=data['name'], city=data['city'], state=data['state'], phone=data['phone'], genres=genres, facebook_link=facebook_link)
      # on successful db insert, flash success
      # OK TODO: on unsuccessful db insert, flash an error instead.
      # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
      db.session.add(artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    else:
      raise Exception('invalid data')
  except:
    flash('Artist could not be created')
    db.session.rollback()
  db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # OK TODO: replace with real shows data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  shows = Show.query.all()
  for show in shows:
    venue = Venue.query.get(show.venue_id)
    artist = Artist.query.get(show.artist_id)
    data.append({
      'venue_id': venue.id,
      'venue_name': venue.name,
      'artist_id': artist.id,
      'artist_name': artist.name,
      'artist_image_link': artist.image_link,
      'start_time': str(show.dt)
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # OK TODO: insert form data as a new Show record in the db, instead
  try:
    data = request.form
    # these 2 queries are used to check if the IDs are valid
    artist = Artist.query.get(data['artist_id'])
    venue = Venue.query.get(data['venue_id'])
    show = Show(artist_id=data['artist_id'], venue_id=data['venue_id'], dt= data['start_time'])
    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    # OK TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    db.session.rollback()
    flash('An error has occured, show was not created')
  finally:
    db.session.close()
    return render_template('pages/home.html')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/

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
