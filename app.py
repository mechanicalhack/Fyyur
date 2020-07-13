# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app, session_options={

    'expire_on_commit': False

})
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Show {self.id} {self.start_time}>'


class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='venue', lazy=True)

    def __repr__(self):
        return f'<Venue {self.id} {self.name}>'


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
        return f'<Artist {self.id} {self.name}>'


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

    data = []
    all_venues = Venue.query.order_by(Venue.city, Venue.state).all()

    oldCity = ''
    i = -1
    for venue in all_venues:
        if venue.city != oldCity:
            i += 1
            oldCity = venue.city
            data.append({
                "city": venue.city,
                "state": venue.state,
                "venues": [{
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": Show.query.filter(Show.venue_id == venue.id).filter(
                        Show.start_time >= datetime.utcnow()).count()
                }]
            })
        else:
            data[i]['venues'].append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": Show.query.filter(Show.venue_id == venue.id).filter(
                    Show.start_time >= datetime.utcnow()).count()
            })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    body = {}
    data = []
    count = 0

    name = request.form.get('search_term')

    venue_results = Venue.query.filter(Venue.name.ilike('%' + name + '%')).all()

    for venue in venue_results:
        count += 1
        dataToAdd = {}
        dataToAdd['id'] = venue.id
        dataToAdd['name'] = venue.name
        dataToAdd['num_upcoming_shows'] = Show.query.filter(Show.venue_id == venue.id).filter(
            Show.start_time >= datetime.utcnow()).count()
        data.append(dataToAdd)

    body['count'] = count
    body['data'] = data
    return render_template('pages/search_venues.html', results=body, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    dataReceived = Venue.query.get(venue_id)

    venue_data = {
        'id': dataReceived.id,
        'name': dataReceived.name,
        'city': dataReceived.city,
        'state': dataReceived.state,
        'address': dataReceived.address,
        'phone': dataReceived.phone,
        'genres': dataReceived.genres,
        'image_link': dataReceived.image_link,
        'website': dataReceived.website,
        'facebook_link': dataReceived.facebook_link,
        'seeking_talent': dataReceived.seeking_talent,
        'seeking_description': dataReceived.seeking_description
    }

    past_shows = Show.query.filter(Show.venue_id == dataReceived.id).filter(
        Show.start_time <= datetime.utcnow()).all()
    venue_data['past_shows'] = []
    for show in past_shows:
        venue_data['past_shows'].append({
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': str(show.start_time),
        })

    upcoming_shows = Show.query.filter(Show.venue_id == venue_data['id']).filter(
        Show.start_time >= datetime.utcnow()).all()
    venue_data['upcoming_shows'] = []
    for show in upcoming_shows:
        venue_data['upcoming_shows'].append({
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': str(show.start_time),
        })

    venue_data['past_shows_count'] = Show.query.filter(Show.venue_id == venue_data['id']).filter(
        Show.start_time <= datetime.utcnow()).count()
    venue_data['upcoming_shows_count'] = Show.query.filter(Show.venue_id == venue_data['id']).filter(
        Show.start_time >= datetime.utcnow()).count()

    return render_template('pages/show_venue.html', venue=venue_data)


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
        new_venue = Venue(name=request.form['name'],
                          city=request.form['city'],
                          state=request.form['state'],
                          address=request.form['address'],
                          phone=request.form['phone'],
                          genres=request.form.getlist('genres'),
                          facebook_link=request.form['facebook_link'])

        db.session.add(new_venue)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())

    finally:
        db.session.close()

    if error:
        abort(400)
        flash('An error occurred. Venue ' + new_venue.name + ' could not be listed.')
    else:
        flash('Venue ' + new_venue.name + ' was successfully listed!')

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    error = False
    # try:
    # show_to_delete = Show.query.filter_by(venue_id=venue_id)
    # db.session.delete(show_to_delete)
    # db.session.commit()
    # venue_to_delete = Venue.query.get(venue_id)
    # db.session.delete(venue_to_delete)
    # db.session.commit()
    # except:
    #     db.session.rollback()
    #     error = True
    # finally:
    #     db.session.close()
    # if error:
    #     flash('An error occurred. Venue ' + venue_to_delete.name + ' could not be deleted.')
    #     abort(500)
    # else:
    #     flash('Venue ' + venue_to_delete.name + ' was successfully deleted!')

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
    body = {}
    data = []
    count = 0

    name = request.form.get('search_term')
    artist_results = Artist.query.filter(Artist.name.ilike('%' + name + '%')).all()

    for artist in artist_results:
        count += 1
        dataToAdd = {}
        dataToAdd['id'] = artist.id
        dataToAdd['name'] = artist.name
        dataToAdd['num_upcoming_shows'] = 0
        data.append(dataToAdd)

    body['count'] = count
    body['data'] = data

    return render_template('pages/search_artists.html', results=body, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    dataReceived = Artist.query.get(artist_id)

    artist_data = {
        'id': dataReceived.id,
        'name': dataReceived.name,
        'city': dataReceived.city,
        'state': dataReceived.state,
        'phone': dataReceived.phone,
        'genres': dataReceived.genres,
        'image_link': dataReceived.image_link,
        'website': dataReceived.website,
        'facebook_link': dataReceived.facebook_link,
        'seeking_venue': dataReceived.seeking_venue,
        'seeking_description': dataReceived.seeking_description
    }

    past_shows = Show.query.filter(Show.artist_id == artist_data['id']).filter(
        Show.start_time <= datetime.utcnow()).all()
    artist_data['past_shows'] = []
    for show in past_shows:
        artist_data['past_shows'].append({
            'venue_id': show.venue_id,
            'venue_name': show.venue.name,
            'venue_image_link': show.venue.image_link,
            'start_time': str(show.start_time),
        })

    upcoming_shows = Show.query.filter(Show.artist_id == artist_data['id']).filter(
        Show.start_time >= datetime.utcnow()).all()
    artist_data['upcoming_shows'] = []
    for show in upcoming_shows:
        artist_data['upcoming_shows'].append({
            'venue_id': show.venue_id,
            'venue_name': show.venue.name,
            'venue_image_link': show.venue.image_link,
            'start_time': str(show.start_time),
        })

    artist_data['past_shows_count'] = Show.query.filter(Show.artist_id == artist_data['id']).filter(
        Show.start_time <= datetime.utcnow()).count()
    artist_data['upcoming_shows_count'] = Show.query.filter(Show.artist_id == artist_data['id']).filter(
        Show.start_time >= datetime.utcnow()).count()

    return render_template('pages/show_artist.html', artist=artist_data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

    artist = Artist.query.filter_by(id=artist_id).first_or_404()
    form = ArtistForm(obj=artist)

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

    error = False
    try:
        artist_to_update = Artist.query.get(artist_id)
        artist_to_update.name = request.form['name']
        artist_to_update.city = request.form['city']
        artist_to_update.state = request.form['state']
        artist_to_update.phone = request.form['phone']
        artist_to_update.genres = request.form.getlist('genres')
        artist_to_update.facebook_link = request.form['facebook_link']
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        abort(500)
        flash('An error occurred. Artist ' + artist_to_update.name + ' could not be updated.')
    else:
        flash('Venue ' + artist_to_update.name + ' was successfully Updated!')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

    venue = Venue.query.filter_by(id=venue_id).first_or_404()
    form = VenueForm(obj=venue)

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

    error = False
    try:
        venue_to_update = Venue.query.get(venue_id)
        venue_to_update.name = request.form['name']
        venue_to_update.city = request.form['city']
        venue_to_update.state = request.form['state']
        venue_to_update.address = request.form['address']
        venue_to_update.phone = request.form['phone']
        venue_to_update.genres = request.form.getlist('genres')
        venue_to_update.facebook_link = request.form['facebook_link']
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        abort(500)
        flash('An error occurred. Artist ' + venue_to_update.name + ' could not be updated.')
    else:
        flash('Venue ' + venue_to_update.name + ' was successfully Updated!')

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False

    try:
        new_artist = Artist(name=request.form['name'],
                            city=request.form['city'],
                            state=request.form['state'],
                            phone=request.form['phone'],
                            genres=request.form.getlist('genres'),
                            facebook_link=request.form['facebook_link'])

        db.session.add(new_artist)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())

    finally:
        db.session.close()

    if error:
        abort(400)
        flash('An error occurred. Artist ' + new_artist.name + ' could not be listed.')
    else:
        flash('Artist ' + new_artist.name + ' was successfully listed!')

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows

    data = []
    shows = Show.query.all()

    for show in shows:
        artObj = {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": str(show.start_time)
        }
        data.append(artObj)

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():

    error = False

    try:
        new_show = Show(artist_id=request.form['artist_id'],
                        venue_id=request.form['venue_id'],
                        start_time=request.form['start_time'])

        db.session.add(new_show)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())

    finally:
        db.session.close()

    if error:
        abort(400)
        flash('An error occurred. Show could not be listed.')
    else:
        flash('Show was successfully listed!')

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

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
