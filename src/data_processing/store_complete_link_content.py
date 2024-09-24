import requests
from bs4 import BeautifulSoup
from src.logger import logger
from src.data_processing.text_processing import process_raw_text
from src.scrapers.web_scraper_selenium_complete import extract_contents_selenium_c
from src.data_processing.text_processing import process_tat
from src.utils import get_database
import time

class Webpage_ingestion:
    def __init__(self):
         pass
    
    async def extract_contents(self,links, use_selenium,crawl_application_name, 
                crawl_application_id,crawl_link):
        try:
            if use_selenium=="YES":
                check_status, storing_response=await extract_contents_selenium_c(links, crawl_application_name, crawl_application_id,crawl_link)
                if check_status==1:
                    return storing_response
                else:
                    return 0, "Failed to extract contents using selenium"
                
            db=get_database()
            Total_Links=len(links)
            header_footer= "yes"
            c=0
            start_time=time.time()
            for link in links[0:72]:
                try:
                    response = requests.get(link, verify=None)
                    content = response.content
                
                    parsed_content = BeautifulSoup(content, 'html.parser')
                    
                    if header_footer == "no":
                        header_footer = "yes"
                        
                        text_content = parsed_content.get_text()
    
                        cleaned_raw_text=process_raw_text(text_content)
                        
                        raw_text={
                                "link": link,
                                "content": cleaned_raw_text,
                            }
        
                        logger.info(f"\n\nText from link {link} extracted")
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
                                "content": cleaned_raw_text}
                
                        logger.info(f"\n\nText from link {link} extracted")
                        c += 1
    
                        storing_response = db.store_web_page([raw_text], crawl_application_name, 
                                                        crawl_application_id,crawl_link)
                        if storing_response["status"]==0:
                              return storing_response

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
            return storing_response
            
        except Exception as e:
            logger.error(f"An error occurred while crawling raw text website: {str(e)}")
            return {"status":0 , "message":"Unable to process text", "body":str(e)}
    
                    
w= Webpage_ingestion() 

async def process_store_webpage(links, use_selenium, crawl_application_name, application_id,crawl_link):
    
    result= await w.extract_contents(links, use_selenium, crawl_application_name, 
                        application_id,crawl_link)
    return result
