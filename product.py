from flask import Blueprint, request, abort
from google.oauth2 import id_token
from google.auth import crypt
from google.auth import jwt
from google.auth.transport import requests
from google.cloud import datastore
import json
import constants

client = datastore.Client()

client_id = "572611850973-tfrgfbf0k74j7tkprtffut7fsk4tpv9i.apps.googleusercontent.com"
client_secret = "wqnOY2WRwSHrPklqLvzm3hH3"

bp = Blueprint('product', __name__, url_prefix='/products')

@bp.app_errorhandler(405)
def method_not_allowed(e):
    return ({"Error":"Method not recognized"}, 405)

@bp.route('', methods=['POST','GET'])
def guests_get_post():
    auth_header = request.headers.get('Authorization')
    owner_sub=''

    if auth_header:
        auth_token = auth_header.split(" ")[1]
    else:
        auth_token =''
       
    try:
        req = requests.Request()
        id_info = id_token.verify_oauth2_token(auth_token, req, client_id)
        owner_sub = id_info['sub']
    except:
        return ({"Error":"Missing or Invalid JWT"}, 401)
    
    accept_handle = str(request.accept_mimetypes)
    if not accept_handle:
        return ({"Error": "Not Acceptable."}, 406)

    if request.method == 'POST':
        content = request.get_json()
        
        if accept_handle == "application/json":

            if len(content) < 4:
                return ({"Error":"The request object is missing at least one of the required attributes"}, 400)
            else:
                new_prod = datastore.entity.Entity(key=client.key(constants.product))
                new_prod.update({"name": content["name"], "type": content["type"], "price": content["price"], "quantity": content["quantity"]})
                new_prod["owner"] = owner_sub
                client.put(new_prod)
                output = {"id":str(new_prod.key.id), "name": content["name"], "type": content["type"],
                        "price": content["price"], "owner": owner_sub, "quantity": content["quantity"], "self":request.url + "/"+str(new_prod.key.id)}
                return (json.dumps(output, sort_keys=True, indent=4), 201)
        else:
            return ({"Error": "Not Acceptable."}, 406)
    elif request.method == 'GET':
        # Get the query of the products that only belongs to the user!
        query = client.query(kind=constants.product).add_filter('owner', '=', owner_sub)
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        g_iterator = query.fetch(limit= q_limit, offset=q_offset)
        pages = g_iterator.pages
        results = list(next(pages))
        res_P = list(query.fetch())
        total_P = len(res_P)
        
        if accept_handle == "application/json":
            if g_iterator.next_page_token:
                next_offset = q_offset + q_limit
                next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
            else:
                next_url = None
            for e in results:
                e["id"] = e.key.id
                e["self"] = request.url+"/"+str(e["id"])
                new_shelf ={}

                if ("shelf" in e) and (e["shelf"] != None):
                    #new_shelf = {"id": e['shelf'], "self":request.url_root+ "/shelves/"+str(e['shelf'])}
                    
                    s_key = client.key(constants.shelf, int(e["shelf"]))
                    shelf = client.get(key=s_key)
                    if not shelf:
                        return ({"Error":"No shelf with this shelf_id exists"}, 404)
                    new_shelf = {"id": e['shelf'], "self":request.url_root+ "/shelves/"+str(e['shelf']), "location": shelf["location"]}
                    
                    e["shelf"] = new_shelf
              
            output = {"total of products": total_P, "products": results}
            if next_url:
                output["next"] = next_url
            return json.dumps(output, indent=4, sort_keys=True)
        else:
            return ({"Error": "Not Acceptable."}, 406)
    else:
        abort(405)
    

