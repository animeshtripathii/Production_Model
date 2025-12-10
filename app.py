from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

# Load the Model
MODEL_FILE = "agro_model.json"
model_knowledge = {}

if os.path.exists(MODEL_FILE):
    with open(MODEL_FILE, "r") as f:
        model_knowledge = json.load(f)
    print("Model loaded successfully.")
else:
    print("Error: agro_model.json not found.")

@app.route('/')
def home():
    return "AgroAI ML Model is Running!"

@app.route('/predict', methods=['GET'])
def predict():
    # 1. Get User Input (e.g., ?crop=Rice)
    crop = request.args.get('crop')
    
    if not crop:
        return jsonify({"error": "Please provide a crop name"}), 400
    
    # 2. Ask the Model
    #    (Normalize input: lowercase and strip spaces)
    crop_key = crop.lower().strip()
    result = model_knowledge.get(crop_key)
    
    if result:
        return jsonify({
            "crop": crop,
            "prediction": result
        })
    else:
        return jsonify({
            "error": f"Crop '{crop}' not found in model."
        }), 404

if __name__ == '__main__':
    app.run(debug=True)
