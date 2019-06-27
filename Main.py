from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.expected_conditions import visibility_of_all_elements_located as all_elements_visible 
from selenium.webdriver.support.expected_conditions import visibility_of_element_located as element_visible 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from fuzzywuzzy.process import extract as fuzzy_search
from math import pow, tau, factorial, fsum, fabs
from fuzzywuzzy import fuzz
from tabulate import tabulate
from click import clear
import configparser
import os
import time
import sys
from gflrr import *

def getElements(css_selector):
    try:
        print("Please wait...")
        return WebDriverWait(browser, 10).until(all_elements_visible((By.CSS_SELECTOR, css_selector)))
    except TimeoutException:
        print("Could not load stats from " + mainPage)
        sys.exit(-1)
        
def getElement(css_selector):
    return getElements(css_selector)[0]
    
def isNumerical(conversion_func, s):
    try: 
        conversion_func(s)
        return True
    except ValueError:
        return False
        
def isListedChoice(choice, upper):
    if not isNumerical(int, choice):
        return False
    choice = int(choice)
    return 1 <= choice and choice <= upper

def getAbsChoice(err_func, upper):
    choice = input()
    if not isListedChoice(choice, upper):
        err_func("**Invalid Input**")
        return
    return int(choice)
    
def requestUserAction(prompt, choice_func, *func_args):
    clear()
    print(prompt, end='')
    return choice_func(*func_args)

def main_menu(message=""):
    prompt = f"""Statistics sourced from {domain}
GFL Recipe Recommender made by Vimtron (UID: 588679)

** Please type a selection and press enter **

[1] Recipes
[2] Settings
[3] Explanation
[4] Quit
{message}
> """
    choice = requestUserAction(prompt, getAbsChoice, main_menu, 4)
    if choice == 1:
        categories_page()
    elif choice == 2:
        settings_page()
    elif choice == 3:
        # Explanation
        pass
    elif choice == 4:
        sys.exit(0)
        
def categories_page():
    choices_column = ""
    num_of_options = len(crafts.keys()) + 1
    width = len(str(num_of_options)) + 3
    for num, cat in enumerate(crafts.keys(), start=1):
        choices_column += f"[{num}]".ljust(width) + cat + os.linesep
    prompt = f"""** Please type a selection and press enter **
** You may also give a query to search **

Recipe Categories
{choices_column}
[{num_of_options}] Go back to main menu

> """
    choice = requestUserAction(prompt, input)
    if isListedChoice(choice, num_of_options):
        choice = int(choice)
        if choice == num_of_options:
            main_menu()
        else:
            individual_category_page(crafts[[*crafts][choice - 1]])
    else:
        query_page(choice)
        
def individual_category_page(crafts):
    choices_column = ""
    num_of_options = len(crafts) + 1
    width = len(str(num_of_options)) + 3
    for num, craft in enumerate(crafts, start=1):
        choices_column += f"[{num}]".ljust(width) + ("*" * craft.get_num_of_stars()).ljust(6) + craft.get_name() + \
            os.linesep

    prompt = f"""** Please type a selection and press enter **
** You may also give a query to search **

{crafts[0].get_type()} Category
{choices_column}
[{num_of_options}] Go back to category list

> """
    choice = requestUserAction(prompt, input)
    if isListedChoice(choice, num_of_options):
        choice = int(choice)
        if choice == num_of_options:
            categories_page()
        else:
            crafting_recipes_page(crafts[choice - 1])
    else:
        query_page(choice)

def get_top_n_recipes(craft, prod_info, n):
    browser.get(craft.get_url_to_page())
    table = getElement("table.table.recipe-table")
    data_rows = []
    if prod_info[1] == 3 or prod_info[1] == 1:
        data_rows.extend(table.find_elements_by_css_selector("tbody > tr.recipe.type-normal"))
    if prod_info[1] == 3 or prod_info[1] == 2:
        data_rows.extend(table.find_elements_by_css_selector("tbody > tr.recipe.type-heavy"))
    z_score = config["Main"]["z-score"]
    sorting_key = lambda recipe: recipe.lower_bound
    top_recipes = sorted([Recipe(data_row, z_score) for data_row in data_rows], key=sorting_key, reverse=True)[0:n]
    return [[rank, *vars(recipe).values()] for rank, recipe in enumerate(top_recipes, start=1)]
        
   
def crafting_recipes_page(craft, prod_info=("NORMAL", 1)):
    headers = ["Rank", "Manpower", "Ammo", "Rations", "Parts", "Tier", "Hits", "Attempts", "Rate", "Lower bound", "TATBH"]
    recipes = get_top_n_recipes(craft, prod_info, int(config["Main"]["num_of_recipes_to_show"]))
    message = os.linesep + "***** No results found *****" if recipes == [] else ""
    prompt = f"""** Please type a selection and press enter **
** You may also give a query to search **
    
{craft.get_type()} {craft.get_name()} | {prod_info[0]} production only | {getElement("body > p:nth-child(4)").text}

{tabulate(recipes, headers=headers, tablefmt="presto", numalign="left")}{message}

[1] Show only normal production recipes
[2] Show only heavy production recipes
[3] Show both normal and heavy production recipes
[4] Go back to category list

> """
    choice = requestUserAction(prompt, input)
    
    if isListedChoice(choice, 4):
        choice = int(choice)
        if choice == 1:
            crafting_recipes_page(craft, prod_info=NORMAL_PROD)
        elif choice == 2:
            crafting_recipes_page(craft, prod_info=HEAVY_PROD)
        elif choice == 3:
            crafting_recipes_page(craft, prod_info=BOTH_PROD)
        else:
            categories_page()
    else:
        query_page(choice)
       
