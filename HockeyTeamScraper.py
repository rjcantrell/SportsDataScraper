import abc
import csv
import io
import os
import re

from SportConfig import SportConfig
from SportsDataScraper import SportsDataScraper


class HockeyTeamScraper(SportsDataScraper):
    @property
    def all_team_names(self):
        if not self.__team_names:
            self.__team_names = self.__init_team_names()
        return self.__team_names

    _config = SportConfig.NHL()

    __team_names = []
    __url_base = 'http://www.hockey-reference.com/teams/'
    __team_url_base = __url_base + SportsDataScraper._team_token + '/' + SportsDataScraper._year_token + '.html'
    __url_regex = __url_base + '(.*)/'
    __defunct_tag = ' (defunct)'

    @staticmethod
    def __get_url(year, team_name):
        return HockeyTeamScraper.__team_url_base.replace(SportsDataScraper._team_token, team_name) \
            .replace(SportsDataScraper._year_token, str(year))

    @abc.abstractmethod
    def scrape(self, start_year, end_year, read_cache=True, write_cache=True):
        return self.scrape_teams(start_year, end_year,
                                 set([x['Abbrev'] for x in self.all_team_names]),
                                 read_cache, write_cache)

    def get_teams_overview(self, read_cache=True, write_cache=True, cache_filename=None):
        if (read_cache or write_cache) and not cache_filename:
            cache_filename = os.path.join(os.path.curdir, 'cache', self._config.league_name, 'teams_overview.csv')

        raw_team_data = self.__get_team_stats().split('\n')  # func returns a string, so make a list

        # header = raw_team_data[0]  # in case I need to pass it to csv.DictReader as fieldnames
        team_data = [re.sub('^Franchise,Lg,', 'Abbrev,Franchise,Lg,', raw_team_data[0])]
        for this_team in raw_team_data[1:]:  # skip the header, naturally
            this_name = this_team.split(',')[0]  # team name is the first field
            matching_abbrevs = [abbr for abbr, name in self.all_team_names if name == this_name]
            this_abbrev = ''
            if matching_abbrevs:
                this_abbrev = matching_abbrevs[0]
            this_team = this_abbrev + ',' + this_team
            team_data.append(this_team)

        str_team_data = '\n'.join(team_data)
        if write_cache and cache_filename and team_data:
            SportsDataScraper._write_cache_data(str_team_data, cache_filename)

        with io.StringIO(str_team_data) as in_file:
            return list(csv.DictReader(in_file))

    def __init_team_names(self, read_cache=True, write_cache=True, cache_filename=None):
        team_names = set()  # list of (abbreviation, full_name) tuples
        cached_stats = None
        team_identities = []

        if (read_cache or write_cache) and not cache_filename:
            cache_filename = os.path.join(os.path.curdir, 'cache', self._config.league_name, 'team_identities.csv')

        if read_cache and cache_filename:
            cached_stats = self._read_cache_data(cache_filename)

        if not cached_stats:
            for table_name in ('#all_active_franchises', '#all_defunct_franchises'):
                team_table = self.get_html_table(self.__url_base, table_name)
                team_links = team_table.find_elements_by_css_selector('a')

                for link in team_links:
                    name = link.text
                    if name in [n for abbr, n in team_names]:
                        name += self.__defunct_tag
                    regex_result = re.search(self.__url_regex, link.get_attribute('href'))
                    abbrev = regex_result.groups()[0]
                    team_names.add((abbrev, name))

            for abbr, name in team_names:
                # TODO: when loading from cache, you get teams like MDA which don't have a page...
                team_abbrevs = self.get_all_identities_for_team(abbr)  # will eval to False if not found
                if team_abbrevs:
                    team_identities.append(team_abbrevs)

            cached_stats = 'Year,Abbrev,Name,Made_Playoffs\n'
            for rv in sorted(team_identities[:-1]):  # all except the last, so there's not a trailing newline
                cached_stats += ','.join([str(x) for x in rv]) + '\n'
            cached_stats += ','.join([str(x) for x in team_identities[-1]])  # last line only, no newline

        with io.StringIO(cached_stats) as in_file:
            ret_val_csv = list(csv.DictReader(in_file))

        if write_cache:
            self._write_cache_data(cached_stats, cache_filename)

        return ret_val_csv

    def get_all_identities_for_team(self, abbr):
        links = self.get_element_by_css(url=self.__url_base + abbr, css='#' + abbr + ' > tbody td:nth-child(3)')
        for link in links:
            # print('found a link with text = "' + link.get_attribute('innerHTML') + '"')
            inner_html = link.get_attribute('innerHTML')
            link_pattern = '^<a href="\/teams\/(.+)\/(.+).html">(.+)<\/a>(.*)$'
            reg = re.match(link_pattern, inner_html)
            if reg:
                abbrev, year, name, made_playoffs = reg.groups()
                return year, abbrev, name, len(made_playoffs) > 0

    def __get_team_stats(self):
        cache_path = os.path.join(self._get_base_cache_path_for_sport(), 'active_teams.csv')
        active_teams = self.get_csv_table(self.__url_base, '#all_active_franchises',
                                          hide_partial_rows=True,
                                          cache_filename=cache_path)

        print('Trying to get defunct teams...')
        cache_path = re.sub('active', 'defunct', cache_path)
        defunct_teams = self.get_csv_table(self.__url_base, '#all_defunct_franchises',
                                           hide_partial_rows=True,
                                           cache_filename=cache_path)

        # both tables will have a header(the first line of each), but we only want to keep one.
        # also, the last line of the tables don't terminate in a newline that we split on.
        # we can fix both of these at once by removing the header from the second table BUT LEAVING THE NEWLINE
        defunct_teams = defunct_teams[defunct_teams.find('\n'):]

        all_teams = []
        with io.StringIO(active_teams + defunct_teams) as csv_file:
            seen_teams = set()
            all_team_rows = list(csv.reader(csv_file))
            for row in all_team_rows:
                if row[0] in seen_teams:
                    row[0] += self.__defunct_tag
                seen_teams.add(row[0])
                all_teams.append(','.join(row))

        return '\n'.join(all_teams)

    def scrape_teams(self, start_year, end_year, teams, read_cache=True, write_cache=True):
        first, last = SportsDataScraper.validate_start_end_years(start_year, end_year, self._config)

        all_results = {}
        for year in range(last, first, -1):
            for team in teams:
                self.__get_team_for_year(year, team, read_cache, write_cache)

    def __get_team_for_year(self, year, team, read_cache=True, write_cache=True):
        if not self.__did_team_exist(team, year):
            print('Team {0} did not exist in the year {1}. Skipping...'.format(team, year))
            return None

        cache_directory = os.path.join(self._get_base_cache_path_for_sport(), 'teams', str(year), team)
        cache_roster_filename = os.path.join(cache_directory, 'roster.csv')

        roster = self.get_csv_table(HockeyTeamScraper.__get_url(year, team), '#all_roster',
                                    read_cache, write_cache, cache_roster_filename)
        pass

    def __did_team_exist(self, team, year):
        return len([x for x in self.all_team_names if x['Abbrev'] == team and x['Year'] == str(year)]) > 0
