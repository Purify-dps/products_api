from flask import Flask, render_template, jsonify, request
from bs4 import BeautifulSoup as bs
import numpy as np
import pandas
import json
import requests

app = Flask(__name__)



#@app.route("/productlist", methods=['GET'])
#def productlist():
#    data = pandas.read_excel('products_database.xlsx', sheet_name='Products')
#    column= np.array(data['Machine/Devices'])
#    lists = column.tolist()
#    return jsonify({'products' : lists})


@app.route("/findresult", methods=['POST'])
def findresult():
    details = request.get_json()
    products = details.get('products')
    result = calculation(products)
    return jsonify(result)

def calculation(products):
    column = []
    for product in products:
        product['avg_cons_per_day'] = scrapper(product.get('name'))
        column.append(product)
    

    lists = column 
    #return lists

    returned_results = []
    for mylist in lists:
        if("is not a device" !=  mylist.get('avg_cons_per_day')):
            avg_energy_cons = int(mylist.get('avg_cons_per_day')) * 360
            co_emissions = (600 * avg_energy_cons * int(mylist['working_hours'])) / 100
            savings_euros = co_emissions * 0.0132
            
            mylist['avg_energy_cons'] = avg_energy_cons
            mylist['co2_emissions'] = co_emissions
            mylist['savings_euros'] = savings_euros
            returned_results.append(mylist)
        else:
            returned_results.append(mylist['name']+' '+mylist['avg_cons_per_day'])    
    sorted_list = recommendationSystem(returned_results)
    return sorted_list
    
def recommendationSystem(returned_results):
    sorted_list_without_msgs = []
    for result in returned_results:
        if("is not a device" not in result):
            sorted_list_without_msgs.append(result)
    
    sorted_list = sorted(sorted_list_without_msgs, key = lambda i: i['co2_emissions'],reverse=True)
    new_dict = []

    for index, my_row in enumerate(sorted_list):
        my_row['rank'] = index+1 
        new_dict.append(my_row)

    for result in returned_results:
        if("is not a device" in result):
            new_dict.append(result)

    return new_dict

def scrapper(product):
    product = product.replace(" ", "+")
    USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
    LANGUAGE = "en-US,en;q=0.5"
    url = "https://www.google.com/search?q="+product+"+average+consumption+watts"
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT
    session.headers['Accept-Language'] = LANGUAGE
    session.headers['Content-Language'] = LANGUAGE
    html = session.get(url)
    soup = bs(html.text, "html.parser")
    soup2 = bs(html.text,'lxml')
    soup3 = bs(html.text,'lxml')
    try:
        data = soup.find("div", attrs={'data-tts':'answers'}).text
        output = [int(s.replace(",", "")) for s in data.split() if s.isdigit()]
        return output[0]
    except:
        try:
            data = soup2.find("div", attrs={'data-attrid':'wa:/description'}).text
            data = [int(s.replace(",", "")) for s in data.split() if s.isdigit()]
            return data[0]
        except:
            try:
                data = soup3.find("div", attrs={'class':'webanswers-webanswers_table__webanswers-table'}).text
                output2 = [int(s.replace(",", "")) for s in data.split() if s.isdigit()]
                return output2[0]
            except:
                return "is not a device"


if __name__ == '__main__':
    app.run(debug=True)
