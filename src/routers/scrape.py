from src.scrapers.web_scraper_bs import fetch_links, extract_contents
from src.logger import logger
from src import schema
from fastapi import Query,APIRouter, Depends
from src.logger import logger
from src.config import DATABASE_TYPE, chroma_host, chroma_port
from src.utils import get_database
from src.config import application_name, application_id, element_id
from src.oauth2 import get_current_user

router=APIRouter(tags=["SCRAPE"])
import validators

@router.post("/scrape_link/")
async def scrape_and_save_data(crawl: schema.Name_link,current_user_uuid:dict=Depends(get_current_user)):
    try:
        if not validators.url(crawl.element_id):
            return {"status":0, "message":"Invalid URL", "body":"Please add url in given format {https://moneyview.in/}"}

        if current_user_uuid["status"] == 0:
            return current_user_uuid
        db=get_database()

        link_status, links, use_selenium = await fetch_links(crawl.element_id)  #array of link
        if link_status==0:
            return links
        
        response= await extract_contents(links, use_selenium, application_name, application_id,crawl.element_id)
        return response
    
    except Exception as e:
        logger.info(f"An error occurred while scraping: {str(e)}")
        return {"status":0 , "message":"", "body":str(e)}
    

@router.post("/delete_item_by_metadata/")
async def delete_item_by_metadata(element_id, current_user_uuid:dict=Depends(get_current_user)):
    try:
        if current_user_uuid["status"] == 0:
            return current_user_uuid
        db=get_database()
        result=await db.delete_content(application_id, element_id)
        return result    
    except Exception as e:
        logger.error(f"An error occurred while deleting the item: {str(e)}")
        return str(e)

