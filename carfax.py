import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import os, sys
os.chdir(sys.path[0])
import json
from pytz import timezone
import datetime

cEmail = None
cPass = None

#TODO: scan old db, branded title, salvage, etc keywords, year/mileage combo filter later thing

def getReading(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')    
    cellArr = soup.find_all('div', class_='history-overview-text-cell')    
    for cell in cellArr:
        if "Last reported odometer reading" in cell.text:
            strong = cell.find('strong')
            if strong:
                reading = strong.get_text(strip=True).replace(',', '')
                print("reading find : ", reading)
                readingInt = int(reading)
                return readingInt
    print("reading not fine")
    return None

def getReadingArr(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    odometer_readings = soup.find_all(class_=["record-odometer-reading", "narrow-record-odometer-reading"])
    odometer_values = []
    for reading in odometer_readings:
        value = reading.get_text(strip=True)
        try:
            value = int(value)
        except ValueError:
            pass
        odometer_values.append(value)
    #print("odometer dump::")
    #print(odometer_values)
    highest_mileage = max([int(mileage.strip('mi').replace(',', '')) for mileage in odometer_values if 'not reported' not in mileage], default=None)
    return highest_mileage

def checkBranded(html):
    #soup = BeautifulSoup(html, "html.parser")
    #count = html.count("total loss vehicle")
    if "branded title:" in html.lower() or "branded titles:" in html.lower():
        print("brand check fail")
        return True # branded
    #elif count > 1:
    elif "total loss reported:" in html.lower():
        print("total loss check fail")
        return None # total loss brand
    return False

def login(email, password):
    driver = uc.Chrome(headless=False, use_subprocess=False)
    url = "https://www.carfaxonline.com/reports"
    print("Trying login...")
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )

        driver.find_element(By.ID, "username").send_keys(email)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()

        location_div = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'location')]")))

        print("Login successful")
        return driver

    except Exception as e:
        print(f"An error occurred in login: {e}")
        return False

def getVinPage(driver, vin):
    driver.get("https://www.carfaxonline.com/vhr/{}".format(vin))
    try:
        vehicle_history_report = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "vehicle-history-report"))
        )
        return driver.page_source
    except Exception as e:
        print(f"An error occurred get vin page: {e}")
        return False

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

def checkDb():
    directory_path = './processed'
    if not os.path.exists(directory_path):
        print(f"Directory does not exist: {directory_path}")
    else:
        vin_array = []
        for filename in os.listdir(directory_path):
            if filename.endswith('.json'):
                file_path = os.path.join(directory_path, filename)
                with open(file_path, 'r') as file:
                    data = json.load(file)
                    for car in data:
                        if "vin" in car:
                            vin_array.append(car["vin"])
        print("excluding", len(vin_array), "vins")
        return vin_array


def append_to_file(path, data, is_first_entry):
    mode = 'a'  # Append mode
    with open(path, mode) as file:
        if is_first_entry:
            # If it's the first entry, check if we need to add a comma
            if os.path.getsize(path) > 0:
                file.write(',')
            file.write('[')
        else:
            file.write(',')
        json.dump(data, file)

def finalize_files(*paths):
    for path in paths:
        with open(path, 'a') as file:
            file.write(']')

