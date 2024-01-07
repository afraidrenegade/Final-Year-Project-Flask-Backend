from flask import Flask, request, jsonify
import pandas as pd
from fuzzywuzzy import fuzz

app = Flask(__name__)

# Load the dataset
file_path = 'csv/crop_GI.csv'
data_location_path = 'csv/crop_L.csv'
data_location = pd.read_csv(data_location_path)
data = pd.read_csv(file_path)

# Drop rows with missing 'GI' values
data_cleaned = data.dropna(subset=['GI'])

# Define ranges for blood sugar categories
low_range = 70
medium_range_start = 55

# Create an empty list to store blood sugar labels
blood_sugar_labels = []

# Iterate through each row and assign blood sugar labels
for index, row in data_cleaned.iterrows():
    gi = row['GI']
    if gi <= 54:
        blood_sugar_labels.append('h')
    elif 55 <= gi <= 69:
        blood_sugar_labels.append('m')
    else:
        blood_sugar_labels.append('l')

# Add the blood sugar labels to the DataFrame
data_cleaned['Type'] = blood_sugar_labels

# Display the updated DataFrame with selected columns
selected_columns = ['FOOD NAME', 'GI', 'FATCE', 'ENERGY', 'WATER', 'PROTCNT', 'FIBTG', 'CA', 'Type', 'CA', 'MG', 'P', 'K', 'NA', 'ZN', 'FE', 'CHOLESTEROL', 'VITA_RAE', 'VITA', 'RETOL', 'VITB12', 'VITC', 'THIA']
selected_data = data_cleaned[selected_columns]


# Define endpoint for blood sugar prediction
@app.route('/predict_food', methods=['POST'])
def predict_food():
    # Get blood sugar level from request
    blood_sugar_level = request.json['blood_sugar_level']
    # Get user location from request
    user_location = request.json['location']
    user_location = user_location.replace('County', '').strip()

    # Determine blood sugar category
    if blood_sugar_level <= 3.9:
        category = 'l'
    elif 4 <= blood_sugar_level <= 5.5:
        category = 'm'
    else:
        category = 'h'

    # Filter selected_data based on blood sugar category
    recommended_foods_data = selected_data[selected_data['Type'] == category]

    # Filter data_location based on user's location (county)
    county_data = data_location[data_location['admin2'] == user_location]

    # Extract relevant columns for matching
    county_commodities = county_data['commodity'].tolist()

    # Perform fuzzy matching with recommended foods
    matches = [(food, max(fuzz.ratio(food, commodity) for commodity in county_commodities)) for food in recommended_foods_data['FOOD NAME']]

    # Set a threshold for similarity score (adjust as needed)
    threshold = 50

    # Filter matches above the threshold
    matched_crops = [match[0] for match in matches if match[1] >= threshold]

    # Filter unmatched crops
    unmatched_crops = list(set(recommended_foods_data['FOOD NAME']) - set(matched_crops))

    # Extract relevant columns for the response
    response_columns = ['FOOD NAME', 'GI', 'FATCE', 'ENERGY', 'WATER', 'PROTCNT', 'FIBTG', 'CA', 'Type', 'CA', 'MG', 'P', 'K', 'NA', 'ZN', 'FE', 'CHOLESTEROL', 'VITA_RAE', 'VITA', 'RETOL', 'VITB12', 'VITC', 'THIA']

    # Prepare response data for foods from the user's county
    from_your_county_data = replace_empty_with_symbol(recommended_foods_data[recommended_foods_data['FOOD NAME'].isin(matched_crops)][response_columns].to_dict(orient='records'), symbol='-')

    # Prepare response data for foods not from the user's county
    not_from_your_county_data = replace_empty_with_symbol(recommended_foods_data[recommended_foods_data['FOOD NAME'].isin(unmatched_crops)][response_columns].to_dict(orient='records'), symbol='-')

    # Return the list of recommended foods from the user's county, not from the user's county, matched crops, and unmatched crops
    return jsonify({
        'from_your_county': from_your_county_data,
        'not_from_your_county': not_from_your_county_data
    })

def replace_empty_with_symbol(records, symbol='-'):
    # Iterate through each record and replace empty values with the specified symbol
    for record in records:
        for key, value in record.items():
            if pd.isnull(value):
                record[key] = symbol
    return records

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)