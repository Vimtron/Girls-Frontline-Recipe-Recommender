import re
from math import sqrt, ceil

class Craft(object):
    def __init__(self, num_of_stars: int, name: str, url_to_page: str, type: str, id: int = None):
        self.num_of_stars = num_of_stars
        self.name = name
        self.url_to_page = url_to_page
        self.type = type
        if id == None:
            self.id = int(re.search(".*/(\d+)", self.url_to_page).group(1))
        else:
            self.id = id
    
    def get_name(self):
        return self.name
        
    def get_num_of_stars(self):
        return self.num_of_stars
        
    def get_url_to_page(self):
        return self.url_to_page

    def get_type(self):
        return self.type
    
    def get_id(self):
        return self.id
        
class Recipe(object):
    def __init__(self, data_row, z_score):
        data_cells = data_row.find_elements_by_css_selector(".formula")
        self.manpower = float(data_cells[0].text)
        self.ammo = float(data_cells[1].text)
        self.rations = float(data_cells[2].text)
        self.parts = float(data_cells[3].text)
        self.tier = float(data_cells[4].text)
        self.hits = float(data_cells[7].text)
        self.attempts = float(data_cells[8].text)
        rate = self.hits / self.attempts
        lower_bound = self.get_lower_bound(rate, z_score)
        self.rate = "{:.3%}".format(rate)
        self.lower_bound = "{:.3%}".format(lower_bound)
        self.TATBH = ceil(1 / lower_bound)
            
    def get_lower_bound(self, p, z_score):
        n = self.attempts
        z = float(z_score)
        return p - z * sqrt(p * (1 - p) / n)