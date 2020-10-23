from flask import Flask, render_template, jsonify, request
import numpy as np
import pandas
import json

app = Flask(__name__)




@app.route("/productlist", methods=['GET'])
def productlist():
    data = pandas.read_excel('products_database.xlsx', sheet_name='Products')
    column= np.array(data['Machine/Devices'])
    lists = column.tolist()
    return jsonify({'products' : lists})


@app.route("/findresult", methods=['POST'])
def findresult():
    product = request.args.get('product')
    working_hours = request.args.get('working_hours')
    result = calculation(product,working_hours)
    return jsonify(result)

def calculation(product, working_hours):
    data = pandas.read_excel('products_database.xlsx', sheet_name='Products')
    column= np.array(data['Machine/Devices']==product)
    lists = column.tolist()
    if True in lists:
        my_index = lists.index(True)
        my_data = np.array(data.loc[my_index:my_index])
        required = my_data.tolist() 
        avg_energy_cons = required[0][1] * 360
        my_array = {
            'product' : required[0][0],
            'avg_energy_cons' :  avg_energy_cons
        }
        co_emissions = 600 * avg_energy_cons * int(working_hours)
        my_array['co_emissions'] = co_emissions
        sorted_dict = recommendationSystem(int(working_hours))
        my_array['top3'] = sorted_dict
        return my_array
    else:
        return "Device is not in the list"

def recommendationSystem(working_hours):
    data = pandas.read_excel('products_database.xlsx', sheet_name='Products')
    df = pandas.DataFrame(data)
    df['Avg cons'] = df['Per day cons'] * 360
    df['co2_emissions'] = working_hours * 600 * df['Avg cons']
    df['rank'] = df.index + 1
    df = df.sort_values(by='co2_emissions', ascending=False)
    df = df.iloc[:3]
    sorted_list = df.values.tolist()

    new_dict = []

    for index, my_row in enumerate(sorted_list):
        dicto = {
            'product' : my_row[0],
            'avg_energy_cons' : my_row[2],
            'co2_emissions' : my_row[3],
            'rank' : index+1
        }
        new_dict.append(dicto)

    return new_dict



if __name__ == '__main__':
    app.run(debug=True)
