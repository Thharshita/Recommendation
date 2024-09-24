import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from src.logger import logging
from langchain_community.document_loaders import WebBaseLoader
from src.data_processing.text_processing import get_page_content, process_raw_document


def fetch_links(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            list_of_links=[url]
            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.find_all('a', href=True)
            extracted_links = [urljoin(url, link['href']) for link in links if is_valid_link(url, link['href'])]
            extracted_links=set(extracted_links)
            extracted_links=list(extracted_links)
            list_of_links.extend(extracted_links)
            list_of_links=set(list_of_links)
            list_of_links=list(list_of_links)
            logging.info(f"extracted_links:{list_of_links}")
            logging.info("All web_links are stored successfully")
            if list_of_links==[]:
                return 0,{"status":0, "message": "empty list of web_links"}
            return 1, list_of_links
        else:
            logging.info(f"Failed to fetch URL: {url}. Status code: {response.status_code}")
            return 0, f"Failed to fetch URL: {url}. Status code: {response.status_code}"
    except Exception as e:
        logging.info((f"An error occurred: {str(e)}"))
        return 0, str(e)


def is_valid_link(base_url, link):
    if link.startswith('#') or link.startswith('javascript:') or link.startswith('mailto:') or link.startswith("tel:"):
        return False
    if 'maps.app.goo.gl' in link:  
        return False
    if 'google.com/maps' in link:   
        return False
    if any(domain in link for domain in ['linkedin.com','.zip', '.jpg','twitter.com', 'facebook.com', 'youtube.com','play.google.com','instagram.com','dlai.in']): 
        return False
    if not link.startswith('http'): 
        link = urljoin(base_url, link)
    return True


async def extract_texts_and_embeddings(links):
    try:
        check_status,docs_transformed = await get_page_content(links)
        if check_status ==0:
            return 0, docs_transformed, ''
        
        paragraph_list, link_list, embeddings_list = await process_raw_document(docs_transformed)
        if paragraph_list == 0:
            return 0, link_list,'' 
        
        return paragraph_list, link_list, embeddings_list
 
    except Exception as e:
        logging.error(f"An error occurred while crawling raw text website: {str(e)}")
        return 0, str(e),''
