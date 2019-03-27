from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from flask import current_app
from ads.auth import login_required
from ads.db import get_db
import datetime
import os

bp = Blueprint('campaigns', __name__, url_prefix='/campaigns')


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

def get_creatives(campaign_id):
	creatives = get_db().execute(
        'SELECT banner_id, banner_name, banner_width, banner_height, banner_html, banner_link, banner_status, banner_parent_campaign_id'
        ' FROM html_banners  WHERE banner_parent_campaign_id = ?',(campaign_id,)).fetchall()

	return creatives

def get_creative(creative_id):
	creative = get_db().execute(
        'SELECT banner_id, banner_name, banner_width, banner_height, banner_html, banner_link, banner_status, banner_parent_campaign_id'
        ' FROM html_banners  WHERE banner_id = ?',(creative_id,)).fetchone()

	return creative

@bp.route('/<int:id>/show', methods=('GET', "POST"))
@login_required
def show(id):
	campaign = get_campaign(id)
	creatives = get_creatives(id)
	if creatives is not None:
		return render_template('campaigns/show.html', campaign=campaign, creatives=creatives)
	else:
		return render_template('campaigns/show.html', campaign=campaign)


@bp.route('/<int:id>/add_creative', methods=('GET', "POST"))
@login_required
def add_creative(id):
	
	if request.method == 'POST':
		creative_name = request.form['creative_name']
		creative_width = int(request.form['creative_width'])       
		creative_height = int(request.form['creative_height'])
		creative_html = request.form['creative_html']
		creative_link = request.form['creative_link']      
		error = None

		if not creative_name:
		    error = 'Creative name is required.'
		elif not creative_width:
			error = 'Creative width is required'
		elif not creative_height:
			error = 'Creative height is required'
		elif not creative_html:
			error = 'Creative html code is required'
		elif not creative_link:
			error = 'Creative link is required'

		if error is not None:
		    flash(error)
		else:
			db = get_db()
			db.execute(
		    	'INSERT INTO html_banners (banner_name, banner_status, banner_width, banner_height, banner_html, banner_link, banner_parent_campaign_id)'
		    	' VALUES (?, ?, ?, ?, ?, ?, ?)', (creative_name, 0,creative_width, creative_height, creative_html, creative_link, id))
			db.commit()
			create_html_file(creative_name, creative_html)
			return redirect(url_for('campaigns.index'))

	return render_template('campaigns/add_creative.html')


def create_html_file(file_name, file_content):
	filepath =   os.getcwd() + "/" + "ads" + current_app.static_url_path
	filename = filepath + "/" + file_name + ".html"
	with open(filename, 'w') as f_obj:
		f_obj.write(file_content)

@bp.route('/<int:id>/show_creative', methods=('GET', "POST"))
@login_required
def show_creative(id):
	creative = get_creative(id)
	file_path = current_app.static_url_path + "/" + creative['banner_name'] + ".html"
	
	return render_template('campaigns/show_creative.html', creative=creative, file_path=file_path)