def dataProcessor(driver, data):
    vinDb = checkDb()

    ogoodPath = outputName("carArr")
    obadPath = outputName("badCarArr")
    goodPath = "./processed/"+ogoodPath
    badPath = "./processed/"+obadPath
    is_first_good_entry = True
    is_first_bad_entry = True
    
    for vehicle in data:
        if vehicle["vin"] in vinDb:
            continue
        pageSrc = getVinPage(driver, vehicle["vin"])
        if pageSrc == False:
            vehicle["reason"] = "pageSrc false"
            append_to_file(badPath, vehicle, is_first_bad_entry)
            is_first_bad_entry = False
            print("excluded", vehicle["vin"], "pagesrc")
        else:
            odometerInt = getReadingArr(pageSrc)
            if odometerInt == None:
                vehicle["reason"] = "reading not fine"
                append_to_file(badPath, vehicle, is_first_bad_entry)
                is_first_bad_entry = False
                print("excluded", vehicle["vin"], "not find reading")
            elif odometerInt > 132000: # MILE EXCLUSION INT
                vehicle["reason"] = "mile exclusion"
                append_to_file(badPath, vehicle, is_first_bad_entry)
                is_first_bad_entry = False
                print("excluded", vehicle["vin"], "mile exclusion")
            else:
                resultCheck = checkBranded(pageSrc)
                if resultCheck == True:
                    vehicle["reason"] = "branded"
                    append_to_file(badPath, vehicle, is_first_bad_entry)
                    is_first_bad_entry = False
                    print("excluded", vehicle["vin"], "brand exclusion")
                elif resultCheck == None:
                    vehicle["reason"] = "total loss"
                    append_to_file(badPath, vehicle, is_first_bad_entry)
                    is_first_bad_entry = False
                    print("excluded", vehicle["vin"], "total loss exclusion")
                else:
                    vehicle["reason"] = odometerInt
                    append_to_file(goodPath, vehicle, is_first_good_entry)
                    is_first_good_entry = False
                    print("included", vehicle["vin"], "good car")
        time.sleep(2)

    if is_first_bad_entry == False:
        finalize_files(badPath)
    if is_first_good_entry == False:
        finalize_files(goodPath)
    print("finish dataProcessor")



def outputName(strput):
    if not os.path.exists("./processed"):
        os.makedirs("./processed")
    et_zone = timezone('US/Eastern')
    et_time = datetime.datetime.now(et_zone)
    file_name = et_time.strftime("{}%Y%m%d-%I%M%p".format(strput))
    file_name += ".json"
    return file_name
    
def find_latest_file(directory, file_prefix):
    latest_time = None
    latest_file_name = None
    for file_name in os.listdir(directory):
        if file_name.startswith(file_prefix):
            full_path = os.path.join(directory, file_name)
            file_time = os.path.getmtime(full_path)
            if latest_time is None or file_time > latest_time:
                latest_time = file_time
                latest_file_name = file_name
    if latest_file_name != None:
        return "{}/".format(directory)+latest_file_name
    else:
        print("no file for use")
        quit()


def handler(bypass=False):
    initVars("./credentials.json")
    driver = login(cEmail, cPass)
    dataCollector = []
    if driver == False:
        print("unable to continue : driver false")
        quit()
    else:
        print("driver loaded!")
        if bypass:
            fileName = find_latest_file("./raw", "output")
            file = fileName
        else:
            file = input("Input Json: ")
        data = jsonProcessor(file)
        if data == False:
            print("unable continue json bad")
            quit()
        else:
            dataProcessor(driver, data)
            print("finish main")
            return True

def testOneVin(vin):
    initVars("./credentials.json")
    driver = login(cEmail, cPass)
    if driver == False:
        print("unable to continue : driver false")
        quit()
    else:
        pageSrc = getVinPage(driver, vin)
        if pageSrc == False:
            print("pagesrc bad")
        else:
            odometerInt = getReading(pageSrc)
            readingarr = getReadingArr(pageSrc)
            resultCheck = checkBranded(pageSrc)
            print("vin: {} odometer: {} odometer2: {} result: {}".format(vin, odometerInt, readingarr, resultCheck))
        

def initVars(path):
    global cEmail, cPass
    with open(path, 'r') as file:
        data = json.load(file)
    cEmail = data.get('cEmail')
    cPass = data.get('cPass')

if __name__ == "__main__":
    #fileName = find_latest_file("./raw", "output")
    #print(fileName)
    handler()
    #testOneVin("2GCEK19T541183036")
    #checkDb()
    #file = input("Input Json: ")
    #data = jsonProcessor(file)
    #testParser()