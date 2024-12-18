#"Id","Yard number","Yard name","Sale Date M/D/CY","Day of Week","Sale time (HHMM)","Time Zone","Item#","Lot number","Vehicle Type","Year","Make","Model Group","Model Detail","Body Style","Color","Damage Description","Secondary Damage","Sale Title State","Sale Title Type","Has Keys-Yes or No","Lot Cond. Code","VIN","Odometer","Odometer Brand","Est. Retail Value","Repair cost","Engine","Drive","Transmission","Fuel Type","Cylinders","Runs/Drives","Sale Status","High Bid =non-vix,Sealed=Vix","Special Note","Location city","Location state","Location ZIP","Location country","Currency Code","Image Thumbnail","Create Date/Time","Grid/Row","Make-an-Offer Eligible","Buy-It-Now Price","Image URL","Trim","Last Updated Time","Rentals","Copart Select","Seller Name","Offsite Address1","Offsite State","Offsite City","Offsite Zip"
#- add more vehicle types, rn just V
#- expand on title definitions ? 
import pandas as pd
import os, sys
os.chdir(sys.path[0])
from iaai import outputName
import json
from carfax import find_latest_file


def parseCsv(file_path, c300Check=False):
    data = pd.read_csv(file_path)
    acceptableTitles = ["ct"]
    acceptableStates = ["ma", "nh", "ri", "ct", "vt", "me", "ny", "nj", "pa", "de", "md", "va", "dc", "wv", "oh", "nc"] # based on distance
    filtered_data = data[data['Sale Date M/D/CY'] != 0]
    filtered_data = filtered_data[filtered_data['Vehicle Type'] == 'V']
    filtered_data = filtered_data[filtered_data['Sale Title Type'].str.lower().isin(acceptableTitles)]
    
    if c300Check:
        filtered_data = filtered_data[filtered_data['Model Group'] == 'C-CLASS']
        filtered_data = filtered_data[(filtered_data['Year'] >= 2008) & (filtered_data['Year'] <= 2014)]
        filtered_data = filtered_data[filtered_data['Location state'].str.lower().isin(["ma", "nh", "ri", "ct", "vt", "me"])]
    else:
        filtered_data = filtered_data[(filtered_data['Odometer'] >= 0.0) & (filtered_data['Odometer'] <= 11.0)]
        filtered_data = filtered_data[filtered_data['Location state'].str.lower().isin(acceptableStates)] # this was bad mistake!!!!
    #filtered_data.to_csv('filtered_output.csv', index=False)  
    print("returning cars amount", len(filtered_data))
    return filtered_data

def toDict(filtered_data):
    cars_list = []
    for _, row in filtered_data.iterrows():
        car = {
            'title': str(row['Year']) +" "+ row['Make'] +" "+ row['Model Detail'],  
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
    return cars_list


def handler(c300Check=False):
    #filepath = input("Point to csv: ")
    filepath = find_latest_file("./", "salesdata")
    filterData = parseCsv(filepath, c300Check)
    dictGrab = toDict(filterData)
    nameFile = outputName()
    with open("./raw/"+nameFile, 'w') as file:
        json.dump(dictGrab, file, indent=4)
    print("result save to "+nameFile)
    return True


if __name__ == "__main__":
    handler()