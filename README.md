# goldensalvage
Tool which identifies hidden gems in vehicle auctions based on misreported mileage

This tool parses vehicle auctions for vehicles matching a specific filter defined by the user. Afterwards, the VINs of the vehicles are funneled through CarFax in order to determine whether the car may potentially be worth acquiring. The vehicle's last known mileage is not available on the auction site because the tool filters to only vehicles which have a malfunctioning odometer. Thus, most users on the website may lowball or skip over these cars, as time is needed to manually verify the mileage of these vehicles. However, by scraping CarFax, we can automate this process. In the end, the tool will also upload the results to a sheet on Google Sheets automatically, so that a human may review only the potentially valid vehicles. 

Some alternate configurations exist in the files to look for other filters, but the initial concept was for misreported mileage. 

iaai.py is used to search the IAAI auction while copart2.py parses the salesdata file from copart. Carfax.py handles the scraping, it requires a dealership login with unlimited lookups to function. Sheetfix and sheetformat are tools used for updating old rows and adding new rows into a google sheets spreadsheet with the necessary data. Use handler.py to run the script as one suite.  
