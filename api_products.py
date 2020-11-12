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
    products = details['products']
    working_hours = details['working_hours']
    result = calculation(products,working_hours)
    return jsonify(result)

def calculation(products, working_hours):
    column = []
    for product in products:
        one_item = np.array([product,scrapper(product)])
        one_item_list = one_item.tolist()
        column.append(one_item_list)

    lists = column 

    returned_results = []
    for mylist in lists:
        if("is not a device" not in mylist[1]):
            avg_energy_cons = int(mylist[1]) * 360
            co_emissions = (600 * avg_energy_cons * int(working_hours)) / 100
            savings_euros = co_emissions * 0.0132
            my_array = {
                'product' : mylist[0],
                'avg_energy_cons' :  avg_energy_cons, 
                'co2_emissions' : co_emissions,
                'savings_euros' : savings_euros
            }
            returned_results.append(my_array)
        else:
            returned_results.append(mylist[0]+' '+mylist[1])

    sorted_list = recommendationSystem(returned_results, int(working_hours))
    return sorted_list
    
def recommendationSystem(returned_results, working_hours):
    new_list = []
    for result in returned_results:
        if("is not a device" not in result):
            new_list.append(result)
    
    df = pandas.DataFrame(new_list)
    df['rank'] = df.index + 1
    df = df.sort_values(by='avg_energy_cons', ascending=False)
    df = df.iloc[:3]
    sorted_list = df.values.tolist()

    new_dict = []

    for index, my_row in enumerate(sorted_list):
        dicto = {
            'product' : my_row[0],
            'avg_energy_cons' : my_row[1],
            'co2_emissions' : my_row[2],
            'savings_euros' : my_row[3],
            'rank' : index+1
        }
        new_dict.append(dicto)
    
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
