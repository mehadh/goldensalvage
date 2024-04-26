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

#TODO: what if captcha, what if that weird exception happen in start
# login and mohamed to vars
# fix that weird exceptino sinc emore common now
# categorize by location
# filter out virginia or smth idk

mEmail = None
mPass = None
mName = None

def initVars(path):
    global mEmail, mPass, mName
    with open(path, 'r') as file:
        data = json.load(file)
    mEmail = data.get('mEmail')
    mPass = data.get('mPass')
    mName = data.get('mName')


def login(email, password):
    driver = uc.Chrome(headless=False, use_subprocess=False)
    url = "https://login.iaai.com/"
    print("Trying login...")
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "Email"))
        )

        driver.find_element(By.ID, "Email").send_keys(email)
        driver.find_element(By.ID, "Password").send_keys(password)
        #print("put stuff in")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        #print("click login")
        #WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '"+mName+"')]")))

        print("Login successful")
        if accept_cookies(driver):
            return driver

    except Exception as e:
        print(f"An error occurred to login: {e}")
        return False
    #finally:
    #    time.sleep(5)
    #    driver.quit()

def accept_cookies(driver):
    try:
        cookie_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler"))
        )
        cookie_button.click()
        print("consent given")
        return True
    except NoSuchElementException:
        # If the button does not exist, it's fine; just log it and move on
        print("no cookie banner for click")
        return True
    except Exception as e:
        print(f"An error occurred to accept cookie: {e}")
        return False


def applyFilter(driver):
    try:
        print("Navigating to search page...")
        driver.get("https://www.iaai.com/Search")
        dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "SaveSearchDropdown"))
        )
        dropdown.click()
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "SavedSearchListItems"))
        )
        # automobiles, 0-1 mi, items with a sale date, northeast, clear
        odometer_item = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Odometer')]"))
        )
        odometer_item.click()
        print("Filter applied")
        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def clickNext(driver):
    nextBtn = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "button.btn-next"))
    )
    if not nextBtn.get_attribute("disabled"):
        nextBtn.click()
        print("Next clicked!")
        time.sleep(1)
        return True
    else:
        print("Next disabled..end reach")
        return False

def extract_car_info(html):
    soup = BeautifulSoup(html, 'html.parser')
    cars = []

    car_rows = soup.find_all('div', class_='table-row-inner')
    for car_row in car_rows:
        car = {
            'title': None,
            'stock_number': None,
            'vin': None,
            'primary_damage': None,
            'odometer': None,
            'engine': None,
            'source': "IAAI",
            #'current_bid': None
        }
        
        title = car_row.find('h4', class_='heading-7')
        if title and title.a:
            car['title'] = title.a.get_text(strip=True)

        stock_number = car_row.find('span', title=lambda x: x and x.startswith('Stock #:'))
        if stock_number:
            car['stock_number'] = stock_number.get_text(strip=True)

        vin = car_row.find('span', title=lambda x: x and x.startswith('VIN :'))
        if vin:
            car['vin'] = vin.get_text(strip=True)

        primary_damage = car_row.find('span', title=lambda x: x and x.startswith('Primary Damage:'))
        if primary_damage:
            car['primary_damage'] = primary_damage.get_text(strip=True)

        odometer = car_row.find('span', title=lambda x: x and x.startswith('Odometer:'))
        if odometer:
            car['odometer'] = odometer.get_text(strip=True)

        engine = car_row.find('span', title=lambda x: x and x.startswith('Engine:'))
        if engine:
            car['engine'] = engine.get_text(strip=True)

        cars.append(car)
    
    return cars


def dataHandler(driver):
    try:
        data = extract_car_info(driver.page_source)
        filterData = [d for d in data if d.get('vin') is not None]
        return filterData
    except Exception as e:
        print("exception datahandler", e)
        return False
    
def outputName():
    if not os.path.exists("./raw"):
        os.makedirs("./raw")
    et_zone = timezone('US/Eastern')
    et_time = datetime.datetime.now(et_zone)
    file_name = et_time.strftime("output%Y%m%d-%I%M%p")
    file_name += ".json"
    return file_name



def handler():
    initVars("./credentials.json")
    driver = login(mEmail, mPass)
    dataCollector = []
    if driver == False:
        print("unable to continue : driver false")
        quit()
    else:
        filterRes = applyFilter(driver)
    if filterRes == False:
        print("unable to continue : filter result false")
        quit()
    else:
        time.sleep(2)
        #clickNext(driver)
        filterData = dataHandler(driver)
        if filterData == False:
            print("unable continue first filterdata bad")
            quit()
        dataCollector += filterData
        print("collect", len(filterData), "from first datahandle")
        while clickNext(driver) == True:
            filterData = dataHandler(driver)
            if filterData == False:
                print("unable continue filterdata loop bad")
                quit()
            dataCollector += filterData
            print("collect", len(filterData), "from filter loop")
    print("finish with data collected")
    nameFile = outputName()
    with open("./raw/"+nameFile, 'w') as file:
        json.dump(dataCollector, file, indent=4)
    print("result save to "+nameFile)
    return True


def testParser():
    file_path = './sample.html'
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    cars_info = extract_car_info(html_content)
    print(cars_info)




if __name__ == "__main__":
    #initVars("./credentials.json")
    handler()
    #testParser()

