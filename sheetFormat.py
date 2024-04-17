import json
import os, sys
os.chdir(sys.path[0])
from carfax import find_latest_file
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import datetime
import pytz

SERVICE_ACCOUNT_FILE = 'gkey.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1zKOaioAQzaGsgEJtt_q27IsVTzQZnMS4cjlYr3T2RX4'
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

RANGE_NAME = 'A2' # Assuming we start appending from row 2

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
        hyperlink_formula = f'=HYPERLINK("https://www.iaai.com/Search?searchkeyword={stock_number}", "{stock_number}")'
        
        row_data = [
            item.get('title', ''),
            item.get('vin', ''),
            item.get('primary_damage', ''),
            item.get('reason', ''),
            hyperlink_formula,
            formatted_datetime
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
        print("finish main")
        return True
    
if __name__ == "__main__":
    handler(True)