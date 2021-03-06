import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

# ROUTES
@app.route('/drinks')
def get_drinks():
    """Get all drinks public endpoint"""

    try:
        # query and format all drinks
        drinks = Drink.query.all()
        formatted_drinks = [drink.short() for drink in drinks]

        # return resonse if successful
        return jsonify({
            'success': True,
            'drinks': formatted_drinks,
        }), 200

    except Exception:
        # return internal server error
        abort(500)


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(token):
    """Get the details of a specific drink"""
    try:
        # Query and format drinks
        drinks = Drink.query.all()
        formatted_drinks = [drink.long() for drink in drinks]

        # return long() formatted response
        return jsonify({
            'success': True,
            'drinks': formatted_drinks,
        }), 200

    except Exception:
        abort(500)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(jwt):
    """creates a new drink"""
    try:
        # get response data
        data = request.get_json()
        title = data.get('title', None)
        recipe = data.get('recipe', None)

        # inserts a new drink
        drink = Drink(title=title, recipe=json.dumps(recipe))
        drink.insert()

        # return success response
        return jsonify({
            'success': True,
            'drinks': drink.long(),
        }), 200
    except Exception:
        abort(422)


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drink(jwt, drink_id):
    """updates a drink in database"""

    # get response data from client
    data = request.get_json()
    title = data.get('title', None)

    # query for drink by id
    drink = Drink.query.filter_by(id=drink_id).one_or_none()

    # returns a 404 error if drink is not found
    if drink is None:
        abort(404)

    # returns a 400 error if no title is sent
    if title is None:
        abort(400)

    try:
        # update drink in the database
        drink.title = title
        drink.update()

        # return success response
        return jsonify({
            'success': True,
            'drinks': [drink.long()],
        })
    except Exception:
        abort(422)


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, drink_id):
    """deletes a drink from the database"""

    # query for drink by id
    drink = Drink.query.filter_by(id=drink_id).one_or_none()

    # return 404 if drink is not found
    if drink is None:
        abort(404)

    try:
        # Delete drink from database
        drink.delete()

        # return 200 and id of deleted drink id
        return jsonify({
            'success': True,
            'deleted': drink_id,
        })
    except Exception:
        abort(422)


# Error Handling
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
        }), 422


@app.errorhandler(404)
def resource_not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "internal server error"
    }), 500


@app.errorhandler(AuthError)
def handle_auth_error(exception):
    response = jsonify(exception.error)
    response.status_code = exception.status_code
    return response
