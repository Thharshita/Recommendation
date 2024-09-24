import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from src.logger import logger
from src.data_processing.text_processing import process_raw_text, generate_embedding
from src.scrapers.web_scraper_selenium import selenium_fetch_links, extract_contents_selenium
from src.data_processing.text_processing import process_text, process_tat
from tenacity import retry, stop_after_attempt, wait_exponential
from src.constant import PROXY
from src.utils import get_database
import time

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))

async def fetch_links(url):
    try:
        logger.info("Fetching links")
        selenium="NO"
        
        response = requests.get(url,proxies=PROXY, 
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"},timeout=10)
        
        if response.status_code == 200:
            list_of_links=[url]
            soup = BeautifulSoup(response.content, 'html.parser')
            # logger.info("soup: {}".format(soup))
            
            links = soup.find_all('a', href=True)
            # logger.info(f"links:{links}")
            extracted_links = [urljoin(url, link['href']) for link in links if is_valid_link(url, link['href'])]
            
            if "https://www.enable-javascript.com/" in extracted_links or extracted_links==[]:
                logger.info("Passing to selenium for link extraction")
                selenium='YES'

                link_status, list_links= await selenium_fetch_links(url)
                if link_status==1:
                    logger.info("Its a success")
                    return 1, list_links, selenium
                
                else:return 0, {"status":0, "message":"", "body":list_links},"."

            list_of_links.extend(extracted_links)
            list_of_links=set(list_of_links)
            final_list_of_links=list(list_of_links)
            logger.info(f"extracted_links:{final_list_of_links}")
            logger.info(f"extracted_links lenght:{len(final_list_of_links)}")
           
            return 1, final_list_of_links, selenium

    except Exception as e:
        logger.error(f"Error while fetching link{url}: {str(e)}")
        logger.info("Trying Selenium after failing BeautifulSoup")
        
        selenium='YES'
        link_status, list_links= await selenium_fetch_links(url)
        if link_status==1:
                return 1, list_links, selenium
        else:return 0, {"status":0, "message":"", "body":list_links},"."

async def check_link(url):
    try:
        logger.info("Checking links")
        selenium="NO"
        
        response = requests.get(url,proxies=PROXY, 
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"},timeout=10)
        
        if response.status_code == 200:
            list_of_links=[url]
            soup = BeautifulSoup(response.content, 'html.parser')
            # logger.info("soup: {}".format(soup))
            
            links = soup.find_all('a', href=True)
            # logger.info(f"links:{links}")
            extracted_links = [urljoin(url, link['href']) for link in links if is_valid_link(url, link['href'])]
            
            if "https://www.enable-javascript.com/" in extracted_links or extracted_links==[]:
                logger.info("Passing to selenium for link extraction")
                selenium='YES'
                return 1, list_of_links, selenium
                
           
            return 1, list_of_links, selenium

    except Exception as e:
        logger.error(f"Error while fetching link{url}: {str(e)}")
        logger.info("Trying Selenium after failing BeautifulSoup")
        
        selenium='YES'
        return 1, list_of_links, selenium


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


async def extract_contents(links, use_selenium,crawl_application_name, 
            crawl_application_id,crawl_link):
    try:
        logger.info("Inside extract content")
        logger.info("Links: {}".format(links))
        logger.info("use_selenium: {}".format(use_selenium))
        if use_selenium=="YES":
            insertion_response=await extract_contents_selenium(links, crawl_application_name, crawl_application_id,crawl_link)
            return insertion_response
            
        db=get_database()
        Total_Links=len(links)
        header_footer= "yes"
        c=0
        start_time=time.time()

        for link in links[0:72]:
            try:
                response = requests.get(link)
                content = response.content
            
                parsed_content = BeautifulSoup(content, 'html.parser')
                
                if header_footer == "no":
                    header_footer = "yes"
                    
                    text_content = parsed_content.get_text()

                    cleaned_raw_text=process_raw_text(text_content)
                    if cleaned_raw_text==0:
                        return {"status":0 , "message":"Unable to clean text", "body":cleaned_raw_text}

                    
                    raw_text={
                            "link": link,
                            "content": cleaned_raw_text,
                            # "corpus_embedding":generate_embedding(cleaned_raw_text)
                        }
    
                    logger.info(f"Text from link {link} extracted")
                    c += 1

                    storing_response = db.store_raw_corpus([raw_text], crawl_application_name, 
                                                    crawl_application_id,crawl_link)
                    if storing_response["status"]==0:
                          return storing_response

                    paragraphs_list, link_list, embeddings_list = process_text([raw_text])
                    if paragraphs_list==0:
                        return {"status":0 , "message":"Unable to process text", "body":embeddings_list}
                    
                    insert_response=db.insert_paragraph_embeddings(paragraphs_list, link_list, embeddings_list,
                                                            crawl_application_name, crawl_application_id,crawl_link)
                    if insert_response["status"]==0:
                        return insert_response

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
                    if cleaned_raw_text==0:
                        return {"status":0 , "message":"Unable to clean text", "body":cleaned_raw_text}
                    
                    raw_text={
                            "link": link,
                            "content": cleaned_raw_text}
                            # "corpus_embedding":generate_embedding(cleaned_raw_text)}

                    logger.info(f"Text from link {link} extracted")
                    c += 1

                    storing_response = db.store_raw_corpus([raw_text], crawl_application_name, 
                                                    crawl_application_id,crawl_link)
                    if storing_response["status"]==0:
                          return storing_response

                    paragraphs_list, link_list, embeddings_list = process_text([raw_text])
                    if paragraphs_list==0:
                        return {"status":0 , "message":"Unable to process text", "body":embeddings_list}
                    
                    insert_response=db.insert_paragraph_embeddings(paragraphs_list, link_list, embeddings_list,
                                                            crawl_application_name, crawl_application_id,crawl_link)
                    if insert_response["status"]==0:
                        return insert_response  #{"status":1, "message": "Pragraph and embedding stored in database","body":""}

            except TimeoutError:
                logger.error(f"Timeout error occurred for link: {link}")
                continue
            
            except Exception as e:
                logger.error(f"An error occurred for link: {link}: {str(e)}")
                continue
            
        logger.info(f"Total links:{Total_Links}, Total scraped links:{c}")  
        end_time = time.time()

        total_time=process_tat(start_time, end_time)
        logger.info(f"Total time taken for embedding and storing:{total_time}")
        return insert_response
        
    except Exception as e:
        logger.error(f"An error occurred while crawling raw text website: {str(e)}")
        return {"status":0 , "message":"Unable to process text", "body":str(e)}


