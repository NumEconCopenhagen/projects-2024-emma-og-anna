%pip install git+https://github.com/alemartinello/dstapi
%pip install pandas-datareader

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ipywidgets as widgets
from matplotlib_venn import venn2
import json
import pandas_datareader
from dstapi import DstApi

'''Importing data from Jobindsats JSON file'''
with open('International Labor.json', 'r') as f:
    int_data = json.load(f)
int_lb = pd.DataFrame(int_data)

def clean_json_data():
    ''' Defining a callable function to use for cleaning our JSON data file '''
    print(f'Before cleaning, the JSON datafile from JobIndsats contains {int_lb.shape[0]} observations and {int_lb.shape[1]} variables.')

    # Copying the DataFrame, which we will clean, incase we need the original data.
    int_lb_copy = int_lb.copy()

    # As we've only extracted the data from 2014 and after, we do not need to drop any time-dependent variables.
    # First, we don't need the second and last column, so we drop these:
    int_lb_copy.drop(1, axis=1, inplace=True)
    int_lb_copy.drop(4, axis=1, inplace=True)

    # The columns are currently named 0,1,...,4. This doesn't say a lot, so we rename all columns:
    int_lb_copy.rename(columns = {0:'time'}, inplace=True)
    int_lb_copy.rename(columns= {2:'industry'}, inplace=True)
    int_lb_copy.rename(columns={3:'int_empl'}, inplace=True)

    print('We have removed two columns and renamed the remaining.')
    print(f'The dataset now contains {int_lb_copy.shape[0]} observations and {int_lb_copy.shape[1]} variables.')

    # Our observations for international employment are currently in the 'string' format. We want them to be numbers.
    string_empl = int_lb_copy['int_empl']
    print(f'All our observations are of type: {type(string_empl[0])}. We want them to be integers.')

    # All our observations are written as Danish 1000, e.g. 2.184 which is supposed to be 2184 and not decimals. 
    # The '.' means we can't convert the numbers directly to integers so we convert them to floats first:
    float_empl = string_empl.astype(float)
    print(f'The observations are now of type: {type(float_empl[0])} and the first observation is: {float_empl[0]}')

    # Next we multiply all observations by 1000 and convert to integers:
    inter_empl = float_empl.multiply(1000).astype(int)
    print(f'The observations are now of type: {type(inter_empl[0])} and the first observation is: {inter_empl[0]}')
    
    # Lastly, we replace the string format of the original series and replace it with the new integer series:
    int_lb_copy['int_empl'] = inter_empl

    # We would like to sort our data by time. To be able to do so, we convert the 'time' variable into datetime variables.
    # All our variables are in the format 'month, year' but in Danish. So we need to translate the 'Time' values from Danish to English
    int_lb_copy['time'] = int_lb_copy['time'].str.replace("Maj", "May")
    int_lb_copy['time'] = int_lb_copy['time'].str.replace("Okt", "Oct")

    # Now we can convert our 'Time' variable into a datetime_variable.
    print('We convert our time Variable into datetime variables.')
    int_lb_copy['time'] = pd.to_datetime(int_lb_copy['time'], format='%b %Y')
    int_lb_copy['time'] = int_lb_copy['time'].dt.strftime('%YM%m')

    # We now sort through the data, first by time.
    int_lb_copy.sort_values(by='time')
    print('We now convert the DataFrame using the .pivot method, using time as index, industries as columns and international labor as our observations.')
    int_lb_pivot = int_lb_copy.pivot(index='time', columns='industry', values='int_empl')

    # The industries are still in Danish, rename to English and in line with our data from DST:
    print('All our industries are in Danish, so we rename them to English.')
    int_lb_pivot.rename(columns={'Andre serviceydelser  mv.':'other_services'}, inplace=True)
    int_lb_pivot.rename(columns={'Ejendomshandel og udlejning':'real_estate'}, inplace=True)
    int_lb_pivot.rename(columns={'Finansiering og forsikring':'finance_insurance'}, inplace=True)
    int_lb_pivot.rename(columns={'Hoteller og restauranter':'hotels_restaurents'}, inplace=True)
    int_lb_pivot.rename(columns={'Information og kommunikation':'information_communictaion'}, inplace=True)
    int_lb_pivot.rename(columns={'Kultur og fritid':'culture_leisure'}, inplace=True)
    int_lb_pivot.rename(columns={'Rejsebureau, rengøring o.a. operationel service':'cleaning_etc'}, inplace=True)
    int_lb_pivot.rename(columns={'Transport':'transport'}, inplace=True)
    int_lb_pivot.rename(columns={'Videnservice':'research_consultancy'}, inplace=True)

    # The dataset on the service industry from DST conatins the totalt and 7 sub-industries.
    # Our dataset above contains 9 sub-industries but not the total. 
    # We therefor need to add all observations togteher to create the total:
    print('For our dataset to match the data from DST, we sum over all industries to get the total and combine four of the industires so that they match')
    int_lb_pivot['total'] = int_lb_pivot.sum(axis=1)

    # Now we combine the observations of 'finance and insurance' with 'real estate':
    int_lb_pivot['finance_real_estate'] = int_lb_pivot['finance_insurance'] + int_lb_pivot['real_estate']

    # We combine the observations of 'culture and leisure' with 'other services':
    int_lb_pivot['culture_leisure_other'] = int_lb_pivot['other_services'] + int_lb_pivot['culture_leisure']

    # Make a final copy, incase we need the original data before dropping the last columns
    print('Lastly, we drop the industries, that we have just combined to make new ones.')
    int_lb_cleaned = int_lb_pivot.copy()
    int_lb_cleaned.drop('finance_insurance', axis=1, inplace=True)
    int_lb_cleaned.drop('real_estate', axis=1, inplace=True)
    int_lb_cleaned.drop('other_services', axis=1, inplace=True)
    int_lb_cleaned.drop('culture_leisure', axis=1, inplace=True)

    print(f'The cleaned dataset now contains 8 columns (industries) and {int_lb_cleaned.shape[0]} observations')

    return int_lb_cleaned

def clean_dst_empl():
    ''' Defining a callable function to use for cleaning our data from DST '''
    employees = DstApi('LBESK03')

    print(f'Before cleaning, the data from DST contains {employees.shape[0]} observations and {employees.shape[1]} variables.')
    print(f'Since we have extracted all the data from the source on DST, we need to select only the variables that are relevant for our analysis'.)
    
    params = employees._define_base_params(language='en')

    # For the employment data, we first define our parameters so that we get only data from january 2014 to january 2024.
    params = {'table': 'LBESK03',
    'format': 'BULK',
    'lang': 'en',
    'variables': [{'code': 'BRANCHEDB071038', 'values': ['*']},
    {'code': 'Tid', 'values': ['>2013M12<=2024M01']}]}

    # Then, we retract the data we defined, drop the column of industry since we do not need it and rename the columns to english, simple titles.
    empl = employees.get_data(params=params)
    empl.drop(['BRANCHEDB071038'], axis=1, inplace=True)
    empl.rename(columns = {'INDHOLD':'employees', 'TID':'time'}, inplace=True)

    return empl

