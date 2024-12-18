import json
import os, sys
os.chdir(sys.path[0])
from carfax import find_latest_file
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import datetime
from datetime import datetime as dTime
import pytz
import shutil

SERVICE_ACCOUNT_FILE = 'gkey.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1zKOaioAQzaGsgEJtt_q27IsVTzQZnMS4cjlYr3T2RX4'
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

RANGE_NAME = 'A2' # Assuming we start appending from row 2

def format_datetime(date_str, time_str):
    time_str = str(time_str).split('.')[0]
    datetime_string = str(date_str) + time_str
    datetime_object = dTime.strptime(datetime_string, '%Y%m%d%H%M')
    formatted_datetime = datetime_object.strftime('%m/%d/%Y %I:%M %p')
    return formatted_datetime


def append_data_to_sheet(service, SPREADSHEET_ID, json_data):
    # Find the first free row
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])

    # If the sheet is not empty, find the first free row
    if values:
        free_row = len(values) + 2 # +2 to adjust for header row and zero-based index
    else:
        free_row = 2 # Start at row 2 if the sheet is empty

    utc_datetime = datetime.datetime.now(pytz.utc)
    est = pytz.timezone('America/New_York')
    est_datetime = utc_datetime.astimezone(est)
    formatted_datetime = est_datetime.strftime('%-I:%M %p %-m/%-d/%Y')

    # Prepare the data to append
    values_to_append = []
    for item in json_data:
        stock_number = item.get('stock_number', '')
        mode = None
        if item.get('source', '').lower() == 'iaai':
            url = f'https://www.iaai.com/Search?searchkeyword={stock_number}'
            mode = "iaai"
        elif item.get('source', '').lower() == 'copart':
            url = f'https://www.copart.com/lot/{stock_number}'
            mode = 'copart'
        else:
            url = ''
        hyperlink_formula = f'=HYPERLINK("{url}", "{stock_number}")'
        # 'yard': row['Yard name'],
        # 'sDate': row['Sale Date M/D/CY'],
        # 'sDay': row['Day of Week'],
        # 'sTime': row['Sale time (HHMM)'],
        # 'sTz': row['Time Zone'] 
        saleTime = format_datetime(item.get('sDate', '19700101'), item.get('sTime', '0000'))

        row_data = [
            item.get('title', ''),
            item.get('vin', ''),
            item.get('primary_damage', ''),
            item.get('reason', ''),
            item.get('ododate', ''),
            hyperlink_formula,
            item.get('yard', ''),
            saleTime,
            formatted_datetime,
            item.get('source', ''),
        ]
        values_to_append.append(row_data)


    # Append the data
    body = {
        'values': values_to_append
    }
    range_to_append = f'A{free_row}' # Update the range to append the data
    request = sheet.values().append(spreadsheetId=SPREADSHEET_ID, range=range_to_append,
                                    valueInputOption='USER_ENTERED', body=body)
    response = request.execute()

    print(f"Data appended at row: {free_row}")



def jsonProcessor(filename):
    try:
        with open(filename, 'r') as file:
            vehicles = json.load(file)        
        #print(vehicles[0]["vin"])
        return vehicles
    except FileNotFoundError:
        print("File not found. Please check the filename and try again.")
        return False
    except json.JSONDecodeError:
        print("Failed to decode JSON. Please check the file content.")
        return False

def dataProcessor(data):
    for vehicle in data:
        pass

def renamer(directory, original_prefix, new_prefix):
    files = [os.path.join(directory, file) for file in os.listdir(directory) if file.startswith(original_prefix)]
    files = [file for file in files if os.path.isfile(file)]
    if not files:
        print(f"No files starting with prefix '{original_prefix}' found in the directory.")
        return
    last_modified_file = max(files, key=os.path.getmtime)
    new_filename = os.path.join(directory, new_prefix + os.path.basename(last_modified_file)[len(original_prefix):])
    os.rename(last_modified_file, new_filename)
    print(f"Renamed '{os.path.basename(last_modified_file)}' to '{os.path.basename(new_filename)}'.")



def handler(bypass=False):
    if bypass:
        file = find_latest_file("./processed", "carArr")
    else:
        file = input("Input Json: ")
    data = jsonProcessor(file)
    if data == False:
        print("unable continue json bad")
        quit()
    else:
        #dataProcessor(data)
        append_data_to_sheet(service, SPREADSHEET_ID, data)
        renamer('./processed', 'carArr', 'f-carArr')
        print("finish main")
        return True
    
if __name__ == "__main__":
    handler(True)
    #print(format_datetime("20240422", "2100"))