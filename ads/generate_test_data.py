import sqlite3
from sqlite3 import Error
from faker import Faker
import datetime

 
 
def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
 
    return None
 
 
def select_all_tasks(conn):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    stats = cur.execute('SELECT * FROM  statistics WHERE banner_id=21').fetchall()     
                
    statsList = []
    
    sum_bids = []
    sum_nurls = []
    sum_imp = []
    sum_clicks = []
    sum_spent = []   
    
    
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
        statsList.append(campaigns_dict)
    
    columnSum = {
        'bid_sum': sum(sum_bids),
        'nurl_sum': sum(sum_nurls),
        'imp_sum': sum(sum_imp),
        'click_sum': sum(sum_clicks),
        'spent_sum': sum(sum_spent)
    }
    statsList.append(columnSum)
        
    print(statsList)

    


# def insert_test_data(conn):
# 	rows_count = 55
# 	while rows_count > 0:
# 		result = init_test_data()
		
# 		name = result['name']
# 		isactive = result['is_active']
# 		author = result['author']
# 		start_date = result['start_date']
# 		finish_date = result['finish_date']
# 		cur = conn.cursor()
	
		
# 		cur.execute("INSERT INTO campaigns (campaign_name, start_date, finish_date,campaign_author, campaign_is_active) VALUES (?, ?, ?, ?, ?)",(name, start_date, finish_date, author, isactive))
# 		rows_count = rows_count-1        

# def init_test_data():
# 	fake = Faker()
# 	campaign = {}
# 	campaign['name'] = fake.sentence(nb_words=6, variable_nb_words=True, ext_word_list=None)
# 	campaign['start_date'] = fake.date(pattern="%Y-%m-%d", end_datetime=None)
# 	campaign['finish_date'] = fake.date(pattern="%Y-%m-%d", end_datetime=None)
# 	campaign['author'] = 1
# 	campaign['is_active'] = 1
	
# 	return campaign

# def insert_test_data(conn):
#     rows_count = 0
#     while rows_count < 31:
#         result = init_test_data(rows_count)
        
#         banner_id = result['banner_id']
#         date = result['date']
#         bids = result['bids']
#         impressions = result['impressions']
#         nurls = result['nurls']
#         clicks = result['clicks']
#         spent = result['spent']
#         cur = conn.cursor()
    
        
#         cur.execute("INSERT INTO statistics (banner_id, date, bids, nurls,impressions, clicks,spent) VALUES (?, ?, ?, ?, ?, ?, ?)",(banner_id, date, bids, nurls, impressions, clicks, spent))
#         rows_count = rows_count+1        

# def init_test_data(item):
    
#     dates = ['2019-03-01','2019-03-02','2019-03-03','2019-03-04','2019-03-05','2019-03-06','2019-03-07','2019-03-08','2019-03-09','2019-03-10','2019-03-11',
#     '2019-03-12','2019-03-13','2019-03-14','2019-03-15','2019-03-16','2019-03-17','2019-03-18','2019-03-19','2019-03-20','2019-03-21','2019-03-22','2019-03-23',
#     '2019-03-24','2019-03-25','2019-03-26','2019-03-27','2019-03-28','2019-03-29','2019-03-30','2019-03-31']
#     fake = Faker()
#     stats = {}
#     stats['banner_id'] = 21
#     stats['date'] = dates[item]
#     stats['bids'] = fake.pyint()
#     stats['impressions'] = fake.pyint()
#     stats['nurls'] = fake.pyint()
#     stats['clicks'] = fake.pyint()
#     stats['spent'] = fake.pyfloat(left_digits=4, right_digits=2, positive=True)
    
    
    
#     return stats

 
 
def main():
    database = "/home/rinat/dev/ads-project/instance/flaskr.sqlite"
 
    # create a database connection
    conn = create_connection(database)
    with conn:
    	# insert_test_data(conn)
        select_all_tasks(conn)
        # res = init_test_data()
        # print(res)
       
 
if __name__ == '__main__':
    main()