@bp.route('/<id>', methods=['PATCH','PUT','DELETE', 'GET'])
def guests_put_delete(id):
    auth_header = request.headers.get('Authorization')
    owner_sub=''

    if auth_header:
        auth_token = auth_header.split(" ")[1]
    else:
        auth_token =''
       
    try:
        req = requests.Request()
        id_info = id_token.verify_oauth2_token(auth_token, req, client_id)
        owner_sub = id_info['sub']
    except:
        return ({"Error":"Missing or Invalid JWT"}, 401)

    if request.method == 'PATCH':
        content = request.get_json()
        accept_handle = str(request.accept_mimetypes)
 
        if not accept_handle:
            return ({"Error": "Not Acceptable."}, 406)

        if accept_handle == "application/json":
            if len(content) < 1:
                return ({"Error":"You need to change at least one property"}, 400)
            prod_key = client.key(constants.product, int(id))
            prod = client.get(key=prod_key)
            if not prod:
                return ({"Error":"No product with this product_id exists"}, 404)
            if owner_sub == prod['owner']:
                if 'name' in content:
                    prod.update({"name": content["name"]})
                if 'type' in content:
                    prod.update({"type": content["type"]})
                if 'price' in content:
                    prod.update({"price": content["price"]})
                if 'quantity' in content:
                    prod.update({"quantity": content["quantity"]})
            
                client.put(prod)
                prod["id"] = str(id)
                prod["self"] = request.url
                
                return (json.dumps(prod, sort_keys=True, indent=4), 200)
            else:
                return ({"Error":"You can only update your product."}, 403)
        else:
            return ({"Error": "Not Acceptable."}, 406)

    elif request.method == 'PUT':
        content = request.get_json()
        accept_handle = str(request.accept_mimetypes)
 
        if not accept_handle:
            return ({"Error": "Not Acceptable."}, 406)
        if accept_handle == "application/json":
            if len(content) != 4:
                return ({"Error":"The request object should have four attributes"}, 400)
            prod_key = client.key(constants.product, int(id))
            prod = client.get(key=prod_key)
            if not prod:
                return ({"Error":"No product with this product_id exists"}, 404)
            if owner_sub == prod['owner']:
                prod.update({"name": content["name"], "type": content["type"], "price": content["price"], "quantity": content["quantity"]})
                
                client.put(prod)
                prod["id"] = str(id)
                prod["self"] = request.url
                return (json.dumps(prod, sort_keys=True, indent=4), 200)
            else:
                return ({"Error":"You can only update your product."}, 403)
        else:
            return ({"Error": "Not Acceptable."}, 406)

    elif request.method == 'DELETE':
        key = client.key(constants.product, int(id))
        prod= client.get(key=key)
        if not prod:
            return ({"Error":"No product with this product_id exists"}, 404)

        if owner_sub == prod['owner']:
            if ("shelf" in prod.keys()) and (prod["shelf"] != None): # if there is "shelf" property in this product.
                
                s_id = prod["shelf"] 
                s_key = client.key(constants.shelf, int(s_id))
                shelf = client.get(key=s_key)
                if not shelf:
                    return ({"Error":"No shelf with this shelf_id exists"}, 404)
            
                for rd in shelf["products"]: 
                    
                    l_key = client.key(constants.product, int(rd))
                    prod = client.get(key=l_key)
                   
                    if int(rd) == int(id):  
                        shelf["products"].remove(rd)
                      
                        client.put(shelf)
                        
            client.delete(key)
        else:
            return ({"Error":"You can only delete your product."}, 403)
        return ('',204)
   
    elif request.method == 'GET':
        accept_handle = str(request.accept_mimetypes)
 
        if not accept_handle:
            return ({"Error": "Not Acceptable."}, 406)
        prod_key = client.key(constants.product, int(id))
        prod= client.get(key=prod_key)
        
        if accept_handle == "application/json":
            if not prod:
                return ({"Error":"No product with this product_id exists"}, 404)
            #As for product, it only shows the owner's product!
            if owner_sub == prod['owner']:
                prod["id"] = str(id)
                prod["self"] = request.url 
                info_shelf ={}
                if ("shelf" in prod) and (prod['shelf'] != None):
                    
                    s_key = client.key(constants.shelf, int(prod["shelf"]))
                    shelf = client.get(key=s_key)
                    if not shelf:
                        return ({"Error":"No shelf with this shelf_id exists"}, 404)
                    info_shelf = {"id": prod['shelf'], "self":request.url_root+ "/shelves/"+str(prod['shelf']), "location": shelf["location"]}

                    prod["shelf"] = info_shelf
                
                return (json.dumps(prod, indent=4, sort_keys=True), 200)
            else:
                return ({"Error":"You can only get your product."}, 403)
        else:
            return ({"Error": "Not Acceptable."}, 406)
    else:
        abort(405)
  