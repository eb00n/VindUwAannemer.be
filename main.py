from bs4 import BeautifulSoup
import requests
import urllib.request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class AllContractors:
    def __init__(self):
        self.list = []
        return

class Category:
    def __init__(self, name, url, cont_list=[]):
        self.name = name
        self.url = url
        self.cont_list = cont_list

    def __str__(self):
        return f"{self.name} - {self.url} - {len(self.cont_list)}"



class Contact:
    def __init__(self, url, cat=None, adres=None, postcode=None, woonplaats=None, tel=None, email=None, btw=None, www=None):
        self.url = url
        self.cat = cat
        self.adres = adres
        self.postcode = postcode
        self.woonplaats = woonplaats
        self.tel = tel
        self.email = email
        self.btw = btw
        self.www = www
        return

    def __str__(self):
        return f"{self.cat}, {self.adres}, {self.postcode}, {self.woonplaats}," \
               f" {self.tel}, {self.email}, {self.btw}, {self.www}"



def get_all_category_urls():
    base_url = 'https://www.vinduwaannemer.be/'

    # Find and loop through sub-categories (acts)
    cat_list = []
    response = requests.get(base_url)
    if not response.ok:
        print(f"Code: {response.status_code}, url: {base_url}")
        return
    soup = BeautifulSoup(response.text, 'html.parser')
    results = soup.find_all('p', class_='acts')
    for cat in results:
        acts = cat.find_all('a')
        for act in acts:
            c = Category(act.get_text(strip=True), act.get('href'))
            # print(c)
            cat_list.append(c)

    return cat_list


cookies_accepted = False
def get_contact_urls(driver, act_url):
    global cookies_accepted
    # get web page
    driver.get(act_url)
    # driver.implicitly_wait(1)

    # Accept the cookie dialogue automatically
    if not cookies_accepted:
        driver.find_element(By.ID, 'c_statistic').click()
        driver.find_element(By.ID, 'c_social').click()
        driver.find_elements(By.XPATH, "//a[@class='c_btnsave c_close']")[0].click()
        cookies_accepted = True

    # execute script to scroll down the page
    for i in range(10):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # driver.execute_script("var scrollingElement = (document.scrollingElement || document.body); "
        #                       "scrollingElement.scrollTop = scrollingElement.scrollHeight;"
        #                      )
        time.sleep(0.5)     # wait till page has loaded the extra items

    # Get all a-tag elements within h2 tags
    items = driver.find_elements(By.CSS_SELECTOR, "h2 a")
    contact_list = [Contact(url=item.get_attribute('href')) for item in items]
    return contact_list


def main():
    base_url = 'https://www.vinduwaannemer.be/'
    allcontractors = AllContractors()

    cat_list = get_all_category_urls()

    # Because of content filled by JavaScript we continue using Selenium
    # driver = webdriver.Firefox(executable_path='C:\\Users\\Ed\\PycharmProjects\\WebScraping - Aannemer.be\\geckodriver.exe')
    driver = webdriver.Firefox()  # geckodriver.exe is in same map as this python script
    i = 0
    # contact_urls = []
    # loop trough all categories and get all contacts per category
    for cat in cat_list:
        print(cat)
        cont_list = get_contact_urls(driver, base_url + cat.url)
        # Store category name together with list of contact_urls
        cat.cont_list = cont_list
        print(len(cat.cont_list))

        # When under development do only the first few to speed up things.
        i += 1
        if i == 4:
            break
    print(cat)
    # Make a list of unique contacts and fetch the detail info per contact





    #driver.quit()



""""
Collect all subcategories and the contractors within from vinduwaannemer.be
"""
if __name__ == '__main__':
    main()
