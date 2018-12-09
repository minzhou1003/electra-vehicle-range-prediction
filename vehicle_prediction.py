#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Min Zhou'
__copyright__ = 'Copyright 2018, electra-vehicle-range-prediction'
__email__ = 'minzhou@bu.edu'

"""
This is a vehicle range prediction API.
"""


import os
import sys

import pickle
import numpy as np
from ast import literal_eval
import pandas as pd
import json
import re

model_names = {
    1: 'rf_model.sav',
    2: 'knn_model.sav',
    3: 'tree_model.sav',
    4: 'ols_model.sav'}


def load_trained_model(model_name):

    filename = 'trained_models/' + model_name
    # load the model from trained models
    try:
        loaded_model = pickle.load(open(filename, 'rb'))
        print(f'{model_name} loaded!')
    except:
        print('Failed to load model. Please try again.')
        sys.exit(1)
    return loaded_model

def save_all_json_file_paths(data_folder, num_of_files):

    count = 0
    json_files = []
    for file in os.listdir(data_folder):
        
        json_files.append(os.path.join(data_folder, file))
        count += 1
        if count == num_of_files:
            break
    print('\nJSON file path saved.')
    return json_files


def read_json_files(json_files):

    feature_list = []
    for file_name in json_files:
        try:
            print(file_name)
            with open(file_name) as data_file:
                json_file = json.load(data_file)
                python_dict = literal_eval(json_file)
                df = pd.DataFrame.from_dict(python_dict)
                python_dict_input = json.loads(df.input[0])

                # HPU and HEU specifications
                df_hpu_heu = pd.DataFrame(python_dict_input, columns=['HPU', 'HEU'])
                df_hpu_heu_series = df_hpu_heu.T[['cost_per_cell', 'nominal_energy', 'cell_mass']].stack()

                # vehicle input variables
                df_vehicle = pd.DataFrame(python_dict_input, columns=['vehicle'])
                df_vehicle_series = df_vehicle.T[['chassisMassMinBatteryMass', 'dragResistance', 
                                                'frontalArea', 'rollingResistance', 'powerTrainEff']].stack()
                # system specifications
                df_spec_series = df.specifications[['system_cost', 'system_weight', 
                                                    'HEU_max_power', 'HPU_max_power', 'num_HEU', 
                                                    'num_HPU', 'dP_threshold', 'system_range']]
                # concate all features
                feature_series = pd.concat([df_spec_series, df_hpu_heu_series, df_vehicle_series])
                feature_list.append(feature_series)
        except:
            print('\nFailed to read the JSON file. Please try again.')
            sys.exit(1)
    print('\nSuccessfully read the JSON file.')
    return feature_list




def prepare_test_data(feature_list):

    features = pd.concat(feature_list, axis=1, sort=False).T
    feature_name_list = features.columns.values.tolist()
    feature_name_list = [re.sub(r'[^\w\s]','',str(name).replace(' ', '_')) for name in feature_name_list]
    features.columns = feature_name_list

    # Add new features
    features['system_cost_per_kg'] = features['system_cost']/features['system_weight']
    features['HPU_power_per_kg'] = features['HPU_max_power']/features['HPU_cell_mass']
    features['HEU_power_per_kg'] = features['HEU_max_power']/features['HEU_cell_mass']
    features['HPU_cost_per_kw'] = features['HPU_cost_per_cell']/features['HPU_max_power']
    features['HEU_cost_per_kw'] = features['HEU_cost_per_cell']/features['HEU_max_power']
    new_features = features.drop(['system_cost', 'system_weight', 'HPU_max_power', 'HPU_cell_mass', 
               'HEU_cell_mass', 'HPU_cost_per_cell',
               'HEU_cost_per_cell', 'HEU_max_power', 'vehicle_powerTrainEff'], axis=1)

    input_df = new_features.drop(['system_range'], axis=1)
    X = input_df.values.astype(float)
    print(f'\nSuccessfully extracted the 14 features, and the input shape: {X.shape}.')
    return X

def main():

    # select and load the model
    print('Please put the JSON file to "new_data" folder.')
    try:
        model_index = int(input('\nSelect the model:\n1. RandomForest 2. KNN 3. DecisionTree 4.OLS\n'))
        num_of_files = int(input('\nEnter the number of JSON files you would like to predict: '))
    except:
        print('Please enter the correct integer. Please try again.')
        sys.exit(1)

    model_name = model_names[model_index]
    loaded_model = load_trained_model(model_name)


    # Preprocess the features
    json_files = save_all_json_file_paths('new_data', num_of_files)
    feature_list = read_json_files(json_files)
    X = prepare_test_data(feature_list)

    # Predict the vehicle range
    result = loaded_model.predict(X)
    for res in result:
        print(f'\nThe predicted system range is {res}.')


if __name__ == '__main__':
    main()
