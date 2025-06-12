from flask import Blueprint, render_template, request, jsonify
import json
from .utils import load_data, search_artist

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('index.html')

@main.route('/search', methods=['GET'])
def search():
    artist_name = request.args.get('artist')
    data = load_data()
    results = search_artist(data, artist_name)
    return jsonify(results)