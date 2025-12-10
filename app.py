from flask import Flask, request, jsonify
from flask_cors import CORS  # <--- IMPORT THIS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)  # <--- ENABLE CORS FOR ALL ROUTES

# --- CONFIGURATION ---
DATA_FILE = "crop_production.csv"

# Global variable to store the dataframe
df = None

def load_data():
    """Loads the CSV data into memory on startup."""
    global df
    if os.path.exists(DATA_FILE):
        print("Loading dataset...")
        try:
            df = pd.read_csv(DATA_FILE)
            # Drop rows where Production is missing (NaN)
            df = df.dropna(subset=['Production'])
            print("Dataset loaded successfully.")
        except Exception as e:
            print(f"Error loading CSV: {e}")
    else:
        print("Error: 'crop_production.csv' not found.")

# Load data immediately when app starts
load_data()

@app.route('/')
def home():
    return "AgroAI Backend is Running with CORS! Use /api/leading-state?crop=Rice"

@app.route('/api/leading-state', methods=['GET'])
def get_leading_state():
    """
    API Endpoint: Get the leading state for a specific crop year-wise.
    Usage: /api/leading-state?crop=Rice
    """
    global df
    if df is None:
        # Try loading again if it failed continuously (optional fallback)
        load_data()
        if df is None:
            return jsonify({"error": "Dataset not loaded on server."}), 500

    crop_name = request.args.get('crop')
    
    if not crop_name:
        return jsonify({"error": "Please provide a crop name. Example: ?crop=Rice"}), 400

    # 1. Filter for the specific crop (Case insensitive)
    try:
        crop_data = df[df['Crop'].str.lower() == crop_name.lower().strip()]
    except Exception as e:
        return jsonify({"error": "Error processing data."}), 500
    
    if crop_data.empty:
        return jsonify({"message": f"No data found for crop: {crop_name}"}), 404

    # 2. Find the Leading State for each Year
    try:
        # Group by Year -> Find index of Max Production -> Select those rows
        idx = crop_data.groupby('Crop_Year')['Production'].idxmax()
        leading_states = crop_data.loc[idx]
        
        # 3. Clean up the result
        #    Select only relevant columns and sort by year
        result_df = leading_states[['Crop_Year', 'State_Name', 'Production']].sort_values('Crop_Year')
        
        # Convert to JSON format
        result_json = result_df.to_dict(orient='records')
        
        return jsonify({
            "crop": crop_name,
            "data": result_json
        })
    except Exception as e:
        return jsonify({"error": f"Error calculating statistics: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
