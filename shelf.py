from flask import Blueprint, request, abort
from google.cloud import datastore
import json
import constants

client = datastore.Client()

#logger = logging.getLogger(__name__)
bp = Blueprint('shelf', __name__, url_prefix='/shelves')

@bp.app_errorhandler(405)
def method_not_allowed(e):
    return ({"Error":"Method not recognized"}, 405)

@bp.route('', methods=['POST','GET'])
def shelf_get_post():
    accept_handle = str(request.accept_mimetypes)    
    if not accept_handle:
        return ({"Error": "Not Acceptable."}, 406)
        
    if request.method == 'POST':
        content = request.get_json()
        
        
        if accept_handle == "application/json":
            if len(content) != 4:
                return ({"Error":"The request object should have four attributes"}, 400)
            
            else:
                new_shelf = datastore.entity.Entity(key=client.key(constants.shelf))
                new_shelf.update({"name": content["name"], "location": content["location"], "size": content["size"], "phone": content["phone"]})
                client.put(new_shelf)
                output = {"id":str(new_shelf.key.id), "name": content["name"], "location": content["location"], "size": content["size"],
                "phone": content["phone"], "self":request.url + "/"+str(new_shelf.key.id)}
            
                return (json.dumps(output, sort_keys=True, indent=4), 201)
        else:
            return ({"Error": "Not Acceptable."}, 406)
            
    elif request.method == 'GET':
        query = client.query(kind=constants.shelf)
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        l_iterator = query.fetch(limit= q_limit, offset=q_offset)
        res = list(query.fetch())
        total = len(res)

        pages = l_iterator.pages
        results = list(next(pages))
        
        if accept_handle == "application/json":
            if l_iterator.next_page_token:
                next_offset = q_offset + q_limit
                next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
            else:
                next_url = None
            for e in results: 
                e["id"] = e.key.id
                e["self"] = request.url+"/"+str(e["id"])
                list_products=[]
                if ("products" in e) and (e["products"] != None):
                    
                    for  pd in e['products']:
                        
                        prod_key = client.key(constants.product, int(pd))
                        product = client.get(key=prod_key)
                        # Below won't usually need but for some cases, I added it in 3 places including below.
                        if not product:
                            return ({"Error":"No product with this product_id exists"}, 404)
                        new_prod = {"id": str(pd), "self":request.url_root+ "/products/"+str(pd), "name": product["name"]}
                        list_products.append(new_prod)
                        
                    e["products"] = list_products
            #length = len(results)
            #output = {"total of shelves": len(res)}  
            output = {"total of shelves": total, "shelves": results}
            if next_url:
                output["next"] = next_url
                
            return (json.dumps(output, sort_keys=True, indent=4), 200)
        else:
            return ({"Error": "Not Acceptable."}, 406)
    else:
        #return ({"Error":"Method not recognized"}, 405)
        abort(405)

