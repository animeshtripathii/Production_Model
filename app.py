from flask import Flask, request, jsonify
import joblib
import pandas as pd
import numpy as np
import os

app = Flask(__name__)

# --- 1. Load Model (for when full data is provided) ---
try:
    model = joblib.load('model.pkl')
    print("✅ Model loaded successfully.")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None

# --- 2. Load Dataset (for Major Producer lookup) ---
try:
    # Ensure crop.xlsx is in the same folder
    df_context = pd.read_excel('crop.xlsx', header=None)
    df_context.columns = ['Crop', 'Crop_Year', 'Season', 'State', 'Area', 'Annual_Rainfall', 'Fertilizer', 'Pesticide', 'Production', 'Yield']
    
    # Create a quick lookup dictionary: {'Rice': 'Punjab', 'Banana': 'Kerala'}
    producer_map = {}
    unique_crops = df_context['Crop'].unique()
    for crop in unique_crops:
        crop_data = df_context[df_context['Crop'] == crop]
        # Sum production to find the top state
        state_production = crop_data.groupby('State')['Production'].sum().sort_values(ascending=False)
        if not state_production.empty:
            producer_map[crop] = state_production.index[0]
            
    print("✅ Major Producers mapped.")
except Exception as e:
    print(f"❌ Error loading dataset: {e}")
    producer_map = {}

@app.route('/')
def home():
    return "AgroAI API Running."

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        crop_name = data.get('Crop')

        if not crop_name:
            return jsonify({'error': 'Crop name is required'}), 400

        # --- PART A: Get Major Producer (Always works) ---
        # Look up the crop in our map, default to "Unknown" if not found
        major_producer = producer_map.get(crop_name, "Data not available for this crop")

        response = {
            'status': 'success',
            'insight': {
                'crop': crop_name,
                'major_producer_state': major_producer,
                'message': f"The largest producer of {crop_name} in India is {major_producer}."
            }
        }

        # --- PART B: Check if we can do ML Prediction ---
        # We need specific fields to run the model
        required_fields = ['Crop_Year', 'Season', 'State', 'Area', 'Annual_Rainfall', 'Fertilizer', 'Pesticide']
        
        # Check if all required fields are present in the request
        if all(field in data for field in required_fields) and model:
            # All data is present, run the ML model
            input_data = {
                'Crop': [crop_name],
                'Crop_Year': [int(data.get('Crop_Year'))],
                'Season': [data.get('Season')],
                'State': [data.get('State')],
                'Area': [float(data.get('Area'))],
                'Annual_Rainfall': [float(data.get('Annual_Rainfall'))],
                'Fertilizer': [float(data.get('Fertilizer'))],
                'Pesticide': [float(data.get('Pesticide'))]
            }
            df_input = pd.DataFrame(input_data)
            prediction = model.predict(df_input)
            
            # Add prediction to response
            response['prediction'] = {
                'yield': float(prediction[0]),
                'unit': 'Production/Area'
            }
        else:
            # Data missing, skip ML
            response['prediction'] = None
            response['note'] = "Yield prediction skipped. To get yield, provide: Year, Season, State, Area, Rainfall, Fertilizer, Pesticide."

        return jsonify(response)

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
