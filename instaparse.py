from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import json, time, pandas as pd

USERNAME = 'larepubblica'

# 1) Set up headless Firefox
opts = Options()
opts.headless = True
driver = webdriver.Firefox(options=opts)  # requires geckodriver in your PATH

# 2) Load the page
driver.get(f'https://www.instagram.com/')
time.sleep(4)

# 3) Scroll to load more posts
for _ in range(10):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

# 4) Grab page source & quit
html = driver.page_source
driver.quit()

# 5) Parse the embedded JSON
soup = BeautifulSoup(html, 'html.parser')
script = soup.find('script', text=lambda t: t and 'window._sharedData' in t).string
json_text = script.split(' = ', 1)[1].rstrip(';')
data = json.loads(json_text)

edges = (
    data['entry_data']['ProfilePage'][0]
        ['graphql']['user']['edge_owner_to_timeline_media']['edges']
)

# 6) Build your DataFrame
rows = []
for edge in edges:
    node = edge['node']
    rows.append({
        'shortcode': node['shortcode'],
        'timestamp': pd.to_datetime(node['taken_at_timestamp'], unit='s'),
        'caption':   node.get('edge_media_to_caption',{}) \
                         .get('edges',[{}])[0] \
                         .get('node',{}) \
                         .get('text',''),
        'likes':     node['edge_liked_by']['count'],
        'comments':  node['edge_media_to_comment']['count'],
        'media_url': node['display_url'],
    })

df = pd.DataFrame(rows)
df.to_csv(f'{USERNAME}_selenium_posts.csv', index=False)
print(f"Scraped {len(df)} posts via Selenium + Firefox")