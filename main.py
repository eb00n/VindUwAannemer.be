from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
DEBUG = False


class Category:
    def __init__(self, url, naam):
        self.url = url
        self.naam = naam

    def __str__(self):
        return f"{self.naam}"


class Contact:
    def __init__(self, url, naam=None, adres=None, tel=None, mob=None, email=None, btw=None, www=None):
        self.url = url
        self.naam = naam
        self.adres = adres
        self.tel = tel
        self.mob = mob
        self.email = email
        self.btw = btw
        self.www = www
        return

    # To enable using .index() on the list of contacts
    def __eq__(self, cont):
        if not isinstance(cont.url, str):
            raise TypeError("Contact URL can be compared only with str")
        if self.url == cont.url:
            return True
        return False

    def __str__(self):
        return f"{self.naam}\t{self.adres}\t{self.tel}\t{self.mob}\t{self.email}\t{self.btw}\t{self.www}"


# Many-to-many class
class CatCont:
    def __init__(self, cat, cont):
        self.cat = cat
        self.cont = cont

    def __str__(self):
        return f"{self.cat}\t{self.cont}"


def get_all_category_urls(base_url):
    """
    Collect all sub categories: the name and the url pointing to the sub category page with the contacts
    :param base_url:
    :return: a list of Category objects
    """
    # Find and loop through sub-categories (acts)
    cat_list = []
    response = requests.get(base_url)
    if not response.ok:
        print(f"Code: {response.status_code}, url: {base_url}")
        return cat_list
    soup = BeautifulSoup(response.text, 'html.parser')
    results = soup.find_all('p', class_='acts')
    for cat in results:
        acts = cat.find_all('a')
        for act in acts:
            c = Category(url=act.get('href'), naam=act.get_text(strip=True))
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
        contact_list = [Contact(url=item.get_attribute('href')) for item in items]
    else:
        # When only 1 contact the contact page itself is presented instead of a list of contacts
        if total_items == 1:
            contact_list = [Contact(url=driver.current_url)]
        else:
            contact_list = []        # no contacts in this category

    return contact_list




def add_cat_contacts(contacts, catcont, cat, cont_list):
    """
    Add sub-list of contacts into contacts, making sure they are unique. And add the many-to-many
    relations for the current category and the contacts in the sub-list.
    :param contacts: list of Contact objects
    :param catcont: list of CatCont objects
    :param cat: current category for which the contacts are added to the cat-contact relation
    :param cont_list: sub-list of contacts to be merged into contacts
    """
    for cont in cont_list:
        # Add cont to contacts if not exists and return index
        try:
            i = contacts.index(cont)
        except ValueError:
            contacts.append(cont)
            i = len(contacts) - 1

        catcont.append(CatCont(cat, contacts[i]))


def get_all_cont_urls(driver, base_url, cat_list):
    """
    Collect the urls to the contact details. Per category the contact urls are collected.
    A list of unique contacts is build tohether with the many-to-many list that records
    the category - contact relation.
    :param driver:
    :param base_url:
    :param cat_list:
    :return: a list of unique contacts and a list of category-contacts relations
    """
    if DEBUG:
        i = 0

    contacts = []
    catcont = []
    # loop trough all categories and get all contacts per category
    for cat in cat_list:
        print(cat)
        # collect contact urls for the current category
        cont_list = get_contact_urls(driver, base_url + cat.url, cat)

        # Merge contacts and add category-contact relations
        add_cat_contacts(contacts, catcont, cat, cont_list)

        print(f"#contacts: {len(contacts)}, #catcont: {len(catcont)}, #cont_list: {len(cont_list)}")

        # When under development do only the first few to speed up things.
        if DEBUG:
            i += 1
            if i == 4:
                break

    return contacts, catcont


def find_contact_details_in_soup(soup, class_string):
    try:
        detail = soup.find('i', class_=class_string).parent.text
    except:
        detail = ''
    return detail


def get_all_contact_info(contacts, base_url):
    counter, total_count = 0, len(contacts)
    for contact in contacts:
        if counter % 10 == 0:
            print(f"Retrieving contact details: {counter}/{total_count}...")

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
            print(f'Contact has no Name: {contact}')
            contact.naam = ''
        contact.adres = find_contact_details_in_soup(soup, 'fas fa-map-marker-alt fa-fw')
        contact.mob = find_contact_details_in_soup(soup, 'fas fa-mobile-alt fa-fw')
        contact.tel = find_contact_details_in_soup(soup, 'fas fa-phone fa-fw')
        contact.email = find_contact_details_in_soup(soup, 'fas fa-envelope fa-fw')
        contact.btw = find_contact_details_in_soup(soup, 'fas fa-file-invoice-dollar fa-fw')
        contact.www = find_contact_details_in_soup(soup, 'fas fa-globe-americas fa-fw')
        counter += 1
    return contacts, True


def write_contacts(file_name, catcont):
    """
    Write detailed many-to-many relations to Tab seperated file
    :param file_name: Output file
    :param catcont: many-to-many list
    :return: output file
    """
    print(f"Writing file: {file_name}")
    with open(file_name, 'w') as f:
        for cc in catcont:
            f.write(f"{cc.cat.naam}\t{str(cc.cont)}")
            f.write('\n')
    return


def main():
    """"
    Collect all subcategories and the contractors within from vinduwaannemer.be
    """
    base_url = 'https://www.vinduwaannemer.be/'
    file_name = 'vinduwaannemer.be.tsv'

    cat_list = get_all_category_urls(base_url)

    # Because of content filled by JavaScript Selenium is used
    driver = webdriver.Firefox()    # geckodriver.exe is in same map as this python script
    contacts, catcont = get_all_cont_urls(driver, base_url, cat_list)

    contacts, status = get_all_contact_info(contacts, base_url)
    print(len(contacts))

    write_contacts(file_name, catcont)

    driver.quit()


if __name__ == '__main__':
    main()
