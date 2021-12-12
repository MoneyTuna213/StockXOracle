import os
from google.cloud import firestore
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash import no_update
from sklearn.linear_model import LinearRegression
import pandas as pd
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as soup
import json
import requests
import datetime as dt

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

app.layout = html.Div([
    html.Div("stockx oracle", style={
        'font-family':'Courier New',
        'font-weight':'bold',
        'font-size':'150px',
        'text-align': 'center',
        'padding-top': '275px'
    }),
    html.Div("created by milo", style={
        'font-family':'Courier New',
        'padding-bottom':'100px',
        'font-weight':'bold',
        'font-size':'75px',
        'text-align': 'center'
    }),
        dcc.Input(
        id="userinput",
        placeholder="Type Link Here...", 
        style={'right':'-760px',
        #'top':'250px',
        #'background':'transparent',
        'color':'black',
        'position':'relative'
        }
        ),
    html.Button("Predict", id="predictbutton", 
    style={
        'right':'-780px',
        'position':'relative',
        #'right':'-410px',
        #'bottom':'-110px' 
    }),
    html.Div(id="predictoutput", style={
        'font-size':'150px',
        'padding-left':'35px',
        'padding-top':'1250px'
    }),
],
style={ 
'background-image': 'url("https://th.bing.com/th/id/OIP.bget4M_o7J-E_S1LP6f-YAHaEo?pid=ImgDet&rs=1")',
'background-size':'30720px 19200px'
})

def pipeline(data) :
  Y = data.iloc[:, 0].values.reshape(-1, 1)  # values converts it into a numpy array
  X = data.iloc[:, 1].values.reshape(-1, 1)  # -1 means that calculate the dimension of rows, but have 1 column
  linear_regressor = LinearRegression()  # create object for the class
  linear_regressor.fit(X, Y)  # perform linear regression
  Y_pred = linear_regressor.predict([X[-1]+5])# make predictions
  return(Y_pred)

def scraper(url):
    url
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    page_soup = soup(webpage, 'html.parser')
    productid=str(page_soup).split('productId":"')[1].split('"')[0]
    #print(productid)
    releasedate=str(page_soup).split('releaseDate":"')[1].split('"')[0]
    if releasedate=="--":
        releasedate=0
    pd.to_datetime(releasedate)
    url='https://stockx.com/api/products//activity?state=480&currency=USD&limit=999999999&page=1&sort=createdAt&order=DESC&country=US'
    url = url[:32] + productid + url[32:]
    print(url)
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    page_soup = soup(webpage, 'html.parser')
    pagejson = json.loads(str(page_soup))
    productdata=pagejson['ProductActivity']
    return productdata, releasedate

def getinputs(productdata, releasedate):
    pricearray=[]
    for i in range (len(productdata)):
        data=productdata [i]
        pricearray.append(data["localAmount"])

    sizearray=[]
    for i in range (len(productdata)):
        data=productdata [i]
        if "W" in data['shoeSize']:
            data['shoeSize']=data['shoeSize'].replace("W","")
        if "Y" in data['shoeSize']:
            data['shoeSize']=data['shoeSize'].replace("Y","")
        shoeSize=float(data['shoeSize'])
        sizearray.append(shoeSize)

    datearray=[]
    for i in range (len(productdata)):
        data=productdata [i]
        datearray.append(pd.to_datetime(dt.datetime.strptime(data["createdAt"],'%Y-%m-%dT%H:%M:%S+00:00')))

    releasearray=[]
    for i in range (len(productdata)):
        releasearray.append(pd.to_datetime(releasedate))

    newdatearray=[]
    for i in range (len(productdata)):
        newdatearray.append((datearray[i]-releasearray[i])/pd.Timedelta(hours=1))

    return pricearray, sizearray, newdatearray

@app.callback(
    Output("predictoutput", "children"),
    State("userinput", "value"),
    Input("predictbutton", "n_clicks"),
)
def predictstockxoutput(url, Input,):
    if Input>0:
        productdata, releasedate=scraper(url)
        #print(scrapeddata)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="StockXFirebaseKey.json"
        db = firestore.Client(project='stockx-predict')
        #sneakerdb=db.collection(u'sneakerdatabase').document().get().to_dict()
        pricearray, sizearray, newdatearray=getinputs(productdata, releasedate)
        data = pd.DataFrame()
        data['price'] = pricearray
        data['date'] = newdatearray
        data['size'] = sizearray
        prediction=pipeline(data)
        return "THE PRICE WILL BE $" + str(round(prediction[0][0]))

if __name__ == '__main__':
    app.run_server(debug=True)