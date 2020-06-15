from application import app
from flask import Flask,redirect,url_for,flash,render_template,request,session
from flask_mysqldb import MySQL 
import MySQLdb
import MySQLdb.cursors
import time
from datetime import datetime
import re

mysql = MySQL(app)

@app.route('/', methods=['GET', 'POST'])
def login():
	msg = ''
	if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
		username = request.form['username']
		password = request.form['password']
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM employee WHERE user_id = %s AND password = %s', (username, password,))
		account = cursor.fetchone()
		if (account):
			session['loggedin'] = True
			session['username'] = account['user_id']
			session['type'] = account['emp_type']
			return redirect(url_for('home'))
		else:
			msg = 'Incorrect username/password!'
	if 'loggedin' in session:
		return redirect(url_for('home'))
	return render_template('index.html', title='Sign In',msg = msg)

@app.route('/logout')
def logout():
	session.pop('loggedin', None)
	session.pop('username', None)
	session.pop('type', None)
	return redirect(url_for('login'))

@app.route('/home')
def home():
	if 'loggedin' in session and session['type']=='executive':
		return render_template('home1.html', username=session['username'],emp_type=session['type'])
	elif 'loggedin' in session and session['type']=='cashier':
		return render_template('home2.html', username=session['username'],emp_type=session['type'])
	return redirect(url_for('login'))


@app.route('/customer_status',methods=['GET', 'POST'])
def customer_status():
	if('loggedin' not in session):
		return redirect(url_for('login'))
	if (request.method == 'POST'):
		return redirect(url_for('customer_status'))
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute('SELECT C.customer_ssn, C.customer_id, S.message, S.last_updated,S.status FROM customer C,customer_status S WHERE C.customer_id = S.customer_id')
	values = cursor.fetchall()
	return render_template('customer_status.html',values=values)

@app.route('/create_account', methods=['GET', 'POST'])
def c_account():
	msg = ''
	if request.method == 'POST' and 'customer_id' in request.form and 'account_type' in request.form and 'amount' in request.form:
		cid = int(request.form['customer_id'])
		acc_type = str(request.form['account_type'])
		amount = int(request.form['amount'])
		last_updated = str(datetime.utcnow())
		details = 'account created successfully'
		status = int('1')
		try:
			cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			cursor.execute('SELECT count(*) FROM account WHERE customer_id = %s AND account_type = %s', (cid,acc_type))
			res = cursor.fetchone()
			if res['count(*)'] == 1:
				raise Exception('fail')
			else:
				cursor.execute('INSERT INTO account (customer_id, account_type, balance, message, last_updated, status) VALUES (%s, %s, %s, %s, %s, %s)', (cid, acc_type, amount, details, last_updated, status))
				cursor.execute('INSERT INTO transactions (customer_id, description, d_acc, amount) VALUES (%s, %s, %s, %s)', (cid, 'deposit', acc_type, amount))
				mysql.connection.commit()
				flash('Account created successfully','success')
		except Exception as e:
			print('Failed to insert into account' + str(e))
			if str(e).find('foreign key constraint fails') != -1: 
				msg = 'Customer ID does not exist'
			elif str(e) == 'fail':
				msg = 'You already have ' + acc_type + ' account'
			else:
				msg = 'Could not create account...Please try again'
	if 'loggedin' in session and session['type']=='executive':
		return render_template('create_account.html', username=session['username'],emp_type=session['type'], msg=msg)
	return redirect(url_for('login'))

@app.route('/create_customer', methods=['GET', 'POST'])
def create_customer():
	msg=""
	if request.method == 'POST' and 'InputSSN' in request.form and 'InputName' in request.form:
		details = request.form
		InputSSN = details['InputSSN']
		InputName = details['InputName']
		InputAge = details['InputAge']
		InputAge=str(InputAge)
		InputAddress1 = details['InputAddress1']
		InputAddress2 = details['InputAddress2']
		InputAddress = InputAddress1 + " " + InputAddress2
		InputCity = details['InputCity']
		InputState = details['InputState']
		mess = "customer created successfully"
		stat = "1"
		try:
			cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

			cur.execute(
				"INSERT INTO customer( customer_ssn, name, age, address, city, state) VALUES (%s, %s, %s, %s, %s, %s)",
				(InputSSN, InputName, InputAge, InputAddress, InputCity, InputState))
			timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
			cur.execute("SELECT customer_id from customer where customer_ssn=" + InputSSN)
			res = cur.fetchone()
			cust_id = res["customer_id"]
			cur.execute("INSERT INTO customer_status(customer_id, message, last_updated, status) VALUES (%s, %s, %s, %s)",
						(cust_id, mess, timestamp, stat))
			mysql.connection.commit()
			flash('Customer created successfully', 'success')
			cur.close()

		except Exception as e:
			msg = "Please enter a valid Customer SSN ID"


	if 'loggedin' in session and session['type'] == 'executive':
			return render_template('create_customer.html', username=session['username'], emp_type=session['type'],
								   msg=msg)
	return redirect(url_for('login'))


