from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from ads.auth import login_required
from ads.db import get_db
import datetime

bp = Blueprint('campaigns', __name__)

@bp.route('/')
def index():
    db = get_db()
    campaigns = db.execute(
        'SELECT campaign_id, campaign_name, campaign_author, u.fname, u.lname, start_date, finish_date, campaign_is_active'
        ' FROM campaigns c JOIN users u ON c.campaign_author = u.user_id WHERE user_id=' + str(g.user['user_id'])        
    ).fetchall()
    return render_template('campaigns/index.html', campaigns=campaigns)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        campaign_name = request.form['campaign_name']
        start_date = request.form['start_date']        
        finish_date = request.form['finish_date']
        date_is_valid = validate_date(start_date, finish_date)        
        error = None

        if not campaign_name:
            error = 'Campaign name is required.'
        elif not start_date:
        	error = 'Start date is required'
        elif not finish_date:
        	error = 'Finish date is required'
        elif not date_is_valid:
        	error = 'Finish date can\'t be earlier that start date.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO campaigns (campaign_name, start_date, finish_date, campaign_author, campaign_is_active)'
                ' VALUES (?, ?, ?, ?, ?)',
                (campaign_name, start_date, finish_date, g.user['user_id'], 0)
            )
            db.commit()
            return redirect(url_for('campaigns.index'))

    return render_template('campaigns/create.html')

def validate_date(start_date, finish_date):	
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    start_date = start_date.strftime('%Y-%m-%d')    
    finish_date = datetime.datetime.strptime(finish_date,"%Y-%m-%d")
    finish_date = finish_date.strftime('%Y-%m-%d')

    if finish_date < start_date:
    	return False

    return True;

def get_campaign(campaign_id, check_author = True):
	campaign = get_db().execute(
        'SELECT campaign_id, campaign_name, start_date, finish_date, campaign_author, campaign_is_active, u.user_id, u.fname, u.lname'
        ' FROM campaigns c JOIN users u ON c.campaign_author = u.user_id'
        ' WHERE campaign_id = ?',(campaign_id,)).fetchone()

	if campaign is None:
		abort(404, "Campaign id {0} doesn't exist.".format(d))

	if check_author and campaign['campaign_author'] != g.user['user_id']:
		abort(403)

	return campaign

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    campaign = get_campaign(id)    
    if request.method == 'POST':
        campaign_name = request.form['campaign_name']
        start_date = request.form['start_date']        
        finish_date = request.form['finish_date']
        date_is_valid = validate_date(start_date, finish_date)     	
        error = None

        if not campaign_name:
            error = 'Campaign name is required.'
        elif not start_date:
            error = 'Start date is required.'
        elif not finish_date:
            error = 'Finish date is required.'
        elif not date_is_valid:
        	error = 'Finish date can\'t be earlier that start date.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE campaigns SET campaign_name = ?, start_date = ?, finish_date = ?'
                ' WHERE campaign_id = ?',
                (campaign_name, start_date,finish_date, id)
            )
            db.commit()
            return redirect(url_for('campaigns.index'))

    return render_template('campaigns/update.html', campaign=campaign)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_campaign(id)
    db = get_db()
    db.execute('DELETE FROM campaigns WHERE campaign_id = ?', (id,))
    db.commit()
    return redirect(url_for('campaigns.index'))

@bp.route('/<int:id>/show', methods=('GET', "POST"))
@login_required
def show(id):
	campaign = get_campaign(id)
	return render_template('campaigns/show.html', campaign=campaign)

