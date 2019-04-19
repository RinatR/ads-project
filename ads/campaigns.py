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
	    # db = get_db()
	    # campaigns = db.execute(
	    #     'SELECT campaign_id, campaign_name, campaign_author, u.fname, u.lname,' 
	    #     'start_date, finish_date, campaign_is_active'
	    #     ' FROM campaigns c JOIN users u ON c.campaign_author = u.user_id '
	    #     'WHERE user_id=' + str(g.user['user_id']) + ' AND campaign_is_active=1 LIMIT 10'      
	    # ).fetchall()
	    
	    return render_template('campaigns/index.html')
 
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
@bp.route('/all/rows_count', methods=('GET', "POST"))
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


@bp.route('/all/<int:page>', methods=('GET', "POST"))
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
        statsList.append(campaigns_dict)

    response = jsonify(statsList)

    return response

@bp.route('/<int:id>/campaign_stats', methods=('GET',))
@login_required
def show_stats(id):
    return render_template('campaigns/statistics.html') 


@bp.route('/<int:campaign_id>/stats', methods=('GET',))
@login_required
def get_campaign_stats(campaign_id):
    '''  
    метод используется для получения статистики рекламной кампании из БД
    id  - идентификатор кре
    в ответ возвращаем json со статистикой рекламной кампании
    также считаем возвращаем итоговую сумму по полям: bids, nurls, impressions, 
    clicks, spent и среднее значение поля ctr
    '''
    error = None
    flag = is_campaign_exist(campaign_id)
    if flag == True:    
        db = get_db()
        
       
        stats = db.execute('SELECT date, SUM(bids), SUM(impressions), SUM(clicks), SUM(nurls),SUM(spent) FROM statistics WHERE banner_id IN (SELECT banner_id  FROM html_banners WHERE banner_parent_campaign_id ='+ str(campaign_id)+')' + ' GROUP BY date ').fetchall()                
        statsList = [] 
        sum_bids = []
        sum_nurls = []
        sum_imp = []
        sum_clicks = []
        sum_spent = [] 
        avg_ctr = []            
    
        for camp in stats:
           
            campaigns_dict = {}
            campaigns_dict['date'] = camp[0]
            campaigns_dict['bids'] = camp[1] 
            sum_bids.append(camp[1])
            campaigns_dict['impressions'] = camp[2] 
            sum_imp.append(camp[2]) 
            campaigns_dict['clicks'] = camp[3]
            sum_clicks.append(camp[3])    
            campaigns_dict['nurls'] = camp[4]
            sum_nurls.append(camp[4])
            campaigns_dict['spent'] = round(camp[5],2)
            sum_spent.append(campaigns_dict['spent'])
            campaigns_dict['ctr'] = round((campaigns_dict['clicks'] / campaigns_dict['impressions']) * 100,2);  
            avg_ctr.append(campaigns_dict['ctr'])          
            statsList.append(campaigns_dict)

        columnSum = {
            'bid_sum': sum(sum_bids),
            'nurl_sum': sum(sum_nurls),
            'imp_sum': sum(sum_imp),
            'click_sum': sum(sum_clicks),
            'spent_sum': round(sum(sum_spent)),
            'avg_ctr': round(sum(avg_ctr)/len(avg_ctr),2)
        }    
        statsList.append(columnSum)
        response = jsonify(statsList)
        return response     
    else:
        error = 'Campaign is not exists.'
        flash(error,"error")
        return redirect(url_for('campaigns.index'))


def is_campaign_exist(id):
    db = get_db()
    campaign_id = db.execute('SELECT campaign_id FROM  campaigns WHERE campaign_id=?', (id,)).fetchone()

    if campaign_id != None:
        return True
    else:
        return False


  



