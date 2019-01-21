import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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



PLACES = [
    'Boston',
    'Chelsea',
]

TOPIC_IDS = [
    'S0101',
    'S1002',
    'S1602',
]


class ElementIds:
    GEOGRAPHIES_PANEL_CONTENT = 'geotabs'
    GEOGRAPHIES_TOGGLE_BUTTON = 'geo-overlay-btn'
    PLACES_SELECT = 'geoAssistList'
    SELECTION_ADDING_LOAD_MASK = 'geoAssist_wait_mask'
    TOPIC_LOADING_MASK = 'topics_wait_mask'


class CensusScraper():
    def __init__(self):
        self.driver = webdriver.Chrome()

    def cleanup(self):
        self.driver.quit()

    def get_census_data(self):
        self.driver.get('https://factfinder.census.gov/faces/nav/jsf/pages/searchresults.xhtml')
        self._wait_for_loading_mask()

        self._select_places(PLACES)
        self._select_topics(TOPIC_IDS)
        pass

    def _add_place_to_selections(self, place):
        self._make_select_selection(ElementIds.PLACES_SELECT, place, needs_initial_click=False)
        self.driver.find_element_by_partial_link_text('ADD TO YOUR SELECTIONS').click()

        try:
            WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.ID, ElementIds.SELECTION_ADDING_LOAD_MASK)))
        except TimeoutException:
            pass
        WebDriverWait(self.driver, 3).until_not(EC.presence_of_element_located((By.ID, ElementIds.SELECTION_ADDING_LOAD_MASK)))

    def _close_geographies_panel(self):
        self.driver.execute_script('requestGeoOverlayToggle();')
        WebDriverWait(self.driver, 10).until_not(EC.visibility_of_element_located((By.ID, ElementIds.GEOGRAPHIES_PANEL_CONTENT)))

    def _make_select_selection(self, select_element_id, selection, needs_initial_click=True):
        select_element = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, select_element_id)))
        if needs_initial_click:
            select_element.click()

        options = select_element.find_elements_by_css_selector('option')
        for option in options:
            if selection in option.get_attribute('value'):
                option.click()
                time.sleep(1)
                return

    def _open_geographies_panel(self):
        self.driver.find_element_by_id(ElementIds.GEOGRAPHIES_TOGGLE_BUTTON).click()
        WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.ID, ElementIds.GEOGRAPHIES_PANEL_CONTENT)))

    def _select_places(self, places):
        self._open_geographies_panel()
        self._make_select_selection('summaryLevel', '160')
        self._make_select_selection('state', 'Massachusetts')
        for place in places:
            self._add_place_to_selections(place)
        self._close_geographies_panel()

    def _select_topics(self, topic_ids):
        unchecked_checkbox_ids = {'ACS_17_5YR_{}'.format(topic_id) for topic_id in topic_ids}
        checked_checkbox_ids = set()

        self._make_select_selection('yearFilter', '2017')
        self._wait_for_loading_mask()

        while len(unchecked_checkbox_ids) > 0:
            for id in unchecked_checkbox_ids.copy():
                try:
                    self.driver.find_element_by_id(id).click()
                    unchecked_checkbox_ids.remove(id)
                    checked_checkbox_ids.add(id)
                except NoSuchElementException:
                    pass
            next_page_button = self.driver.find_element_by_class_name('yui-pg-next')
            if next_page_button.is_enabled():
                next_page_button.click()
            else:
                print('Could not find entries for {}'.format(', '.join(unchecked_checkbox_ids)))
                break
            self._wait_for_loading_mask()

        pass

    def _wait_for_loading_mask(self):
        try:
            WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.ID, ElementIds.TOPIC_LOADING_MASK)))
        except TimeoutException:
            pass
        WebDriverWait(self.driver, 10).until_not(EC.presence_of_element_located((By.ID, ElementIds.TOPIC_LOADING_MASK)))


def main():
    scraper = CensusScraper()
    try:
        scraper.get_census_data()
    finally:
        scraper.cleanup()

    _search_for_topic(driver, 'S0101')
    _select_5_year_summary(driver, 'S0101')

    _download_zip(driver)

    print('Downloaded successfully')


if __name__ == '__main__':
    main()
