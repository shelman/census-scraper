import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


PLACES = [
    'Essex',
    'Ipswich',
    'Topsfield',
]

TOPIC_IDS = [
    'B01001',  # Sex by Age
    'B01003',  # Total Population
    'B02001',  # Race
    'B03002',  # Hispanic or Latino
    'B09002',  # Own Children Under 18 Years By Family Type And Age
    'B11003',  # Family Type By Presence And Age Of Own Children Under 18 Years
    'B11016',  # Household Type By Household Size
    'B14001',  # School Enrollment By Level Of School For The Population 3 Years And Over
    'B15002',  # Educational Attainment For The Population 25 Years And Over
    'B19001',  # Household Income in the Past 12 Months
    'B19013',  # Median Household Income In The Past 12 Months
    'B19202',  # Median Nonfamily Household Income In The Past 12 Months
    'B25001',  # Housing Units
    'B25003',  # Tenure
    'B25007',  # Tenure By Age Of Householder
    'B25010',  # Average Household Size Of Occupied Housing Units By Tenure
    'B25024',  # Units In Structure
    'B25034',  # Year Structure Built
    'B25064',  # Median Gross Rent (Dollars)
    'B25077',  # Median Value (Dollars)
    'B26001',  # Group Quarters Population
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
        self._download_zip_file()

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

    def _download_zip_file(self):
        self.driver.find_element_by_id('dnld_btn_below').click()
        WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#message-dialog button')))
        for btn in self.driver.find_element_by_id('message-dialog').find_elements_by_css_selector('button'):
            if btn.text == 'OK':
                btn.click()

        start = time.time()
        while True:
            if time.time() - start > 60:
                print('Waited 60 seconds to download - cancelling')
                return
            for btn in self.driver.find_element_by_id('downloadprogress').find_elements_by_css_selector('button'):
                if btn.text == 'DOWNLOAD' and btn.is_enabled():
                    btn.click()
                    time.sleep(5)
                    return 

    def _make_select_selection(self, select_element_id, selection, needs_initial_click=True, cls=None):
        if cls is not None:
            select_element = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, cls)))
        else:
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

        self._make_select_selection('', '75', cls='yui-pg-rpp-options')
        self._wait_for_loading_mask()

        while len(unchecked_checkbox_ids) > 0:
            for id in unchecked_checkbox_ids.copy():
                try:
                    checkbox = self.driver.find_element_by_id(id)
                    self.driver.execute_script('arguments[0].scrollIntoView({ behavior: "auto", block: "center", inline: "center"});', checkbox)
                    checkbox.click()
                    unchecked_checkbox_ids.remove(id)
                    checked_checkbox_ids.add(id)
                except NoSuchElementException:
                    pass

            next_page_button = self.driver.find_element_by_id('paginator_below').find_element_by_class_name('yui-pg-next')
            if next_page_button.is_enabled():
                next_page_button.click()
            else:
                print('Could not find entries for {}'.format(', '.join(unchecked_checkbox_ids)))
                break
            self._wait_for_loading_mask()

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
        print('Downloaded successfully')
    except Exception as e:
        raise e
    finally:
        scraper.cleanup()


if __name__ == '__main__':
    main()
