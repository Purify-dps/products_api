from flask import Flask, render_template, jsonify, request
import numpy as np
import pandas
import json

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
    data = pandas.read_excel('products_database.xlsx', sheet_name='Products')
    column = []
    database_column_lowercase = [x.lower() for x in data['Machine/Devices']]
    for product in products:
        product_lowercase = product.lower()
        if(product_lowercase in database_column_lowercase):
            one_item = np.array(data.loc[database_column_lowercase.index(product_lowercase)])
            one_item_list = one_item.tolist()
            column.append(one_item_list)
        else:
            column.append(product + " is not present")

    lists = column  

    returned_results = []
    for mylist in lists:
        if("is not present" not in mylist):
            avg_energy_cons = mylist[1] * 360
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
            returned_results.append(mylist)

    sorted_list = recommendationSystem(returned_results, int(working_hours))
    return sorted_list
    

def recommendationSystem(returned_results, working_hours):
    new_list = []
    for result in returned_results:
        if("is not present" not in result):
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
        if("is not present" in result):
            new_dict.append(result)

    return new_dict



if __name__ == '__main__':
    app.run(debug=True)