@bp.route('/<id>', methods=['PATCH','PUT','DELETE', 'GET'])
def update_get_delete(id):
    

    if request.method == 'PATCH':
        content = request.get_json()

        accept_handle = str(request.accept_mimetypes)
        if not accept_handle:
            return ({"Error": "Not Acceptable."}, 406)
        
        if accept_handle == "application/json":
            if len(content) < 1:
                return ({"Error":"You need to change at least one property"}, 400)
            shelf_key = client.key(constants.shelf, int(id))
            shelf = client.get(key=shelf_key)
            if not shelf:
                return ({"Error":"No shelf with this shelf_id exists"}, 404)
            if 'name' in content:
                shelf.update({"name": content["name"]})
            if 'location' in content:
                shelf.update({"location": content["location"]})
            if 'size' in content:
                shelf.update({"size": content["size"]})
            if 'phone' in content:
                shelf.update({"phone": content["phone"]})
            
            client.put(shelf)
            shelf["id"] = str(id)
            shelf["self"] = request.url

            return (json.dumps(shelf, sort_keys=True, indent=4), 200)
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
            shelf_key = client.key(constants.shelf, int(id))
            shelf = client.get(key=shelf_key)
            if not shelf:
                return ({"Error":"No shelf with this shelf_id exists"}, 404)
            shelf.update({"name": content["name"], "location": content["location"], "size": content["size"], "phone": content["phone"]})
            client.put(shelf)
            shelf["id"] = str(id)
            shelf["self"] = request.url
            return (json.dumps(shelf, sort_keys=True, indent=4), 200)
        else:
            return ({"Error": "Not Acceptable."}, 406)

    elif request.method == 'DELETE':
        key = client.key(constants.shelf, int(id))
        shelf= client.get(key=key)
        if not shelf:
            return ({"Error":"No shelf with this shelf_id exists"}, 404)
        if "products" in shelf.keys():
            for pd in shelf["products"]:
                
                s_key = client.key(constants.product, int(pd))
                products = client.get(key=s_key)
                products.update({"shelf": None})
                client.put(products)
        client.delete(key)
        return ('',204)

    elif request.method == 'GET':
        accept_handle = str(request.accept_mimetypes)
        if not accept_handle:
            return ({"Error": "Not Acceptable."}, 406)
        shelf_key = client.key(constants.shelf, int(id))
        shelf= client.get(key=shelf_key)
        
        if accept_handle == "application/json":
            if not shelf:
                return ({"Error":"No shelf with this shelf_id exists"}, 404)
            shelf["id"] = str(id)
            shelf["self"] = request.url 
            list_products=[]
            if ("products" in shelf) and shelf["products"] != None:
                    
                for pd in shelf['products']:
                    #new_prod = {"id": str(pd), "self":request.url_root+ "/products/"+str(pd)}
                    prod_key = client.key(constants.product, int(pd))
                    product = client.get(key=prod_key)
                    if not product:
                        return ({"Error":"No product with this product_id exists"}, 404)
                    new_prod = {"id": str(pd), "self":request.url_root+ "/products/"+str(pd), "name": product["name"]}
                        
                    list_products.append(new_prod)
                shelf["products"] = list_products
            #client.put(boats)
            return (json.dumps(shelf, indent=4, sort_keys=True), 200)
        else:
            return ({"Error": "Not Acceptable."}, 406)
    else:
        abort(405)

@bp.route('/<sid>/products/<pid>', methods=['PUT','DELETE'])
def add_delete_freight(sid,pid):
    if request.method == 'PUT':
        shelf_key = client.key(constants.shelf, int(sid))
        shelf = client.get(key=shelf_key)
        prod_key = client.key(constants.product, int(pid))
        prod = client.get(key=prod_key)
        if (not shelf) or (not prod):
            return ({"Error":"The specified shelf and/or product don’t exist"}, 404)
        if ('shelf' in prod) and (prod['shelf'] != None):
            return ({"Error":"This product is already stored in another shelf."}, 403)

        if 'products' in shelf.keys():
            shelf['products'].append(prod.id)
        else:
            shelf['products']=[prod.id]
            
        client.put(shelf)

        if ('shelf' not in prod.keys()):
            prod['shelf'] = shelf.id
        else:
            prod['shelf'] = shelf.id
            
        client.put(prod)
        return('',204)
    elif request.method == 'DELETE':
        shelf_key = client.key(constants.shelf, int(sid))
        shelf = client.get(key=shelf_key)
        prod_key = client.key(constants.product, int(pid))
        prod = client.get(key=prod_key)

        if (not shelf) or (not prod):
            return ({"Error":"The specified shelf and/or product don’t exist"}, 404)

        if int(prod['shelf']) != int(sid):
            return ({"Error":"The shelf and product doesn't match"}, 403)

        if 'products' in shelf.keys():
            shelf['products'].remove(prod.id)
            client.put(shelf)
        
        if 'shelf' in prod.keys():
            prod['shelf'] = None
            client.put(prod)
        
        return('',204)
    
    else:
        abort(405)
'''
Below is not required for the final, but I want to add this.
'''
@bp.route('/<id>/products', methods=['GET'])
def get_freight(id):
    if request.method == 'GET':
        accept_handle = str(request.accept_mimetypes)
        if not accept_handle:
            return ({"Error": "Not Acceptable."}, 406)

        if accept_handle == "application/json":

            s_key = client.key(constants.shelf, int(id))
            shelf = client.get(key=s_key)
            if not shelf:
                return ({"Error":"No shelf with this shelf_id exists"}, 404)

            prod_list  = []
            if 'products' in shelf.keys():
                for lid in shelf['products']: 
                    #add_ld = {"self": request.url_root +"loads/"+str(lid), "id": str(lid)}
                    prod_key = client.key(constants.product, int(lid))
                    product = client.get(key=prod_key)
                    add_ld = {"id": str(lid), "self":request.url_root+ "/products/"+str(lid), "name": product["name"]}

                    prod_list.append(add_ld)
                return json.dumps(prod_list, indent=4, sort_keys=True)
            else:
                return json.dumps([])
        else:
            return ({"Error": "Not Acceptable."}, 406)
    else:
        abort(405)
