import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def _add_to_your_selections(driver):
    driver.find_element_by_partial_link_text('ADD TO YOUR SELECTIONS').click()
    time.sleep(3)


def _download_zip(driver):
    driver.find_element_by_id('dnld_btn_below').click()
    time.sleep(1)
    for btn in driver.find_element_by_id('message-dialog').find_elements_by_css_selector('button'):
        if btn.text == 'OK':
            btn.click()

    time.sleep(10)
    for btn in driver.find_element_by_id('downloadprogress').find_elements_by_css_selector('button'):
        if btn.text == 'DOWNLOAD':
            btn.click()

    time.sleep(5)


def _fetch_once_clickable(driver, id):
    return WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, id)))


def _make_select_selection(driver, select_element_id, selection, needs_initial_click=True):
    select_element = _fetch_once_clickable(driver, select_element_id)
    if needs_initial_click:
        select_element.click()

    options = select_element.find_elements_by_css_selector('option')
    for option in options:
        if selection in option.text:
            option.click()
            return


def _search_for_topic(driver, topic_id):
    topic_input = driver.find_element_by_id('searchTopicInput')
    topic_input.send_keys(topic_id)
    driver.find_element_by_id('refinesearchsubmit').click()
    time.sleep(2)


def _select_5_year_summary(driver, topic_id):
    driver.find_element_by_id('ACS_17_5YR_{}'.format(topic_id)).click()
    time.sleep(1)
    # rows = driver.find_elements_by_css_selector('#resulttable > table > tbody > tr')
    # for row in rows:
    #     cells = row.find_elements_by_css_selector('td')
    #     if '2017 ACS 5-year estimates' in cells[3].text:
    #         cells[0].find_element_by_css_selector('input').click()


def _toggle_geographies_panel(driver):
    driver.execute_script('requestGeoOverlayToggle();')
    time.sleep(2)


class ElementIds:
    GEOGRAPHIES_TOGGLE_BUTTON = 'geo-overlay-btn'


class CensusScraper():
    def __init__(self):
        self.driver = webdriver.Chrome()

    def cleanup(self):
        self.driver.quit()

    def get_census_data(self):
        self.driver.get('https://factfinder.census.gov/faces/nav/jsf/pages/searchresults.xhtml')
        self._wait_initial_load()

        pass

    def _wait_initial_load(self):
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, ElementIds.GEOGRAPHIES_TOGGLE_BUTTON)))

def main():
    scraper = CensusScraper()
    try:
        scraper.get_census_data()
    finally:
        scraper.cleanup()

    driver = webdriver.Chrome()
    driver.get('https://factfinder.census.gov/faces/nav/jsf/pages/searchresults.xhtml')

    _toggle_geographies_panel(driver)

    _make_select_selection(driver, 'summaryLevel', 'Place - 160')
    time.sleep(1)

    _make_select_selection(driver, 'state', 'Massachusetts')

    time.sleep(2)
    _make_select_selection(driver, 'geoAssistList', 'Chelsea', needs_initial_click=False)
    _add_to_your_selections(driver)

    _make_select_selection(driver, 'geoAssistList', 'Boston', needs_initial_click=False)
    _add_to_your_selections(driver)

    _toggle_geographies_panel(driver)

    _search_for_topic(driver, 'S0101')
    _select_5_year_summary(driver, 'S0101')

    _download_zip(driver)

    print('Downloaded successfully')


if __name__ == '__main__':
    main()
