import abc
import os

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains


# TODO: how do I differentiate between requests to pull many pages into one dataset,
# TODO: and those that pull a single page into many datasets?


class SportsDataScraper:
    __metaclass__ = abc.ABCMeta

    _config = None
    _driver = webdriver.Firefox()
    _year_token = '-YEAR-'
    _league_token = '-LEAGUE-'
    _player_token = '-PLAYER-'
    _team_token = '-TEAM-'
    _css_selector_token = '-CSSBASE-'

    __hasmore_css_path = _css_selector_token + ' > div.section_heading > div > ul > li.hasmore '
    __csv_button_selector = '> div > ul > li:nth-child(4) > button'

    def __del__(self):
        try:
            if self._driver:
                self._driver.quit()
        except:
            pass

    def _get_base_cache_path_for_sport(self):
        return os.path.join(os.path.curdir, 'cache', self._config.league_name)

    def _scroll_to_element(self, element):
        print('scrolling element "{0}" into view...'.format(element.text))
        driver = self._driver
        driver.execute_script('arguments[0].scrollIntoView(true);', element)
        driver.execute_script('window.scrollBy(0, -100);')

    def _hover_element(self, element):
        try:
            print('trying to hover to element with text "{0}"...'.format(element.text))
            driver = self._driver
            """
            if element:
                element.screenshot('hover_me.png')
            else:
                print('Tried to screenshot element with text "{0}", but can\'t find it!'.format(element.text))
            """
            hov = ActionChains(driver).move_to_element(element)
            hov.perform()
        except Exception as e:
            print(e)
            pass

    def get_element_by_css(self, url, css):
        driver = self._driver
        driver.get(url)
        # TODO: handle not-found case by returning []
        return driver.find_element_by_css_selector(css)

    def get_html_table(self, url, css_table_name):
        return self.get_element_by_css(url, 'div' + css_table_name + ' > div.table_outer_container')

    def get_csv_table(self, url, css_table_name, read_cache=True, write_cache=True, cache_filename='',
                      hide_partial_rows=False):
        if read_cache and cache_filename:
            cached_stats = SportsDataScraper._read_cache_data(cache_filename)

            if cached_stats:
                # print('found a cached copy of {0}\'s {1} table, not contacting the web after all.'
                #       .format(url, css_table_name))
                return cached_stats

        selector_base = SportsDataScraper.__hasmore_css_path.replace(SportsDataScraper._css_selector_token,
                                                                     css_table_name)

        if not self._driver:
            self._driver = webdriver.Firefox()
        driver = self._driver

        try:
            driver.get(url)

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

            get_csv_button = driver.find_element_by_css_selector(
                selector_base + self.__csv_button_selector)

            if get_csv_button:
                self._scroll_to_element(get_csv_button)
                self._hover_element(get_csv_button)
                get_csv_button.click()
                # TODO: not properly hovering Get CSV button. Is it the -100 scroll?

                '''to generalize, it should probably look for a "pre" tag inside the table container
                or use the name of the original table to get the csv table name
                (they usually have the name "#csv_stats" based on a table name of "#all_stats)
                but if we've only clicked one "get csv" button, it should be the only "pre" on the page'''
                these_stats = driver.find_element_by_css_selector('pre').text
                # print(these_stats)
            else:
                raise NoSuchElementException('Could not find the button to get CSV stats!')
        finally:
            driver.close()

        if write_cache and cache_filename:
            SportsDataScraper._write_cache_data(these_stats, cache_filename)

        return these_stats

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

        print('Writing team stats ({0}-{1}) to file: {2}'.format(start_year, end_year, output_filename))

        if output_filename:
            scrape_data.to_csv(output_filename)
