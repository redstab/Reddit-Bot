from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import pickle
import time
import os
import sys
import random
import argparse


def url_validator(x):
    valid_url = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        # domain...
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(valid_url, x) is not None

def new_chrome():
    driver_path = r"C:\Users\Jens\source\repos\redstab\Reddit-Bot\Reddit Bot\Chrome Driver\chromedriver.exe"
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.default_content_setting_values.notifications": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--log-level=3")
    return webdriver.Chrome(executable_path=driver_path, options=chrome_options)

def add_account(username: str, password: str):
    pickle.dump((username, password), open("database", "wb"))

def login(drv, username, password):
    
    drv.get("http://reddit.com/login")

    user_field = "#loginUsername"
    pass_field = "#loginPassword"

    login_btn = ".AnimatedForm__submitButton"
    result = ".AnimatedForm__errorMessage"

    drv.find_element_by_css_selector(user_field).send_keys(username)
    drv.find_element_by_css_selector(pass_field).send_keys(password)

    drv.find_element_by_css_selector(login_btn).click()

    time.sleep(0.5)

    login_result = drv.find_element_by_css_selector(result).text

    return not login_result

def logout(drv):
    drv.delete_all_cookies()
    drv.refresh()

def set_cookie(drv, cookie):
    drv.add_cookie(cookie)

def save_cookies(credentials: str, cookie_directory: str):

    file = open(credentials, "r")
    accounts = file.readlines()
    file.close()

    if not os.path.exists(cookie_directory):
        os.makedirs(cookie_directory)
    
    os.chdir(cookie_directory)

    driver = new_chrome()

    wait = WebDriverWait(driver, 10)
   
    print()

    for account in accounts:
        username, password = account.split(' | ')
        cookie_file = username + ".c0ki"
        print("[~] Saving Cookie from user: {}".format(username))
        driver.delete_all_cookies()
        print("    [+] Logging in user")
        if(login(driver, username, password)):
            print("    [~] Waiting for Signin to complete")
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".header-user-dropdown"))
            )
            print("    [+] Signin completed")
            print("    [+] Dumping cookies to \"{}\"".format(cookie_file))
            pickle.dump(driver.get_cookies(), open(cookie_file, "wb"))
            print("    [+] Logging out")
            logout(driver)
            print("    [+] Successfully Saved Cookies\n")
        else:
            print("    [-] Invalid credentials")
            print("    [-] Exiting")
            sys.exit()
    
def chain_upvote(drv, url, cookies_directory):
    for cookie_file in os.listdir(cookies_directory):
        print("Upvoting with: {}", cookie_file)
        drv.delete_all_cookies()
        drv.get(url)
        cookies = pickle.load(open(cookies_directory+"\\"+cookie_file, "rb"))
        for cookie in cookies:
            drv.add_cookie(cookie)
        drv.refresh()
        time.sleep(1000)
        #post_upvote(drv, url)
        # cookies are fuked so it wont upvote, this needs some fix maybe login and upvote instead of cookies
def post_upvote(drv, url):

    regex = r"(?<=\/comments\/)[a-z-0-9]{6}"

    if(url_validator(url)):
        print("Url is valid -> Extracting Post ID")
        url_search = re.search(regex, url)
        if(url_search is not None):
            post_id = url_search.group()
            print("Post ID found: {}".format(post_id))

            upvote_btn = str("#upvote-button-t3_" + post_id)
            btn = drv.find_element_by_css_selector(upvote_btn)
            btn.click()
            time.sleep(3)
        else:
            print("Post ID was not found in the url")
    else:
        print("URL is not valid")

def main():
    parser = argparse.ArgumentParser(description="Upvotes a reddit post with multiple accounts")
    parser.add_argument('reddit_posts', help="the posts to upvote", nargs='?')
    parser.add_argument('-g', help="generate cookies from credentials file in cookie directory", action="store_true")
    parser.add_argument('-a', help="the credentials file", dest="cred_file")
    parser.add_argument('-c', help="the directory which hold all the cookies", dest="cookie_dir", required="true")
    args = parser.parse_args()

    if(args.g): # If wants to generate cookies
        save_cookies(args.cred_file, args.cookie_dir) # Generate
    
    if(args.cookie_dir):
        print("\nPost: {}\nCredentials: {}\nCookie Directory: {}".format(args.reddit_posts, args.cred_file, args.cookie_dir))
        chain_upvote(new_chrome(), args.reddit_posts, args.cookie_dir)


if __name__ == "__main__":
    main()