######## CUSTOMER UPDATE ########
@app.route('/update_search')
def update_search():
	if 'loggedin' in session and session['type'] == 'executive':
		return render_template('update_search.html')
	return redirect(url_for('login'))
@app.route("/update",methods=['GET','POST'])
def update():
	if(request.method=='POST' and ('SSN' in request.form or 'CUSTOMER_ID' in request.form)) :
		ssn=request.form['SSN']
		Id=request.form['CUSTOMER_ID']
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM customer WHERE customer_id = %s or customer_ssn=%s', (Id,ssn))
		details = cursor.fetchone()
		if(details is None):
			flash("Could not find an account with given details","danger")
			return redirect('/update_search')
		cursor.execute('SELECT status FROM customer_status WHERE customer_id = %s ', (details['customer_id'],))
		details2=cursor.fetchone()
		if(details2['status']!=1):
			flash("Customer no longer exists exists","danger")
			return redirect('/update_search')
	if request.method=='POST' and ('new_name' in request.form or 'new_age' in request.form or 'new_address' in request.form) :
		n_name=request.form['new_name']
		n_addr=request.form['new_address']
		n_age=request.form['new_age']
		Id=request.form['ID']
		timestamp = timestamp = datetime.utcnow()
		print(timestamp)
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute("UPDATE customer SET name = %s,address=%s,age=%s WHERE customer_id=%s",(n_name,n_addr,n_age,Id,))
		cursor.execute("UPDATE customer_status SET message=%s WHERE customer_id=%s",("customer update complete",Id,))
		cursor.execute("UPDATE customer_status SET message=%s WHERE last_updated=%s",(timestamp,Id,))
		cursor.execute("COMMIT")
		flash("Successfully Updated","success")
		return redirect(url_for('login'))
	if 'loggedin' in session and session['type']=='executive':
		return render_template("update.html",details=details)
	return redirect(url_for('login'))


	
######## ACCOUNT STATUS ####### 
@app.route('/account_status',methods=['GET','POST'])
def account_status():
	cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute("SELECT * FROM account")
	details_raw=list(cursor.fetchall())
	details=[]
	for i in details_raw:
		if(i['status']==1):
			details.append(i)
	if request.method=='POST' and 'refresh' in request.form :
		return redirect('/account_status')
	if 'loggedin' in session and session['type']=='executive':
		return render_template("account_status.html",details=details)
	return redirect(url_for('login'))
	


##### CUSTOMER SEARCH ######### 
@app.route('/customer_search')
def customer_search():
	if 'loggedin' in session and session['type']=='executive':
		return render_template('customer_search.html')
	return redirect(url_for('login'))
@app.route('/customer_detail',methods=['GET','POST'])
def customer_detail():
	if request.method=='POST' and ('SSN' in request.form or 'CUSTOMER_ID' in request.form) :
		ssn=request.form['SSN']
		Id=request.form['CUSTOMER_ID']
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM customer WHERE customer_id = %s or customer_ssn=%s', (Id,ssn))
		customer_detail1 = cursor.fetchone()
		if(customer_detail1 is None):
			flash("No user available with given SSN ID/Customer ID","danger")
			return redirect('/customer_search')
		cust_id=customer_detail1['customer_id']
		cursor.execute('SELECT * FROM customer_status WHERE customer_id = %s', (cust_id,))
		customer_detail2=cursor.fetchone()
		if(customer_detail2['status']!=1):
			flash("Customer no longer exists exists","danger")
			return redirect('/customer_search')
		if 'loggedin' in session and session['type']=='executive':
			return render_template("customer_detail.html",customer_detail1=customer_detail1 ,customer_detail2=customer_detail2)
		return redirect(url_for('login'))
		
	



