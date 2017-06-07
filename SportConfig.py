class SportConfig:
    __minimum_year = 0
    __maximum_year = 0
    __league_name = ''

    @property
    def minimum_year(self):
        return self.__minimum_year

    @property
    def maximum_year(self):
        return self.__maximum_year

    @property
    def league_name(self):
        return self.__league_name

    def __init__(self, league, min_year, max_year):
        self.__league_name = league
        self.__minimum_year = min_year
        self.__maximum_year = max_year

    @staticmethod
    def NHL():
        return SportConfig('nhl', 1918, 2017)
