#!/usr/bin/env python3
"""
Hair Color Classification Web Server
Handles image uploads, predictions via Vertex AI endpoint, and product recommendations
"""

import os
import json
import tempfile
import base64
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google.oauth2 import service_account
from google.auth.transport.requests import Request as AuthRequest
import pandas as pd

app = Flask(__name__)
CORS(app)

# Configuration
PROJECT_ID = os.getenv('PROJECT_ID')
LOCATION = os.getenv('LOCATION', 'us-central1')
SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
ENDPOINT_ID = "8435306973250977792"
DEDICATED_ENDPOINT_URL = f"https://{ENDPOINT_ID}.{LOCATION}-{PROJECT_ID}.prediction.vertexai.goog/v1/projects/{PROJECT_ID}/locations/{LOCATION}/endpoints/{ENDPOINT_ID}:predict"

# Initialize credentials
if SERVICE_ACCOUNT_JSON:
    service_account_info = json.loads(SERVICE_ACCOUNT_JSON)
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
else:
    credentials = None

# Load product recommendations (optional - will work without Excel file)
products_df = pd.DataFrame()
EXCEL_PATH = os.getenv('EXCEL_PATH', 'Tones_IBG.xlsx')
if os.path.exists(EXCEL_PATH):
    try:
        products_df = pd.read_excel(EXCEL_PATH)
        print(f"Loaded {len(products_df)} products from Excel file")
    except Exception as e:
        print(f"Warning: Could not load Excel file: {e}")

def get_access_token():
    """Get access token for authentication"""
    if credentials:
        credentials.refresh(AuthRequest())
        return credentials.token
    return None

def predict_hair_color(image_files):
    """Make predictions using the REST API with correct format"""
    try:
        access_token = get_access_token()
        if not access_token:
            raise Exception("Unable to get access token")

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        all_predictions = []

        for idx, image_file in enumerate(image_files):
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file_path = tmp_file.name

            try:
                # Save the uploaded file
                image_file.save(tmp_file_path)

                # Read the image file as bytes and encode to base64
                with open(tmp_file_path, "rb") as f:
                    file_content = f.read()
                    encoded_content = base64.b64encode(file_content).decode("utf-8")

                # Use the correct format from your working curl command
                payload = {
                    "instances": [{
                        "image_bytes": {
                            "b64": encoded_content
                        },
                        "key": f"sample-image-{idx + 1:03d}"
                    }],
                    "parameters": {
                        "confidenceThreshold": 0.5,
                        "maxPredictions": 5
                    }
                }

                print(f"Making REST prediction for image {idx + 1}")
                print(f"Encoded content length: {len(encoded_content)}")
                print(f"Base64 prefix: {encoded_content[:50]}...")
                print(f"URL: {DEDICATED_ENDPOINT_URL}")

                # Make prediction request
                response = requests.post(DEDICATED_ENDPOINT_URL, headers=headers, json=payload)

                if response.status_code != 200:
                    raise Exception(f"Prediction request failed: {response.status_code} - {response.text}")

                prediction_result = response.json()
                all_predictions.append(prediction_result)

                print(f"✅ Success! Got response with {len(prediction_result.get('predictions', []))} predictions")
                print(f"Raw prediction response: {prediction_result}")

            finally:
                # Clean up temp file with better error handling
                try:
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
                except Exception as cleanup_error:
                    print(f"Warning: Could not delete temp file {tmp_file_path}: {cleanup_error}")

        return all_predictions

    except Exception as e:
        print(f"Prediction error: {e}")
        raise

