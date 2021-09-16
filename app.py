from flask import Flask, request, render_template, url_for, flash, session
from company import company, company1
import bs4
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, and_
import atexit
import smtplib, ssl
from apscheduler.schedulers.background import BackgroundScheduler
import math

def parsePrice(link):
    headers = {
    'User-agent': 'Mozilla/5.0',
    }
    r= requests.get(link, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    price = soup.find('div', {'class':'My(6px) Pos(r) smartphone_Mt(6px)'}).find_all('span')[0].text
    return price

def eps(link):
    headers = {
    'User-agent': 'Mozilla/5.0',
    }
    r= requests.get(link, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    eps = soup.find_all('td', {'class':'Ta(end) Fw(600) Lh(14px)'})[11].find('span').text
    return eps
def growth(link):
    headers = {
    'User-agent': 'Mozilla/5.0',
    }
    r= requests.get(link, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    growth = soup.find_all('td', {'class':'Ta(end) Py(10px)'})[16].text
    return growth
def high(link):
    headers = {
    'User-agent': 'Mozilla/5.0',
    }
    r= requests.get(link, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    high = soup.find_all('td', {'class':'Fw(500) Ta(end) Pstart(10px) Miw(60px)'})[12].text
    return high
def low(link):
    headers = {
    'User-agent': 'Mozilla/5.0',
    }
    r= requests.get(link, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    low = soup.find_all('td', {'class':'Fw(500) Ta(end) Pstart(10px) Miw(60px)'})[13].text
    return low

def update():
    for s in range(0,len(company1)):
        company1[s].price =str(parsePrice('https://ca.finance.yahoo.com/quote/'+company1[s].ticker+'?p='+company1[s].ticker))
        company1[s].price = float (company1[s].price[0:10].replace(',',''))
        users.query.filter_by(ticker = company1[s].ticker).update({users.stock_price: company1[s].price})
        db.session.commit()

    for x in range(0,len(company1)): #goes through each company
        query = users.query.filter(and_(users.user_price >= company1[x].price, users.ticker == company1[x].ticker))
        reslist = query.all()
        rows =len(reslist)
        j=0
        print('for')
        while rows>0:
            deleted_user = query[j]
            rows-=1
            j+=1
            deleted_email = deleted_user.email
            deleted_ticker = deleted_user.ticker
            deleted_price = str(deleted_user.user_price)
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.ehlo()
            server.starttls()
            server.ehlo()

            server.login ('myemail', 'mypassword')

            subject = 'Price Reached!'
            body = 'Your desired price of $' + deleted_price +' for ' + deleted_ticker +' has been reached! Thank you for using Bottom-Up'
            msg = f"Subject: {subject}\n\n{body}"
            server.sendmail('myemail',deleted_email, msg)
            print ('sent')
        query.delete()
        db.session.commit()




app = Flask(__name__)
app.secret_key = 'app'
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'myemail'
app.config['MAIL_PASSWORD'] = 'mypassword'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] =True
db = SQLAlchemy(app)

class users(db.Model):
    __tablename__ = 'users'
    user_price = db.Column(db.Float)
    stock_price = db.Column(db.Float)
    email = db.Column (db.String(50))
    ticker = db.Column (db.String(50))
    num = db.Column (db.Integer, primary_key=True)

    def __init__(self,user_price,stock_price, email, ticker):
        self.user_price = user_price
        self.stock_price =stock_price
        self.email= email
        self.ticker =ticker

@app.before_first_request
def init_scheduler():
    sched = BackgroundScheduler()
    sched.add_job(update,'interval',minutes=5)
    sched.start()
    atexit.register(lambda : sched.shutdown())

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/', methods=['POST'])
def my_form_post():
    stock = request.form['stock']
    price = request.form['price']
    email = request.form ['email']
    
    i=0
    for i in range(0,len(company1)):
        if (company1[i].name.lower() == stock.lower() or company1[i].ticker.lower() == stock.lower()):
            break
    company1[i].price = str(parsePrice('https://ca.finance.yahoo.com/quote/'+company1[i].ticker+'?p='+company1[i].ticker))
    company1[i].price = float (company1[i].price[0:10].replace(',',''))
    price = float(price.replace('$',''))

    u1= users(user_price = float (price),stock_price= float (company1[i].price),email= email,ticker= company1[i].ticker)
    db.session.add(u1)
    db.session.commit()
   
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()

    server.login ('myemail', 'mypassword')

    subject = 'Confirmation'
    body = "We will send you an email when " + company1[i].name + " reaches a price of $" + str(price) +"!"
    msg = f"Subject: {subject}\n\n{body}"
    server.sendmail('myemail',email, msg)
    flash ("Confirmation Email has been sent!")
    return render_template("index.html")

@app.route("/ahmed")
def view():
    return render_template("view.html", values=users.query.all())

@app.route('/calculations')
def calc():
    return render_template("calculation.html")
@app.route('/calculations', methods =['POST'])
def calculation():
    MOS = request.form['MOS']
    stock = request.form['stock']
    option = request.form['sellist1']
    discount = request.form['discount']
    for i in range(0,len(company1)):
            if (company1[i].name.lower() == stock.lower() or company1[i].ticker.lower() == stock.lower()):
             break
    if (company1[i].name.lower() != stock.lower() and company1[i].ticker.lower() != stock.lower()):
        flash ("StockNotFound")
    else:
        print(i)
        company1[i].price = str(parsePrice('https://ca.finance.yahoo.com/quote/'+company1[i].ticker+'?p='+company1[i].ticker))
        company1[i].price = float (company1[i].price[0:10].replace(',',''))

        company1[i].eps = str(eps('https://ca.finance.yahoo.com/quote/'+company1[i].ticker+'?p='+company1[i].ticker))
        company1[i].eps = float (company1[i].eps[0:10])

        company1[i].growth = str(growth('https://ca.finance.yahoo.com/quote/'+company1[i].ticker+'/analysis?p='+company1[i].ticker))
        company1[i].growth = float (company1[i].growth[0:10].replace ('%',''))
        
        company1[i].high = str(high('https://ca.finance.yahoo.com/quote/'+company1[i].ticker+'/key-statistics?p='+company1[i].ticker))
        company1[i].high = float (company1[i].high[0:10].replace(',',''))
        
        company1[i].low = str(low('https://ca.finance.yahoo.com/quote/'+company1[i].ticker+'/key-statistics?p='+company1[i].ticker))
        company1[i].low = float (company1[i].low[0:10].replace(',',''))

        if (option == 'graham'):
            if(math.isnan(company1[i].eps) or math.isnan(company1[i].growth) or company1[i].eps<0):
                flash ('UnableToCalculate')
                return render_template("calculation.html")
            else:
                MOS =float(MOS.replace('%',''))
                MOS = (100 -MOS)/100;
                i_price = float (((company1[i].eps)* (7+company1[i].growth) *4.4 / 2.34) * MOS)
        elif (option == 'lower'):
            i_price = ((company1[i].high - company1[i].low) *0.1) + company1[i].low
        elif (option == 'lower15'):
             i_price = ((company1[i].high - company1[i].low) *0.15) + company1[i].low
        elif (option == 'lower20'):
             i_price = ((company1[i].high - company1[i].low) *0.20) + company1[i].low
        elif(option=='eps'):
            if(math.isnan(company1[i].eps) or math.isnan(company1[i].growth) or company1[i].eps<0 or company1[i].growth<0):
                flash ('UnableToCalculate')
                return render_template("calculation.html")
            else:
                dec = (company1[i].growth/100) +1
                dec = (math.pow(dec,4)) * company1[i].eps
                pe = company1[i].growth *2
                pe =pe*dec #188.10
                MOS =float(MOS.replace('%',''))
                MOS = (100 -MOS)/100;
                discount =(float(discount.replace('%','')) /100) +1
                discount = math.pow(discount,4)
                pe = pe/discount
                i_price = pe*MOS
            
        
        flash (i_price)
    return render_template("calculation.html")


if __name__=="__main__":
    db.create_all()
    app.run(debug=True)
    
