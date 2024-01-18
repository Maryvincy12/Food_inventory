
from flask import Flask,render_template,request,redirect,url_for,flash,session,g
import boto3
from flask_mysqldb import MySQL
import os

application = app = Flask(__name__)

#s3 connection
s3 = boto3.client('s3',
                      aws_access_key_id='AKIAQRKQEGPJJ5QM53X6',
                      aws_secret_access_key='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')


app.secret_key=os.urandom(24)

#database connection establishment
app.config['MYSQL_HOST'] = 'marydb.cuuatoz5ywpt.ap-southeast-2.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'marydb'
app.config['MYSQL_PASSWORD'] = 'Mary12vincy'
app.config['MYSQL_DB'] = 'sys'

mysql = MySQL(app)

#home page
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

#About website
@app.route('/about')
def about():
    return render_template('about.html')

#user registration page
@app.route('/register', methods = ['POST', 'GET'])
def register():
     
    if request.method == 'POST':

        mail = request.form['email']
        uname = request.form['uname']        
        passwd = request.form['psw']
        contact_num = request.form['number']
        
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM registered_users WHERE user_name=%s ',(uname,))
        s=cursor.fetchall()
        cursor.execute('SELECT * FROM registered_users WHERE user_mail=%s ',(mail,))
        s1=cursor.fetchall()

        #To acknowledge Username and Mail id already exists
        if len(s)==1 and len(s1)==1:    
            flash('Username and mail id already exists!')
            return redirect(url_for('register')) 
        
        #To acknowledge Username already exists
        elif len(s)==1:
            flash('Username already exists!')
            return redirect(url_for('register')) 
        
        #To acknowledge Mail id already exists
        elif len(s1)==1:
            flash('Mail Id already exists!')
            return redirect(url_for('register')) 
        
        #Registering new user 
        else:
            cursor.execute(' INSERT INTO registered_users VALUES(%s,%s,%s,%s)',(mail,uname,passwd,contact_num))
            #Create a new table for this new user
            query = f"CREATE TABLE {uname} (username VARCHAR(45), item_name VARCHAR(255), quantity VARCHAR(55), image VARCHAR(255))"
            cursor.execute(query)
            mysql.connection.commit()
            cursor.close()
        
            return redirect(url_for('login'))
    return render_template('register.html')


#user login page
@app.route('/login' , methods = ['POST', 'GET'])
def login():
    
    if request.method == 'POST':
       
        fname = request.form['mail']
        psw = request.form['psw']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM registered_users WHERE user_mail=%s AND user_password=%s ',(fname,psw))
        s=cursor.fetchall()
        cursor.close()
        session.pop('user',None)
        
        #Verifying the login credentials
        if len(s)==1:
            session['user'] = s[0][1]      
            return redirect(url_for('profile',name = s[0][1]))      

        #Wrong Credentials,redirect to the same page         
        else:
            flash('Check your login details !')
            return redirect(url_for('login'))

    return render_template('login.html')

#Redirecting to Profile page
@app.route('/profile<name>',methods=['POST','GET'])
def profile(name):

    #Checks if user logged in
    if g.user:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM {}'.format(name))
        list_items = cursor.fetchall()
        mysql.connection.commit()
        cursor.close()
        return render_template('profile.html', stat = name,list_items=list_items , user = session['user'])
    return redirect(url_for('login'))

#session management
@app.before_request
def before_request():

    g.user = None

    if 'user' in session:
        g.user = session['user']

#User Logout         
@app.route('/dropsession')
def dropsession():

    session.clear()
    return render_template('login.html')

#adding items
@app.route('/add_item', methods=['POST','GET'])
def add_item():

    cur = mysql.connection.cursor()
    if request.method == 'POST':

        bname = request.form['bname']
        iname = request.form['iname']
        num = request.form['num']
        file = request.files['file']
        sql = f"SELECT * FROM {bname} WHERE item_name= %s"
        values = (iname,)
        cur.execute(sql,values)
        s2=cur.fetchall()
        
        #Checks if the item already exists to avoid duplicate data
        if len(s2)!=0:
            flash('This item already exists !')
            return redirect(url_for('profile',name = bname))

        #Adding food items     
        else:
            #Storing image in S3
            s3.upload_fileobj(file, 'foodbucketapp',file.filename)
            #retriving data from s3
            object_url = f"https://foodbucketapp.s3.ap-southeast-2.amazonaws.com/{file.filename}"
            sql = f"INSERT INTO {bname} (username,item_name,quantity,image) VALUES (%s,%s,%s,%s)"
            values = (bname,iname,num,object_url)
            cur.execute(sql,values)
            mysql.connection.commit()
            cur.close()
            #Notifying User
            flash('Successfully Added !!')
            return redirect(url_for('profile',name = bname))
            
#Edit or delete an item
@app.route('/edit_item', methods=['POST','GET'])
def edit_item():
    
    if request.method == 'POST':

        cur = mysql.connection.cursor()
        bname = request.form['bname']
        iname = request.form['iname']
        num = request.form['num']
        file = request.form['file']

        if file == "Edit":

            #Updating an existing items 
            sql = f"UPDATE {bname} SET quantity= %s WHERE item_name=%s"
            values = (num,iname)
            cur.execute(sql,values)
            mysql.connection.commit()
            cur.close()
            #Notifying User
            flash('Successfully Updated !!')
            return redirect(url_for('profile',name = bname))
        
        else:

            #Deleting an existing item
            cur = mysql.connection.cursor()
            sql = f"DELETE FROM {bname} WHERE item_name=%s"
            values = (iname,)
            cur.execute(sql,values)
            mysql.connection.commit()
            cur.close()
            #Notifying User
            flash('Successfully deleted !!')
            return redirect(url_for('profile',name = bname))

if __name__=='__main__':
    app.run(debug=True)