####delete customer page####
@app.route('/delete_customer',methods=['GET','POST'])
def delete_customer():
	if('loggedin' not in session):
		return redirect(url_for('login'))
	if('loggedin' in session and session['type'] != 'executive'):
		return redirect(url_for('home'))
	checked = False
	details = None
	msg= ""
	if  request.method =='POST' and request.form['btn']=='back':
		return redirect('home')
	if  request.method =='POST' and request.form['btn']=='d':
		print("deleted query deetcted")
		try:
			cursor2 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			id2 = request.form['customer_id']
			print("Hello this was customer id",id2)
			
			#print("\n queru=y is : "+query)
			timestamp = datetime.utcnow()
			print("after timestamp")
			cursor2.execute("UPDATE customer_status set status = 0,message='customer deleted successfully', last_updated = %s  where customer_id = %s",(timestamp,id2))
			print("delete query executed")
			cursor2.execute("COMMIT")
			print('delete query committed')
			flash('Deleted successfully','success')
			cursor2.close()
			
		except:
			print("in except of delete   ")
		return render_template('delete_customer.html',checked = checked,details = details,msg =msg ) 	
		
	if  request.method =='POST' and 'customer_id' in  request.form:
		print('post detected and customer id was ', request.form['customer_id'] )
		print('post detected and  btn id was ', request.form['btn'] )
		id = request.form['customer_id']
		try:
			cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			query = "SELECT c.customer_id,c.customer_ssn,c.name, c.age, c.address,c.city, c.state FROM customer c, customer_status cs where c.customer_id = cs.customer_id and cs.status = 1 and c.customer_id ="+ id
			cursor.execute(query)
			print('query executed')
			details = cursor.fetchone()
			cursor.close()
			if(details is None):
				print('deyail is none')
				x = 'Could not search for the customer :'+  id
				msg =x
				#flash(x,'success')
				return render_template('delete_customer.html',checked = checked,msg=msg)
			checked = True
			#print(type(details),details)
			
		except Exception as e:
			print("in except of retrieve  ")
			msg = "Could not search for the customer"
	
	
	return render_template('delete_customer.html',checked = checked,details =details,msg=msg)
	
@app.route('/search_account')
def search_account():
	if 'loggedin' in session and session['type'] == 'cashier':
		if('error_empty' in request.args):
			return render_template('search_account.html',username=session['username'],emp_type=session['type'],error_empty=True)
		else:
			return render_template('search_account.html', username=session['username'], emp_type=session['type'])
	else:
		return redirect(url_for('login'))

@app.route('/display_search_account',methods=['GET','POST'])
def display_search_account():
	if request.method == 'GET':
		return redirect(url_for('search_account'))
	if 'loggedin' in session and session['type'] == 'cashier':
		if (request.method=='POST' and 'account_select' in request.form):
			account_id = request.form['account_select']
			cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			cursor.execute('SELECT * FROM account WHERE account_id = %s', (account_id,))
			values_account_select = cursor.fetchone()
			cust_id = values_account_select['customer_id']
			cursor.execute('SELECT * FROM account WHERE customer_id = %s', (cust_id,))
			values_customer = cursor.fetchall()
			return render_template('display_search_account.html',values_account_select = values_account_select,values_customer = values_customer)
		elif request.method == 'POST' and ('customer_id' or 'customer_ssn' or 'account_id' in request.form):
			customer_id = request.form['customer_id']
			customer_ssn = request.form['customer_ssn']
			account_id = request.form['account_id']
			cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			if(account_id == '' and customer_id == '' and customer_ssn == ''):
				error_empty = True
				return redirect(url_for('search_account',error_empty = error_empty))
			if(account_id == '' and customer_id == ''):
				cursor.execute('SELECT C.customer_id,C.name FROM customer C,customer_status S WHERE C.customer_ssn = %s AND C.customer_id=S.customer_id AND S.status=1;', (customer_ssn,))
				values = cursor.fetchone()
				if(values):
					customer_id = values['customer_id']
				else:
					return render_template('display_search_account.html',error_empty=True)
			if(account_id == ''):
				cursor.execute('SELECT * FROM account A,customer C,customer_status S WHERE A.customer_id = C.customer_id AND C.customer_id = S.customer_id AND A.customer_id = %s AND S.status=1 AND A.status=1', (customer_id,))
				values_customer = cursor.fetchall()
				if(values_customer):
					return render_template('display_search_account.html',values_customer = values_customer)
				else:
					return render_template('display_search_account.html', error_empty=True)
			else:
				cursor.execute('SELECT * FROM account A,customer C WHERE A.customer_id=C.customer_id AND account_id = %s AND status=1', (account_id,))
				values_account = cursor.fetchone()
				if(values_account):
					return render_template('display_search_account.html',values_account = values_account)
				else:
					return render_template('display_search_account.html', error_empty=True)
		else:
			return redirect(url_for('search_account'))
	else:
		redirect(url_for('login'))