def process_predictions(predictions):
    """Process raw predictions and extract top colors, averaging across multiple images"""
    # Hair color labels from your training data folders
    hair_color_labels = [
        "Shimmer_Ale", "Creamy_Toffee", "Velvet_Rebel", "Spring_Lush", "Fire_Dash",
        "Onyx", "Diamond_Frost", "Marshmellow_Roast", "Copper_Bronze", "Ginger",
        "Auburn_Sugar", "Satin_Caramel", "Raspberry_Ice", "Espresso_Smoke", "Iced_Gold",
        "Ashy_Ribbon", "Honey_Blossom", "Mocha_Chino", "Cayenne_Spice", "Havanna_Roots",
        "Apricot_Amber", "Atomic_Punch", "Cyber_Glam", "Sun_Kissed"
    ]

    # Collect all scores for averaging
    all_scores = []

    for prediction in predictions:
        if 'predictions' in prediction and prediction['predictions']:
            pred = prediction['predictions'][0]
            if 'scores' in pred:
                all_scores.append(pred['scores'])

    if not all_scores:
        return []

    # Average the scores across all images
    avg_scores = []
    num_labels = len(hair_color_labels)

    for i in range(num_labels):
        if i < len(all_scores[0]):  # Make sure index exists
            # Calculate average score for this label across all images
            scores_for_label = [scores[i] for scores in all_scores if i < len(scores)]
            avg_score = sum(scores_for_label) / len(scores_for_label)
            avg_scores.append(avg_score)
        else:
            avg_scores.append(0.0)

    # Create color-confidence pairs using averaged scores
    color_pairs = []
    for i, avg_score in enumerate(avg_scores):
        if i < len(hair_color_labels):
            color_name = hair_color_labels[i]
            color_pairs.append((color_name, avg_score))

    # Sort by confidence and take top colors with confidence > 0.1 (10%)
    color_pairs.sort(key=lambda x: x[1], reverse=True)

    detected_colors = []
    for color_name, confidence in color_pairs[:5]:  # Check top 5
        if confidence > 0.1:
            detected_colors.append({
                'name': color_name,
                'confidence': confidence
            })

    # Return top 2 colors
    final_colors = detected_colors[:2]

    processed_colors_text = [f"{c['name']}: {c['confidence']:.3f}" for c in final_colors]
    print(f"Averaged colors from {len(all_scores)} images: {processed_colors_text}")
    return final_colors

def find_matching_products(detected_colors):
    """Find products that match the detected hair colors"""
    if products_df.empty or not detected_colors:
        return []

    matching_products = []
    color_names = [color['name'].lower().replace(' ', '_') for color in detected_colors]

    for _, product in products_df.iterrows():
        matches = []

        # Check root_tone match
        if pd.notna(product['root_tone']):
            root_tone = str(product['root_tone']).lower().replace(' ', '_')
            if root_tone in color_names:
                matches.append('Root Tone')

        # Check tip_tone match
        if pd.notna(product['tip_tone']):
            tip_tone = str(product['tip_tone']).lower().replace(' ', '_')
            if tip_tone in color_names:
                matches.append('Tip Tone')

        # Check if product name contains any detected color
        product_name_lower = str(product['product_name']).lower()
        for color in detected_colors:
            color_words = color['name'].lower().replace('_', ' ').split()
            if any(word in product_name_lower for word in color_words if len(word) > 3):
                matches.append('Product Name')
                break

        # If we have matches, add the product
        if matches:
            product_info = {
                'sku': str(product['sku']),
                'product_name': str(product['product_name']),
                'match_type': ', '.join(matches),
                'root_tone': str(product['root_tone']) if pd.notna(product['root_tone']) else None,
                'tip_tone': str(product['tip_tone']) if pd.notna(product['tip_tone']) else None,
                'link': str(product['Unnamed: 4']) if pd.notna(product['Unnamed: 4']) else None
            }
            matching_products.append(product_info)

    # Sort by number of matches (prioritize products with more matches)
    matching_products.sort(key=lambda x: len(x['match_type'].split(', ')), reverse=True)

    return matching_products[:5]  # Return top 5 matches

@app.route('/')
def index():
    """Serve the HTML interface"""
    return send_from_directory('.', 'hair_color_classifier.html')

@app.route('/classify', methods=['POST'])
def classify_hair_color():
    """Handle image classification requests"""
    try:
        # Get uploaded images - process only the first one for now
        image_files = []
        for key in request.files:
            if key.startswith('image_'):
                image_files.append(request.files[key])

        if not image_files:
            return jsonify({'error': 'No images provided'}), 400

        # Process up to 3 images
        if len(image_files) > 3:
            image_files = image_files[:3]
        print(f"Processing {len(image_files)} images")

        # Make predictions
        print(f"Processing {len(image_files)} images...")
        predictions = predict_hair_color(image_files)

        # Process predictions to get detected colors
        detected_colors = process_predictions(predictions)
        print(f"Detected colors: {detected_colors}")

        # Find matching products
        matching_products = find_matching_products(detected_colors)
        print(f"Found {len(matching_products)} matching products")

        # Return results
        return jsonify({
            'colors': detected_colors,
            'products': matching_products,
            'total_images': len(image_files)
        })

    except Exception as e:
        print(f"Classification error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'endpoint_id': ENDPOINT_ID})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("Starting Hair Color Classification Server...")
    print(f"Project ID: {PROJECT_ID}")
    print(f"Endpoint ID: {ENDPOINT_ID}")
    print(f"Products loaded: {len(products_df)}")
    print(f"Server running on port {port}")

    app.run(debug=False, host='0.0.0.0', port=port)