# SportsDataScraper
This summer, I took a data visualization class, and wanted some unique data to plot instead of the same hoary old GISTEMP or World-Indicators datasets. The Stanley Cup Playoffs were happening at the time, and my wife happened to ask, "How often do they score?"

Being a nerd, I replied, "Ehhhh, about 10 percent. Give me a few days and I can [break it down by year, team, player-age, and position!](https://public.tableau.com/profile/rj.cantrell#!/vizhome/NHLShotPercentage_midterm/Dashboard)" I decided this would be a pretty good toy-project to try to learn Python. As such, I have no idea how Pythonic or usable it is beyond what my IDE tells me.

## What does this code do?
The inimitable [Sports-Reference.com](https://www.sports-reference.com/) is a great resource for stats, and very easy to scrape because it features standardized URLs, CSS selectors, and a "Get CSV data" button for every table on every page. This code uses the [selenium](https://pypi.python.org/pypi/selenium) package to find the appropriate tables, click the "Get CSV data" button, and save the plaintext data to a file on disk for later analysis.

## What's in this repository?
- **SportsDataScraper.py:** This class can locate a table on a page, download the HTML of a specified table, or click the "Get CSV data" button to download a plaintext version of the table. Results are always returned to the caller, or can be written to disk with the 'write_cache' parameter.
- **SportConfig.py:** Because Hockey-Reference.com contains data from multiple hockey leagues, live and defunct, I created this class to specify which league we're pulling data for, and for which years that league was active. No guarantees are made for backward-compatibility if I extend this code to scrape other sports' reference sites.
- **HockeySeasonScraper.py:** Scrapes league-wide stats for a given year, from Hockey-Reference.com's "Season Summary" pages like [this one](https://www.hockey-reference.com/leagues/NHL_2017.html)
- **HockeyTeamScraper.py:** Scrapes per-team stats for a given team-year combination, from Hockey-Reference.com's "Roster and Statistics" pages like [this one](https://www.hockey-reference.com/teams/PIT/2017.html). Results will include individual stats for each player on that team's roster for that season. It can also report whether a team existed in a given year, and whether they made the playoffs in a given year (in order to record playoff data in a separate CSV file).

## Additions I hope to make
- **HockeyPlayerScraper.py:** I did not need this for my school projects, because much of this data is also present on the team's season summary page. [Player pages](https://www.hockey-reference.com/players/k/kesseph01.html) contain a bit more data not related to NHL seasons, so I hope to provide this one day to make a more complete scrape.
- **HockeyCoachScraper.py:** Maybe if I get injured or develop insomnia, but don't hold your breath. :)

## Okay, so how do I use it?
As this was an ad-hoc project for my schoolwork, I simply had a runme.py file that asked HockeySeasonScraper and HockeyTeamScraper for what I needed. By default, HockeyTeamScraper will attempt to scrape all teams for all years and write each scraped table to `(current directory)\cache\nhl\teams\(year)\(team name)\(table name).csv`. Running the base class' `scrape_to_file` method with no filename means that the data will not be returned as a single dataset, and is the simplest way to locally save all team data for all teams for all seasons.

~~~
scraper = HockeyTeamScraper()
scraper.scrape_to_file()
~~~
