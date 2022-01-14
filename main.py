from bs4 import BeautifulSoup
import requests
import urllib.request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
DEBUG = False


class Category:
    def __init__(self, name, url, cont_list=[]):
        self.name = name
        self.url = url
        self.cont_list = cont_list

    def __str__(self):
        return f"{self.name} - {self.url} - {len(self.cont_list)}"


class Contact:
    def __init__(self, url, cat=None, naam=None, adres=None,
                 tel=None, mob=None, email=None, btw=None, www=None):
        self.url = url
        self.cat = cat
        self.naam = naam
        self.adres = adres
        self.tel = tel
        self.mob = mob
        self.email = email
        self.btw = btw
        self.www = www
        return

    def __str__(self):
        return f"{self.cat}\t{self.naam}\t{self.adres}\t{self.tel}\t{self.mob}\t{self.email}\t{self.btw}\t{self.www}"


def get_all_category_urls(base_url):
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
def accept_cookies(driver):
    global cookies_accepted

    # Accept the cookie dialogue automatically (only once needed)
    if not cookies_accepted:
        driver.find_element(By.ID, 'c_statistic').click()
        driver.find_element(By.ID, 'c_social').click()
        driver.find_elements(By.XPATH, "//a[@class='c_btnsave c_close']")[0].click()
        cookies_accepted = True


def get_contact_urls(driver, act_url, cat):
    # get web page
    driver.get(act_url)
    time.sleep(0.1)         # give it some time to load, otherwise there is nothing to find

    accept_cookies(driver)

    total_items = (driver.find_element(By.CSS_SELECTOR, "div h1").text.split(' ')[0])
    total_items = int(total_items) if total_items.isnumeric() else 0

    # execute script to scroll down the page until all items are loaded
    items_on_first_page = 0
    while items_on_first_page == 0 and total_items > 0:
        items_on_first_page = len(driver.find_elements(By.CSS_SELECTOR, "h2 a"))
        time.sleep(0.1)     # wait a bit longer to let the page render.

    if total_items > 1:
        for i in range(total_items//items_on_first_page):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.1)     # wait till page has loaded the extra items

        # Get all a-tag elements within h2 tags
        items = driver.find_elements(By.CSS_SELECTOR, "h2 a")
        contact_list = [Contact(url=item.get_attribute('href'), cat=cat.name) for item in items]
    else:
        # When only 1 contact the contact page itself is presented instead of a list of contacts
        if total_items == 1:
            contact_list = [Contact(url=driver.current_url, cat=cat.name)]
        else:
            pass        # no contacts in this category

    return contact_list


def get_all_cont_urls(driver, base_url, cat_list):
    if DEBUG:
        i = 0

    contacts = []
    # loop trough all categories and get all contacts per category
    for cat in cat_list:
        print(cat)
        # collect contact urls for the current category
        cont_list = get_contact_urls(driver, base_url + cat.url, cat)

        # Store category name together with list of contact_urls
        contacts.extend(cont_list)  # add contacts to the main contacts list
        # cat.cont_list = cont_list      # add contact list to the category
        print(len(contacts))

        # When under development do only the first few to speed up things.
        if DEBUG:
            i += 1
            if i == 4:
                break
    print(len(contacts), len(set(contacts)))

    return contacts


def find_contact_details_in_soup(soup, class_string):
    try:
        detail = soup.find('i', class_=class_string).parent.text
    except:
        detail = ''
    return detail


def get_all_contact_info(contacts, base_url):

    for contact in contacts:
        response = requests.get(contact.url)
        if not response.ok:
            print(f"Code: {response.status_code}, url: {contact.url}")
            return contacts, False
        soup = BeautifulSoup(response.text, 'html.parser')
        if soup == None:
            print(f'Empty soup: {contact}')
            continue

        # Find the name of the Contact
        try:
            contact.naam = soup.find('div', id='ficheWrap').find('h1').text
        except:
            print(f'Contact has no adres: {contact}')
            contact.adres = ''
        contact.adres = find_contact_details_in_soup(soup, 'fas fa-map-marker-alt fa-fw')
        contact.mob = find_contact_details_in_soup(soup, 'fas fa-mobile-alt fa-fw')
        contact.tel = find_contact_details_in_soup(soup, 'fas fas fa-phone fa-fw fa-fw')
        contact.email = find_contact_details_in_soup(soup, 'fas fa-envelope fa-fw')
        contact.btw = find_contact_details_in_soup(soup, 'fas fa-file-invoice-dollar fa-fw')
        contact.www = find_contact_details_in_soup(soup, 'fas fa-globe-americas fa-fw')

    return contacts, True


def write_contacts(file_name, contacts):
    with open(file_name, 'w') as f:
        for contact in contacts:
            f.write(str(contact))
            f.write('\n')
    return


def main():
    base_url = 'https://www.vinduwaannemer.be/'
    file_name = 'vinduwaannemer.be.tsv'

    cat_list = get_all_category_urls(base_url)

    # Because of content filled by JavaScript we continue using Selenium
    driver = webdriver.Firefox()    # geckodriver.exe is in same map as this python script

    contacts = get_all_cont_urls(driver, base_url, cat_list)

    #### Make a list of unique contacts and fetch the detail info per contact
    ####
    contacts, status = get_all_contact_info(contacts, base_url)
    print(len(contacts))

    write_contacts(file_name, contacts)

    driver.quit()



""""
Collect all subcategories and the contractors within from vinduwaannemer.be
"""
if __name__ == '__main__':
    main()
