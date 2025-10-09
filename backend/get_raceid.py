import re

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


URL = 'https://race.netkeiba.com/top/race_list.html?kaisai_date=20250920'


def get_race_ids(url: str) -> list[str]:
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(url)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#RaceTopRace')))

        soup = BeautifulSoup(driver.page_source, 'lxml')

        race_ids = []

        for a_tag in soup.select('.RaceList_DataItem > a:first-of-type'):
            race_id = re.search(r'race_id=(.+)&', a_tag.get('href')).group(1)
            race_ids.append(race_id)
    finally:
        driver.quit()

    return race_ids


if __name__ == '__main__':
    race_ids = get_race_ids(URL)
    print(race_ids)

'''
['202405040801', '202405040802', '202405040803', '202405040804',
..., '202404040810', '202404040811', '202404040812']
'''