def get_n_queried_results(query, n):
    queried_results = fuzzy_search(query, crafts_by_names.keys(), limit=int(n), scorer=fuzz.partial_ratio)
    return [(crafts_by_names[result[0]], result[1]) for result in queried_results]
    
def query_page(query):
    num_of_crafts = int(config["Main"]["num_of_query_results"])
    queried_list = get_n_queried_results(query, num_of_crafts)

    num_of_options = int(num_of_crafts) + 1
    bracket_width = len(str(num_of_options)) + 3
    percent_width = len(str(queried_list[0][1])) + 2
    type_width = max(len(query[0].get_type()) for query in queried_list) + 1
    star_width = max(query[0].get_num_of_stars() for query in queried_list) + 1
    
    choices_col = ""
    for num, queried_craft in enumerate(queried_list, start=1):
        craft = queried_craft[0]
        percent = queried_craft[1]
        choices_col += f"[{num}]".ljust(bracket_width)
        choices_col += f"{percent}%".ljust(percent_width)
        choices_col += f"{craft.get_type()}".ljust(type_width)
        choices_col += ("*" * craft.get_num_of_stars()).ljust(star_width)
        choices_col += craft.get_name()
        choices_col += os.linesep


    prompt = f"""** Please type a selection and press enter **
** You may also give a query to search **

Search query: {query}
{choices_col}

[{num_of_options}] Go back to category list

> """
    choice = requestUserAction(prompt, input)
    if isListedChoice(choice, num_of_options):
        choice = int(choice)
        if choice == num_of_options:
            categories_page()
        else:
            crafting_recipes_page(queried_list[choice - 1][0])
    else:
        query_page(choice)
   
def get_probability(z):
    return 0.5 + pow(tau, -0.5) * fsum(pow(-1, n) * pow(z, 2 * n + 1) / ((2 * n + 1) * factorial(n) * pow(2, n)) for n in range(41))
        
def standard_bell_curve(z):
    return pow(tau, -0.5) * fsum(pow(-1, n) * pow(z, 2 * n) / (factorial(n) * pow(2, n)) for n in range(41))
        
def get_z_score(prob, init_z=0, count=0):
    if count > 20:
        return init_z
    new_z = init_z - (get_probability(init_z) - prob) / standard_bell_curve(init_z)
    if fabs(new_z - init_z) < 0.0001:
        return new_z
    else:
        return get_z_score(prob, init_z=new_z, count=count + 1)
   
def settings_page(message=""):
    z = float(config["Main"]["z-score"])
    z_score = "{:0.3f}".format(z)
    confidence = "{:0.3%}".format(get_probability(z))

    prompt = f"""** Please type a selection and press enter to change a setting or go back**

[1] Z-score: {z_score}
[2] Using {confidence} Confidence Intervals
[3] Number of recipes to show: {config["Main"]["num_of_recipes_to_show"]}
[4] Number of query results: {config["Main"]["num_of_query_results"]}

[5] Go back to main menu
{message}
> """
    choice = requestUserAction(prompt, getAbsChoice, settings_page, 5)
   
    isInt = lambda x: isNumerical(int, x)
    isFloat = lambda x: isNumerical(float, x)
    if choice == 1:
        new_value = settings_change_page("Z-score", z_score, isFloat)
        change_config("Main", "z-score", new_value)
    elif choice == 2:
        new_value = float(settings_change_page("Confidence (as percentage)", confidence, isFloat, 
                                               "Do not include the percentage sign")) / 100
        change_config("Main", "z-score", get_z_score(new_value))
    elif choice == 3:
        new_value = settings_change_page("Number of recipes to show", config["Main"]["num_of_recipes_to_show"], isInt)
        change_config("Main", "num_of_recipes_to_show", new_value)
    elif choice == 4:
        new_value = settings_change_page("Number of query results", config["Main"]["num_of_query_results"], isInt)
        change_config("Main", "num_of_query_results", new_value)
    elif choice == 5:
        return
    settings_page()
    
def settings_change_page(printable_name, old_value, input_check_func, message=""):
    prompt = f"""** Please type a new value and then press enter**
{os.linesep + message + os.linesep if message else ""}
OLD: {printable_name} == {old_value}
NEW: {printable_name} == """
#
    choice = requestUserAction(prompt, input)
    if not input_check_func(choice):
        settings_change_page(printable_name, old_value, input_check_func, message="** Invalid Input. Please try again. **")
    return choice
    
def change_config(section, name, new_value):
    config[section][name] = str(new_value)
    with open('Config.txt', 'w') as configfile:
        config.write(configfile)

if __name__ == "__main__":
    clear()
    
    domain = "https://sangvis.science"
    mainPage = domain + "/list/all"
    
    NORMAL_PROD = ("NORMAL", 1)
    HEAVY_PROD = ("HEAVY", 2)
    BOTH_PROD = ("NORMAL & HEAVY", 3)

    config = configparser.ConfigParser()
    config.read("Config.txt")
    
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    browser = webdriver.Chrome(options=options)
    browser.get(mainPage)
    
    crafts = {}  
    current_type = ""
    for elem in getElement(".content").find_elements_by_css_selector("*"):
        if elem.get_attribute("class") == "craft-type":
            current_type = elem.text
        else:
            craft = Craft(int(elem.get_attribute("class")[-1]), elem.text, elem.get_attribute("href"), current_type)
            if craft.get_type() not in crafts.keys():
                crafts[craft.get_type()] = [craft]
            else:
                crafts[craft.get_type()].append(craft)
          
    crafts_by_names = {}   
    for category_list in crafts.values():
        for craft in category_list:
            crafts_by_names[craft.get_name()] = craft
          
    while True:
        main_menu()
        