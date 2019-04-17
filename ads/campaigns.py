from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from flask import current_app
from ads.auth import login_required
from ads.db import get_db
import datetime
import os
from flask import jsonify
from sqlite3 import Error

bp = Blueprint('campaigns', __name__, url_prefix='/campaigns')


@bp.route('/')
def index():	
	    db = get_db()
	    campaigns = db.execute(
	        'SELECT campaign_id, campaign_name, campaign_author, u.fname, u.lname,' 
	        'start_date, finish_date, campaign_is_active'
	        ' FROM campaigns c JOIN users u ON c.campaign_author = u.user_id '
	        'WHERE user_id=' + str(g.user['user_id']) + ' AND campaign_is_active=1 LIMIT 10'      
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
                'INSERT INTO campaigns (campaign_name, start_date, finish_date,' 
                'campaign_author, campaign_is_active)'
                ' VALUES (?, ?, ?, ?, ?)',
                (campaign_name, start_date, finish_date, g.user['user_id'], 1)
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
        'SELECT campaign_id, campaign_name, start_date, finish_date,' 
        'campaign_author, campaign_is_active, u.user_id, u.fname, u.lname'
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
                'UPDATE campaigns SET campaign_name = ?, start_date = ?,' 
                'finish_date = ?'
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
    # db.execute('DELETE FROM campaigns WHERE campaign_id = ?', (id,))
    db.execute('UPDATE campaigns SET campaign_is_active=0' + 
    	' WHERE campaign_id = ?', (id,))
    db.commit()
    return redirect(url_for('campaigns.index'))

def get_creatives(campaign_id):
	creatives = get_db().execute(
        'SELECT banner_id, banner_name, banner_width, banner_height, '
        'banner_link, banner_status, banner_parent_campaign_id'
        ' FROM html_banners  WHERE banner_parent_campaign_id = ?',
        (campaign_id,)).fetchall()

	return creatives

@bp.route('/<int:id>/show', methods=('GET', "POST"))
@login_required
def show(id):
	campaign = get_campaign(id)
	creatives = get_creatives(id)
	if creatives is not None:
		return render_template('campaigns/show.html', 
			campaign=campaign, creatives=creatives)
	else:
		return render_template('campaigns/show.html', campaign=campaign)

# получаем количество всех рекламных кампаний для конкретного юзера.
# полученное число используется для пагинации
@bp.route('/stats/rows_count', methods=('GET', "POST"))
def get_rows_count():
	db = get_db()
	try:	
		rows_count = db.execute(
			'SELECT COUNT(*) count_rows FROM campaigns c JOIN users u '
			'ON c.campaign_author = u.user_id WHERE user_id=' 
			+ str(g.user['user_id']) +  ' AND campaign_is_active=1'
			).fetchone()

	except Error as e:
		return e
	
	return str(rows_count[0])


@bp.route('/stats/<int:page>', methods=('GET', "POST"))
def get_stats(page):
	
	offset = page * 10
	offset = str(offset)
	db = get_db()
	campaigns = db.execute(
		'SELECT campaign_id, campaign_name, campaign_author, u.fname, u.lname,' 
    	'start_date, finish_date, campaign_is_active'
        ' FROM campaigns c JOIN users u ON c.campaign_author = u.user_id '
        'WHERE user_id=' + str(g.user['user_id']) + ' AND campaign_is_active=1 LIMIT 10 OFFSET ' + offset 
		).fetchall()

	statsList = []
	for camp in campaigns:
		campaigns_dict = {}
		campaigns_dict['id'] = camp[0]
		campaigns_dict['camp_name'] = camp[1]
		campaigns_dict['camp_author'] = camp[3] + " " + camp[4]
		campaigns_dict['start_date'] = camp[5]
		campaigns_dict['finish_date'] = camp[6]
		campaigns_dict['camp_status'] = camp[7]
		# campaigns_dict['rows-count'] = rows_count
		statsList.append(campaigns_dict)

	response = jsonify(statsList)

	return response


  



	
