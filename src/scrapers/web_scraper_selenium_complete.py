from bs4 import BeautifulSoup
from urllib.parse import urljoin
from src.logger import logging 
from urllib.parse import urljoin, urlparse
from src.data_processing.text_processing import process_tat
import time 
# https://myexternalip.com/raw
import random
def rand_proxy():
    proxy= random.choice(ips)
    return proxy

# Set up WebDriver

async def selenium_fetch_links(url):
    logging.info("Inside seenium_fetch_links")
    from selenium.webdriver.common.by import By
    import time
    from src.constant import ips
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium import webdriver

    driver = webdriver.Chrome()

    try:
        driver.get(url)
        # WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'load-more')))
        driver.implicitly_wait(15)
        page_source =  driver.page_source
        time.sleep(15)
        logging.info(f"page_Sorce :{page_source}")
        
        soup = BeautifulSoup(page_source, 'html.parser')
        time.sleep(15)
        logging.info("soup: {}".format(soup))

        links = soup.find_all('a', href=True)
        logging.info("links: {}".format(links))

        list_of_links=[url]
        extracted_links = [urljoin(url, link['href']) for link in links if is_valid_link(url, link['href'])]
        list_of_links.extend(extracted_links)
        list_of_links = list(set(list_of_links))  # Remove duplicates
        logging.info("list_of_links: {}".format(list_of_links))

        return 1, list_of_links
    
    except Exception as e:
        logging.error(f"An error occurred while fetching through selenium: {str(e)}")
        return 0, str(e)
  

def is_valid_link(base_url, link):
    if link.startswith('#') or link.startswith('javascript:') or link.startswith('mailto:') or link.startswith("tel:"):
        return False
    if 'maps.app.goo.gl' in link:  
        return False
    if 'google.com/maps' in link:   
        return False
    if any(domain in link for domain in ['linkedin.com','.pdf','.zip', 'xlsx','.jpg','twitter.com', 'facebook.com', 
            'youtube.com','play.google.com','instagram.com','dlai.in']): 
        return False
    if not link.startswith('http'): 
        link = urljoin(base_url, link)
    
    parsed_link = urlparse(link)# Parse the URL to get the domain
    base_domain = urlparse(base_url).netloc
    if parsed_link.netloc != base_domain and not parsed_link.netloc.endswith('.' + base_domain):
        return False
    return True




async def extract_contents_selenium_c(links,crawl_application_name, crawl_application_id, crawl_link):
    from bs4 import BeautifulSoup
    from src.logger import logging
    from src.data_processing.text_processing import process_raw_text, generate_embedding
    from src.utils import get_database
    from selenium import webdriver

    
    try:
        logging.info("Inside extract_content_selenium")
        logging.info(f"links:{links}")

        db= get_database()
        header_footer = "no"
        raw_text = []
        web_data = []
        c = 0
        driver = webdriver.Chrome()
        
        Total_Links=len(links)          
        start_time=time.time()

        for link in links[:72]:
            try:
                driver.get(link)
                driver.implicitly_wait(10)
        
                html = driver.page_source
                driver.implicitly_wait(5)
               
                parsed_content = BeautifulSoup(html, 'html.parser')
               
                # noscripts = parsed_content.find_all('noscript')
                # for noscript in noscripts:
                #         noscript.decompose()

                if header_footer == "no":
                    header_footer = "yes"
                    
                    
                    text_content = parsed_content.get_text()

                    cleaned_raw_text=process_raw_text(text_content)
                    
                    raw_text={
                            "link": link,
                            "content": cleaned_raw_text,
                        }
                    logging.info(f"Text from link {link} extracted")
                    c += 1

                    storing_response = db.store_web_page([raw_text], crawl_application_name, 
                                                        crawl_application_id,crawl_link)
                    if storing_response["status"]==0:
                        return storing_response
                    
                else:
                    header_tags = parsed_content.find_all('header')
                    for header_tag in header_tags:
                        header_tag.decompose()
                    
                    footer_tags = parsed_content.find_all('footer')
                    for footer_tag in footer_tags:
                        footer_tag.decompose()

                    title_tags = parsed_content.find_all('title')
                    for title_tag in title_tags:
                        title_tag.decompose()

                    
                    text_content = parsed_content.get_text()
                    cleaned_raw_text=process_raw_text(text_content)
                    
                    raw_text={
                            "link": link,
                            "content": cleaned_raw_text,
                        }
                    logging.info(f"Text from link {link} extracted")
                    c += 1

                    storing_response = db.store_web_page([raw_text], crawl_application_name, 
                                                        crawl_application_id,crawl_link)
                    if storing_response["status"]==0:
                        return storing_response
                    
            except TimeoutError:
                logging.error(f"Timeout error occurred for link: {link}")
                continue
            
            except Exception as e:
                logging.error(f"An error occurred for link: {link}: {str(e)}")
                continue
        
        logging.info(f"Total links:{Total_Links}, Total scraped links:{c}")  
        end_time = time.time()    

        total_time=process_tat(start_time, end_time)
        logging.info(f"Total time taken for embedding and storing:{total_time}")
        return 1, storing_response
        
    except Exception as e:
        logging.error(f"abc")
        logging.error(f"An error occurred while crawling raw text website: {str(e)}")
        return 0, str(e)