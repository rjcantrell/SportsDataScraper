import abc
import csv
import io
import os
import re

import pandas as pd

from SportConfig import SportConfig
from SportsDataScraper import SportsDataScraper


class HockeySeasonScraper(SportsDataScraper):
    _url_base = 'http://www.hockey-reference.com/leagues/NHL_' + \
                SportsDataScraper._year_token + '.html'

    _config = SportConfig.NHL()

    @staticmethod
    def __get_url(year):
        return re.sub(HockeySeasonScraper._year_token,
                      str(year),
                      HockeySeasonScraper._url_base)

    @staticmethod
    def __assemble_dataset(all_stats):
        combined_years = pd.DataFrame()

        for year in all_stats:
            # remove header categorizing the stat
            # and last row with calculated 'League Average' stats
            year_stats = all_stats[year][1:-1]

            '''Let's add a header for the Team Name field they left unlabeled.
            Maybe they omit it so you don't join on it. For example, the
            Winnipeg Jets (2011-) are not the same team as the Winnipeg
            Jets (1979-1995); the former were previously known as the Atlanta
            Thrashers and the latter are now known as the Arizona Coyotes.'''
            found_header_row = False
            if len(year_stats) > 0:
                matched = re.sub('^Rk,,', 'Rk,Team,', year_stats[0])
                if matched:
                    found_header_row = True
                header_row = 'Year,' + matched

            if len(year_stats) > 1:  # prepend $year to non-header lines
                year_stats = ['{0},{1}'.format(str(year), item) for item in year_stats[1:]]

            if found_header_row and len(header_row):
                year_stats.insert(0, header_row)  # put the header back up top

            year_stats_string = ''.join(year_stats)
            with io.StringIO(year_stats_string) as csv_file:
                reader = list(csv.reader(csv_file))
                if reader:  # Still cursing the 04-05 lockout a decade later!
                    year_dataframe = pd.DataFrame(data=reader[1:],
                                                  columns=reader[0],
                                                  index=None)

                    combined_years = combined_years.append(year_dataframe, ignore_index=True)

        return combined_years

    def __get_team_stats(self, year, read_cache=True, write_cache=True):
        cache_directory = os.path.join(self._get_base_cache_path_for_sport(), 'seasons')
        cache_filename = os.path.join(cache_directory, str(year) + '.csv')

        this_years_stats = self.get_csv_table(HockeySeasonScraper.__get_url(year), '#all-stats',
                                              read_cache, write_cache, cache_filename)
        return this_years_stats

    @abc.abstractmethod
    def scrape(self, start_year, end_year, read_cache=True, write_cache=True):
        first, last = SportsDataScraper.validate_start_end_years(start_year, end_year, self._config)

        stats_dict = {}
        print('Scraping hockey team stats, {0} to {1}'.format(first, last))
        for year in range(first, last):
            stats_dict[year] = self.__get_team_stats(year)

        return HockeySeasonScraper.__assemble_dataset(stats_dict)
