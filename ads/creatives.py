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


bp_cr = Blueprint('creatives', __name__, url_prefix='/creatives')

def get_creative(creative_id):
	creative = get_db().execute(
        'SELECT banner_id, banner_name, banner_width, banner_height,' 
        'banner_html, banner_link, banner_status, banner_parent_campaign_id'
        ' FROM html_banners  WHERE banner_id = ?',(creative_id,)).fetchone()

	return creative


@bp_cr.route('/<int:id>/add_creative', methods=('GET', 'POST'))
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
		    	'INSERT INTO html_banners (banner_name, banner_status,' 
		    	'banner_width, banner_height, banner_html, banner_link,' 
		    	'banner_parent_campaign_id)'
		    	' VALUES (?, ?, ?, ?, ?, ?, ?)', 
		    	(creative_name, 0,creative_width, creative_height, 
		    		creative_html, creative_link, id))
			db.commit()
			create_html_file(creative_name, creative_html)
			return redirect(url_for('campaigns.show', id=id))

	return render_template('creatives/add_creative.html')


def create_html_file(file_name, file_content):
	filepath =   os.getcwd() + "/" + "ads" + current_app.static_url_path
	filename = filepath + "/" + file_name + ".html"
	with open(filename, 'w') as f_obj:
		f_obj.write(file_content)

@bp_cr.route('/<int:id>/show_creative', methods=('GET', "POST"))
@login_required
def show_creative(id):
	creative = get_creative(id)
	file_path = current_app.static_url_path + "/" + creative['banner_name'] + ".html"
	
	return render_template('creatives/show_creative.html', creative=creative, 
		file_path=file_path)


@bp_cr.route('/<int:id>/update_creative', methods=('GET', 'POST'))
@login_required
def update(id):
    creative = get_creative(id)    
    if request.method == 'POST':
        creative_name = request.form['creative_name']
        creative_width = request.form['creative_width']        
        creative_height = request.form['creative_height']
        creative_html = request.form['creative_html'] 
        creative_link = request.form['creative_link']    	
        error = None

        if not creative_name:
            error = 'Creative name is required.'
        elif not creative_width:
            error = 'Creative width is required.'
        elif not creative_height:
            error = 'Creative height is required.'
        elif not creative_html:
        	error = 'Creative HTMl code is required.'
        elif not creative_link:
        	error = 'Creative click link is required.'

        if error is not None:
            flash(error, 'error')
        else:
            db = get_db()
            db.execute(
                'UPDATE html_banners SET banner_name = ?, banner_width = ?,' 
                'banner_height = ?, banner_html = ?, banner_link = ?'
                ' WHERE banner_id = ?',
                (creative_name, creative_width,creative_height, creative_html, creative_link, id)
            )
            flash("The creative was edit successfully")
            db.commit()            
            return redirect(url_for('campaigns.show', id=creative['banner_parent_campaign_id']))

    return render_template('creatives/update_creative.html', creative=creative)

@bp_cr.route('<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
	creative = get_creative(id)
	db = get_db()
	db.execute('DELETE FROM html_banners WHERE banner_id = ?', (id,))
	db.commit()

	return redirect(url_for('campaigns.show', id=creative['banner_parent_campaign_id']))

@bp_cr.route('/<int:id>/stats_creative', methods=('GET',))
@login_required
def show_stats(id):
	return render_template('creatives/statistics.html')	


@bp_cr.route('/<int:id>/get_stats_creative', methods=('GET',))
@login_required
def get_stats(id):
	'''  
	метод используется для получения статистики креатива из БД
	id  - идентификатор креатива
	в ответ возвращаем json со статистикой 
	также считаем возвращаем итоговую сумму по полям: bids, nurls, impressions, 
	clicks, spent и среднее значение поля ctr
	'''
	error = None
	flag = is_creative_exist(id)
	if flag == True:	
		db = get_db()
		
		stats = db.execute('SELECT * FROM  statistics WHERE banner_id=?', (id,)).fetchall()		
				
		statsList = []    
		sum_bids = []
		sum_nurls = []
		sum_imp = []
		sum_clicks = []
		sum_spent = [] 
		avg_ctr = []      
    
		for camp in stats:
	       
			campaigns_dict = {}
			campaigns_dict['banner_id'] = camp[0]
			campaigns_dict['bids'] = camp[1]   
			sum_bids.append(camp[1])     
			campaigns_dict['nurls'] = camp[2] 
			sum_nurls.append(camp[2])
			campaigns_dict['impressions'] = camp[3]
			sum_imp.append(camp[3])
			campaigns_dict['clicks'] = camp[4]
			sum_clicks.append(camp[4])
			campaigns_dict['spent'] = camp[5]
			sum_spent.append(camp[5])
			campaigns_dict['date'] = camp[6]
			campaigns_dict['ctr'] = round((campaigns_dict['clicks'] / campaigns_dict['impressions']) * 100,2);
			avg_ctr.append(campaigns_dict['ctr'])
			statsList.append(campaigns_dict)
	    
		columnSum = {
		    'bid_sum': sum(sum_bids),
		    'nurl_sum': sum(sum_nurls),
		    'imp_sum': sum(sum_imp),
		    'click_sum': sum(sum_clicks),
		    'spent_sum': sum(sum_spent),
		    'avg_ctr': round(sum(avg_ctr)/len(avg_ctr),2)
		}
		statsList.append(columnSum)

		response = jsonify(statsList)
		return response		
	else:
		error = 'Creative is not exists.'
		flash(error,"error")
		return redirect(url_for('campaigns.index'))



def is_creative_exist(id):
	db = get_db()
	creative_id = db.execute('SELECT banner_id FROM  statistics WHERE banner_id=?', (id,)).fetchone()

	if creative_id != None:
		return True
	else:
		return False

