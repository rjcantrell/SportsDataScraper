import abc
import os
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.webdriver import WebDriver


def __get_if_needed(self, url):
    if self.current_url != url:
        self.get(url)


WebDriver.get_if_needed = __get_if_needed


class SportsDataScraper:
    __metaclass__ = abc.ABCMeta

    _debug = False
    _config = None
    _driver = webdriver.Firefox()
    _year_token = '-YEAR-'
    _league_token = '-LEAGUE-'
    _player_token = '-PLAYER-'
    _team_token = '-TEAM-'
    _css_selector_token = '-CSSBASE-'

    __hasmore_css_path = _css_selector_token + ' > div.section_heading > div > ul > li.hasmore '
    __csv_button_selector = ' > div > ul > li:nth-child(4) > button'

    def __init__(self, debug=False):
        self._debug = debug

    def __del__(self):
        try:
            if self._driver:
                self._driver.quit()
        except:
            pass

    def get_element_by_css(self, url, css):
        ret_val = None
        elements = self.get_elements_by_css(url, css)
        if elements and len(elements):
            ret_val = elements[0]
        return ret_val

    def get_elements_by_css(self, url, css):
        driver = self._driver
        driver.get_if_needed(url)
        return driver.find_elements_by_css_selector(css)

    def get_html_table(self, url, css_table_name):
        return self.get_element_by_css(url, 'div' + css_table_name + ' > div.table_outer_container')

    def get_csv_table(self, url, css_table_name, read_cache=True,
                      write_cache=True, cache_filename='',
                      hide_partial_rows=False):

        if read_cache and cache_filename:
            cached_stats = SportsDataScraper._read_cache_data(cache_filename)

            if cached_stats:
                self._dbg_print('found a cached copy of {0}\'s {1} table, not contacting the web after all.'
                                .format(url, css_table_name))
                return cached_stats

        selector_base = SportsDataScraper.__hasmore_css_path.replace(SportsDataScraper._css_selector_token,
                                                                     css_table_name)

        if not self._driver or self._driver.start_client():
            self._driver = webdriver.Firefox()
        driver = self._driver

        driver.get_if_needed(url)

        if hide_partial_rows:
            partial_rows_button = driver.find_element_by_css_selector(css_table_name +
                                                                      " button[id$='_toggle_partial_table']")

            if partial_rows_button:
                partial_rows_button.click()
            else:
                print('Could not find the partial rows button. = (')

        sharing_dropdown = driver.find_element_by_css_selector(selector_base + '> span')
        if sharing_dropdown:
            self._scroll_to_element(sharing_dropdown)
            self._hover_element(sharing_dropdown)
        else:
            raise NoSuchElementException('Could not find the "Sharing" dropdown!')

        get_csv_button = driver.find_element_by_css_selector(selector_base + self.__csv_button_selector)

        if get_csv_button:
            get_csv_button.click()

            # the web version of the table is e.g., "#all_skaters" and the <pre>-wrapped csv is "#csv_skaters"
            csv_stats = driver.find_element_by_css_selector(css_table_name.replace('#all', '#csv')).text
            # self._dbg_print('Woo, found some stats!\n\n{0}\n'.format(csv_stats))
        else:
            raise NoSuchElementException('Could not find the button to get CSV stats!')

        if write_cache and cache_filename:
            SportsDataScraper._write_cache_data(csv_stats, cache_filename)

        return csv_stats

    @staticmethod
    def validate_start_end_years(start_year, end_year, config):
        invalid_year_message = 'No {0} stats are available for the year {1}!'

        if not int(start_year):
            raise ValueError('Invalid Start Year: "{0}"'.format(start_year))
        if not int(end_year):
            raise ValueError('Invalid End Year: "{0}"'.format(end_year))
        if start_year < config.minimum_year:
            raise ValueError(invalid_year_message.format(config.league_name, start_year))
        if end_year > config.maximum_year:
            raise ValueError(invalid_year_message.format(config.league_name, end_year))

        first = min(start_year, end_year)
        last = max(start_year, end_year)
        return first, last

    @abc.abstractmethod
    def scrape(self, start_year, end_year, read_cache=True, write_cache=True):
        """
        """

    # I'd prefer not to do these if blocks, but you can't reference self._config in the definition
    def scrape_to_file(self, output_filename=None, start_year=None, end_year=None, read_cache=True, write_cache=True):
        if not start_year:
            start_year = self._config.minimum_year
        if not end_year:
            end_year = self._config.maximum_year

        scrape_data = self.scrape(start_year, end_year, read_cache, write_cache)

        self._dbg_print('Writing team stats ({0}-{1}) to file: {2}'.format(start_year, end_year, output_filename))

        if output_filename:
            scrape_data.to_csv(output_filename)

    @staticmethod
    def _read_cache_data(filename):
        data = None
        if os.path.exists(filename):
            copy_file = open(filename, 'r')
            data = ''.join(copy_file.readlines())
            copy_file.close()
        return data

    @staticmethod
    def _write_cache_data(data, filename):
        cache_dir = os.path.dirname(os.path.realpath(filename))
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        if type(data) is list:
            data = '\n'.join(data)

        debug_file = open(filename, 'w')
        debug_file.write(data)
        debug_file.close()

    def _get_base_cache_path_for_sport(self):
        return os.path.join(os.path.curdir, 'cache', self._config.league_name)

    def _scroll_to_element(self, element):
        # self._dbg_print('scrolling element "{0}" into view...', element.text)

        if self._debug:
            if element and element.screenshot_as_png:
                element.screenshot('scroll_to_me.png')
            else:
                self._dbg_print(
                    'Tried to screenshot element with text "{0}", but can\'t find it!'.format(element.text))

        driver = self._driver
        driver.execute_script('arguments[0].scrollIntoView(true);', element)
        driver.execute_script('window.scrollBy(0, -250);')

    def _hover_element(self, element):
        try:
            # self._dbg_print('trying to hover to element with text "{0}"...'.format(element.text))
            driver = self._driver

            if self._debug:
                if element and element.screenshot_as_png:
                    element.screenshot('hover_me.png')
                else:
                    self._dbg_print(
                        'Tried to screenshot element with text "{0}", but can\'t find it!',
                        element.text)

            hov = ActionChains(driver).move_to_element(element)
            hov.perform()
        except Exception as e:
            print(e)
            pass

    def _dbg_print(self, s, *args):
        if self._debug:
            st = s.format(args)
            print('[{0}]:\t{1}'.format(time.asctime(time.localtime()), st))
