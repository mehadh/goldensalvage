import pandas as pd
import os, sys
import json
os.chdir(sys.path[0])

import pandas as pd
import os, sys
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pytz
from datetime import datetime as dTime
import time
import googleapiclient.errors
from sheetFormat import find_latest_file

# Constants
SERVICE_ACCOUNT_FILE = 'gkey.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1zKOaioAQzaGsgEJtt_q27IsVTzQZnMS4cjlYr3T2RX4'
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)
SHEET_NAME = 'Sheet1'  # Ensure this is your sheet name

def find_and_update_row(service, vehicle_data_list, spreadsheet_id, sheet_name):
    # Fetch the current VINs from the spreadsheet to find the rows that need updating
    range_to_read = f'{sheet_name}!B2:B'
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_to_read).execute()
    existing_vins = result.get('values', [])
    existing_vins = [item[0] for item in existing_vins if item]  # Flatten list

    # Map VINs to their data
    vin_to_data_map = {vehicle['vin']: vehicle for vehicle in vehicle_data_list}
    requests = []
    delete = []
    # Check and update rows where VINs match
    for index, vin in enumerate(existing_vins):
        row_number = index + 2  # Calculate the row number based on index
        if vin in vin_to_data_map:
            vehicle_data = vin_to_data_map[vin]
            
            # Update the Google Sheet with the 'yard' and 'sDate' from the vehicle data
            update_range = f'{sheet_name}!F{row_number}:G{row_number}'
            saleTime = format_datetime(vehicle_data['sDate'], vehicle_data['sTime'])
            values = [
                [
                    vehicle_data['yard'],  # Column F: Yard
                    saleTime
                ]
            ]
            body = {'values': values}
            try:
                # Send the update request to Google Sheets
                # service.spreadsheets().values().update(
                #     spreadsheetId=spreadsheet_id, range=update_range,
                #     valueInputOption='USER_ENTERED', body=body).execute()
                requests.append({
                "updateCells": {
                    "range": {
                        #"sheetId": spreadsheet_id,
                        "startRowIndex": row_number - 1,
                        "endRowIndex": row_number,
                        "startColumnIndex": 5,  # Column F
                        "endColumnIndex": 7   # Column G
                    },
                    "rows": [
                        {"values": [{"userEnteredValue": {"stringValue": vehicle_data['yard']}},
                                    {"userEnteredValue": {"stringValue": saleTime}}]}
                    ],
                    "fields": "userEnteredValue"
                }
            })

                print(f"Want to update row {row_number} for VIN {vin}")
            except Exception as e:
                print(e)
                print("11 except 11")
            #except googleapiclient.errors.HttpError as e:
            #    if e.resp.status == 429:
                    # You've hit the rate limit, pause the execution for 100 seconds
            #        print("Rate limit exceeded, pausing for 100 seconds...")
            #        time.sleep(100)
                    # Try to update again
                    # service.spreadsheets().values().update(
                    #     spreadsheetId=spreadsheet_id, range=update_range,
                    #     valueInputOption='USER_ENTERED', body=body).execute()
            # To prevent hitting the rate limit, wait for 1 second after each write operation
            #time.sleep(1)
        else:
            print(vin, "not present want delete")
            #delete.append(vin)
            delete.append({
                "deleteDimension": {
                    "range": {
                        "dimension": "ROWS",
                        "startIndex": row_number - 1,
                        "endIndex": row_number
                    }
                }
            })
    if requests:
        applyBatch(requests, spreadsheet_id)
    #time.sleep(2)
    delete.sort(key=lambda x: x["deleteDimension"]["range"]["startIndex"], reverse=True)
    if delete:
        applyBatch(delete, spreadsheet_id)
    #print("bad vins are", delete)

def applyBatch(requests, spreadsheet_id):
    batch_update_body = {
        "requests": requests,
        "includeSpreadsheetInResponse": False,
        "responseRanges": [],
        "responseIncludeGridData": False
    }
    try:
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=batch_update_body).execute()
        print("batch operation apply ! ")
    except googleapiclient.errors.HttpError as e:
        print(f"An error occurred: {e}")


def format_datetime(date_str, time_str):
    time_str = str(time_str).split('.')[0]
    datetime_string = str(date_str) + time_str
    datetime_object = dTime.strptime(datetime_string, '%Y%m%d%H%M')
    formatted_datetime = datetime_object.strftime('%m/%d/%Y %I:%M %p')
    return formatted_datetime


def filter_and_convert_to_dict(vin_list, input_csv_file):
    df = pd.read_csv(input_csv_file)
    filtered_df = df[df['VIN'].isin(vin_list)]
    cars_list = []
    for _, row in filtered_df.iterrows():
        car = {
            'title': str(row['Year']) + " " + row['Make'] + " " + row['Model Detail'],  
            'stock_number': row['Lot number'], 
            'vin': row['VIN'],  
            'primary_damage': row['Damage Description'], 
            'odometer': row['Odometer'],  
            'engine': str(row['Engine']), 
            'source': "Copart",
            'yard': row['Yard name'],
            'sDate': row['Sale Date M/D/CY'],
            'sDay': row['Day of Week'],
            'sTime': row['Sale time (HHMM)'],
            'sTz': row['Time Zone']
        }
        cars_list.append(car)
    print("make cardict", len(cars_list))
    return cars_list

def sheetVinList(service, spreadsheet_id, sheet_name):
    range_to_read = f'{sheet_name}!B2:B'
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_to_read).execute()
    existing_vins = result.get('values', [])
    existing_vins = [item[0] for item in existing_vins if item]  # Flatten list
    return existing_vins

def updateSalesData(inputFile):
    input_csv_file = inputFile
    vin_list = sheetVinList(service, SPREADSHEET_ID, SHEET_NAME)
    vehicle_data_list = filter_and_convert_to_dict(vin_list, input_csv_file)
    find_and_update_row(service, vehicle_data_list, SPREADSHEET_ID, SHEET_NAME)

def updateLatest():
    updateFile = find_latest_file("./", "salesdata")
    updateSalesData(updateFile)

if __name__ == '__main__':
    #main()
    #sheetVinList(service, SPREADSHEET_ID, SHEET_NAME)
    #todo: auto update, auto delete if no longer in OR if sale date marked passed ? 
    #updateSalesData("./salesdata422.csv")
    updateLatest()
