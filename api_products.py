from flask import Flask, render_template, jsonify, request
from bs4 import BeautifulSoup as bs
import numpy as np
import pandas
import json
import requests
import os
from openpyxl import load_workbook
from random import randint
import re
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier

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
    total_emissions = 0
    total_energy_cons = 0
    total_savings = 0
    for device in result:
        if("is not found" not in device):
            total_emissions = device['overall_co2_emissions_per_device'] + total_emissions
            total_energy_cons = device['overall_avg_energy_cons_per_device'] + total_energy_cons
            total_savings = device['overall_savings_euros_per_device'] + total_savings

    
    exceloutput = list(filter(lambda k: 'is not found' not in k, result))
    #return jsonify(exceloutput)
    df = pandas.DataFrame(exceloutput)
    #df = df.iloc[:1]
    #df = df.loc[:, df.columns != 'rank']
    df['overall_co2_emissions_of_all_devices'] = total_emissions
    df['overall_avg_energy_cons_of_all_devices'] = total_energy_cons
    df['overall_savings_euros_of_all_devices'] = total_savings
    
    initiative = classify(total_emissions)  
    #return jsonify(initiative) 
    df['initiative_number'] = initiative
    #return jsonify(classify(total_emissions)[0])
    if os.path.isfile('output.xlsx'):
        df1 = pandas.read_excel("output.xlsx")
        if df1.empty:
            header = True
            startrow = 0
            user = 0
            user = df1['user_number'].iloc[-1] + 1 
        else:
            header = False
            length = len(df1)
            startrow =  length + 1
            user = df1['user_number'].iloc[-1]
            df['user_number'] = user + 1
            df = df1.append(df, ignore_index=True)
    else:
        header = True
        startrow = 0
        user = 0
        df['user_number'] = user + 1

    my_file = open("initiative.txt", "r")
    content = my_file.read()
    content_list = content.split("\"")
    content_list = list(filter(None,content_list))
    my_file.close() 
    #return jsonify(content_list)   
    output = {'overall_results_all_devices':{'total_emissions_all_devices':total_emissions,'total_energy_cons_all_devices':total_energy_cons,'total_savings_all_devices':total_savings}, 'detailed_device_results' : result, 'initiative' : {'initiative_number' : initiative, 'initiative_text' : content_list[initiative - 1]} }
    mode = 'w' if header else 'a'
    with pandas.ExcelWriter("output.xlsx", engine='openpyxl', mode='w') as writer:
        df.to_excel(writer, sheet_name='Sheet1', header=True, index=False, startrow=0)
    writer.save()
    writer.close()

    return jsonify(output)

def calculation(products):
    column = []
    for product in products:
        myout = scrapper(product.get('name'))
        if("is not found" not in str(myout)):
            product['avg_cons_per_day'] =(myout / 1000) * int(product.get('working_hours'))
        else:
            product['avg_cons_per_day'] = myout
        column.append(product)
    

    lists = column 
    #return lists
    returned_results = []
    for mylist in lists:
        if("is not found" !=  mylist.get('avg_cons_per_day')):
            avg_energy_cons = float(mylist.get('avg_cons_per_day')) * 365
            overall_avg_energy_cons = avg_energy_cons * int(mylist.get('number'))
            co_emissions = (600 * avg_energy_cons)
            overall_co_emissions = co_emissions * int(mylist.get('number'))
            savings_euros = co_emissions * 0.0132
            overall_savings_euros = savings_euros * int(mylist.get('number'))
            
            mylist['avg_energy_cons_per_year_per_device'] = avg_energy_cons
            mylist['co2_emissions_per_device'] = co_emissions
            mylist['savings_euros_per_device'] = savings_euros
            mylist['overall_avg_energy_cons_per_device'] = overall_avg_energy_cons
            mylist['overall_co2_emissions_per_device'] = overall_co_emissions
            mylist['overall_savings_euros_per_device'] = overall_savings_euros
            returned_results.append(mylist)
        else:
            returned_results.append(mylist['name']+' '+mylist['avg_cons_per_day'])    
    sorted_list = recommendationSystem(returned_results)
    return sorted_list
    
def recommendationSystem(returned_results):
    sorted_list_without_msgs = []
    for result in returned_results:
        if("is not found" not in result):
            sorted_list_without_msgs.append(result)
    
    sorted_list = sorted(sorted_list_without_msgs, key = lambda i: i['overall_co2_emissions_per_device'],reverse=True)
    new_dict = []

    for index, my_row in enumerate(sorted_list):
        my_row['rank'] = index+1 
        new_dict.append(my_row)

    for result in returned_results:
        if("is not found" in result):
            new_dict.append(result)

    return new_dict

def scrapper(product):
    product = product.replace(" ", "+")
    USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
    LANGUAGE = "en-US,en;q=0.5"
    url = "https://www.google.com/search?q="+product+"+average+consumption+watt&oq="+product+"+average+consumption+watt"
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT
    session.headers['Accept-Language'] = LANGUAGE
    session.headers['Content-Language'] = LANGUAGE
    html = session.get(url)
    soup = bs(html.text, "html.parser")
    soup2 = bs(html.text,'lxml')
    soup3 = bs(html.text,'lxml')
    soup4 = bs(html.text,'html.parser')
    soup5 = bs(html.text,'html.parser')
    
    try:
        data = soup.find("div", attrs={'data-tts':'answers'}).text
        output = [float(s.replace(",", "")) for s in data.split() if s.isdigit()]
        return output[0]
    except:
        try:
            data = soup2.find("div", attrs={'data-attrid':'wa:/description'}).text
            data = [float(s.replace(",", "")) for s in data.split() if s.isdigit()]
            return data[0]
        except:
            try:
                data = soup3.find("div", attrs={'class':'webanswers-webanswers_table__webanswers-table'}).text
                output2 = [float(s.replace(",", "")) for s in data.split() if s.isdigit()]
                return output2[0]
            except:
                try:
                    data = soup4.find_all("span", attrs={'class':'aCOpRe'})
                    data =  data[1].find('span', attrs={}).text
                    output4 = [float(s.replace(",", "")) for s in data.split() if s.isdigit()]
                    return output4[0]
                except:
                    try:
                        data = soup5.find("span", attrs={'class':'hgKElc'}).text
                        #data =  data[0].find('span', attrs={}).text
                        regex = re.compile('[^0-9.]')
                        output5 = [regex.sub('', s).replace(",","") for s in data.split() if s.isalnum()]
                        output5 = list(filter(None, output5))
                        output5 = list(map(float, output5))
                        return output5[0]        
                    except:
                        return "is not found"

def classify(overall_co2_emissions):
    if os.path.isfile('output.xlsx'):    
        devices = pandas.read_excel("output.xlsx", index_col=None)
        if len(devices) > 1:
            feature_names = ['overall_co2_emissions_of_all_devices']
            X = devices[feature_names]
            y = devices['initiative_number']
                
            X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)

            scaler = MinMaxScaler()
            X_train = scaler.fit_transform(X_train)
            X_test = scaler.transform(X_test)

                
            knn = KNeighborsClassifier()
            knn.fit(X_train, y_train)
            print('Accuracy of K-NN classifier on training set: {:.2f}'
                    .format(knn.score(X_train, y_train)))
            print('Accuracy of K-NN classifier on test set: {:.2f}'
                    .format(knn.score(X_test, y_test)))
            predicted =  knn.predict([[overall_co2_emissions]]).tolist()
            return predicted[0]
        else:
            return randint(1,3)
    else:
        return randint(1,3)

if __name__ == '__main__':
    app.run(debug=True)
