from flask import Flask, render_template, request, send_from_directory, make_response
import pandas as pd
import json
import pdfkit

app = Flask(__name__)


data = pd.read_excel('table.xlsx', skiprows=3)

columns_old = [
    'Family Origin\n',
    'ID', 
    'RECOMMENDATION = Infinitive verb sentence, 1 or 2 sentence grand max',
    'CRITERIA = Rather Interrogative A recommendation for N criteria',
    'Life Cycle Stage',
    'Indicators', 
    'X Indicators', 
    'Y Indicators',
    'unmissable'
]

columns = [
    'family',
    'id', 
    'recommendation',
    'criteria',
    'life_cycle_stage',
    'indicators', 
    'x_indicators', 
    'y_indicators',
    'unmissable'
]


df = pd.DataFrame(data, columns=columns_old)
df = df.rename(columns={k:v for k,v in zip(columns_old, columns)})


unmissable_df = df.loc[df[columns[-1]] == "UNAVOIDABLE"]
#print(unmissable_df.count) #43 rows
missable_df = df.loc[df[columns[-1]] != "UNAVOIDABLE"]
#print(missable_df.count) #511 rows
family_origin = df[columns[0]].unique()


missable_data, unmissable_data = dict(), dict() 
for fam in family_origin:
    unmissable_data[fam] =  [item for item in unmissable_df.to_dict(orient='records') if item[columns[0]]== fam and item[columns[0]] != "ACCOMMODATION"]
    missable_data[fam] = [item for item in missable_df.to_dict(orient='records') if item[columns[0]]== fam]

cart = list()


@app.route('/static/<file>')
def send_static_file(file):
    return send_from_directory('static', file)

@app.route("/")
def index():
    cart.clear()
    for val in unmissable_data.values():
        for item in val:
            cart.append(item)
    return render_template('index.html', family_origin = family_origin, cart_count = len(cart))


@app.route('/api/get_data', methods=["GET"])
def get_data():

    family = request.args.get('family')
    id = request.args.get('id')

    if family is not None:
        family = family.upper()

        if family in missable_data.keys(): 
            
            if id is not None:
                id = id.upper()
                
                try:
                    filtered = list(filter(lambda x: (len(x['id'])>len(id)) & (id in x['id']), missable_data[family]))
                    list_sub_id = [obj['id'] for obj in filtered]
                    criterias = [obj['criteria'] for obj in filtered]
                    return json.dumps({"status": True, "sub_id": list_sub_id, "criterias":criterias})
                except:
                    return json.dumps({"status": False}) 
                
            else:
                try:
                    filtered = list(filter(lambda x: ( len(x['id']) <= len(missable_data[family][0]['id']) ), missable_data[family]))
                    list_id = [obj['id'] for obj in filtered]
                    recommendations = [obj['recommendation'] for obj in filtered]
                    return json.dumps({"status": True, "id": list_id, "recommendations": recommendations})                
                except:
                    return json.dumps({"status": False}) 
        else:
            return json.dumps({"status": False}) 

    else:
        return json.dumps({"status": False}) 

    
  
    

    
@app.route('/api/add_to_cart', methods=["POST"])
def add_to_cart():
    family = request.form['family']
    id = request.form['id']
    sub_id = request.form['sub_id']
    family = family.upper()
    sub_id = sub_id.upper()

    item = next(filter(lambda x: x['id'] == sub_id, missable_data[family]))
    item = {k: "N / A" if str(v) == "nan" else v for k, v in item.items() }

    if item not in cart:
        cart.append(item)
        return json.dumps({"status": True})
    else:
        return json.dumps({"status": False})

@app.route('/api/get_cart_items', methods=["GET"])
def get_cart_items():
    try:
        data = [{columns[i]:a_dict[columns[i]] for i in range(4) if i != 1 } for a_dict in cart]
        return json.dumps({"status": True, "data": data})
    except Exception as e:
        print(e)
        return json.dumps({"status": False})



@app.route('/api/get_result', methods=["GET"])
def get_result():
    try:
        data = [{columns[i]:a_dict[columns[i]] for i in range(0,len(columns)-1) if i != 1} for a_dict in cart]
        return json.dumps({"status": True, "data": data})
    except Exception as e:
        print(e)
        return json.dumps({"status": False})

@app.route('/download_result', methods=["GET"])
def download_result():
        data = [{columns[i]:a_dict[columns[i]] for i in range(0,len(columns)-1) if i != 1} for a_dict in cart]
        
        html = render_template( "result.html",
            cart_data=data)
        
        pdf = pdfkit.from_string(html, False)
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = "inline; filename=result.pdf"
        return response

        return html

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8888)
