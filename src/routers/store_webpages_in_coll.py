from src.scrapers.web_scraper_bs import fetch_links, extract_contents, check_link
from src.logger import logger
from src import schema
from fastapi import Query,APIRouter, Depends
from src.logger import logger
from src.config import application_name, application_id, website_collection
from src.data_processing.store_complete_link_content import process_store_webpage
from src.utils import get_password_hash, get_database


router=APIRouter(tags=["Store_Complete_Webpage"])
# , current_user_uuid:dict=Depends(get_current_user)

@router.post("/scrape_only_one_link/")
async def scrape_and_store_one_link(crawl: schema.Name_link):
    try:
        # if current_user_uuid["status"] == 0:
        #     return current_user_uuid
        logger.info("\n only extracting one link")
        link_status, links, use_selenium = await check_link(crawl.content_id)  #array of link
        if link_status==0:
            return links
        
        response=await process_store_webpage(links, use_selenium, application_name, application_id,crawl.content_id)
        logger.info(response)

        # return response
        
        db= get_database()
        client= db.connect()
        collection=client.get_or_create_collection(name=website_collection)
        data=collection.get(where={"sub_link": crawl.content_id})
        if data['ids']==[]:
            logger.error(f"No data found")
            return {"status":0,"message":"Data not exists","body":""}
        
        return {"status":1,"message": "", "body": data["documents"]}
        
    
    except Exception as e:
        logger.info(f"An error occurred while scraping: {str(e)}")
        return {"status":0 , "message":"", "body":str(e)}
    
@router.post("/scrape_and_store_webpage/")
async def scrape_and_store_webpages(crawl: schema.Name_link):
    try:
        # if current_user_uuid["status"] == 0:
        #     return current_user_uuid
        link_status, links, use_selenium = await fetch_links(crawl.content_id)  #array of link
        if link_status==0:
            return links
        
        response=await process_store_webpage(links, use_selenium, application_name, application_id,crawl.content_id)
        return response
    
    except Exception as e:
        logger.info(f"An error occurred while scraping: {str(e)}")
        return {"status":0 , "message":"", "body":str(e)}
    
@router.get("/get_link_data")
async def get_information(link:str):
    try: 
        logger.info("\n get-link-data running")
        db= get_database()
        client= db.connect()         
        # collection=client.get_or_create_collection(name=pdf_collection)
        # existing_admin=collection.get(where={"email":admin_username})
        # logger.info(f"Existing_admin:{existing_admin}")
        # if existing_admin['ids']==[]:
        #     logger.error("Unauthorized admin ")
        #     return {"Admin not valid"}
        #     # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
        #     #                     detail=f"ADMIN NOT VALID")
        collection=client.get_or_create_collection(name=website_collection)
        data=collection.get(where={"sub_link": link})
        # logger.info(f"\n existing_file_data:{data}")
        if data['ids']==[]:
            logger.error(f"No data found")
            return {"status":0,"message":"Data not exists","body":""}
        
        return {"status":1,"message": "", "body": data}
    except Exception as e:
        logger.error("Exception occured while delting user %s", str(e))
        return {"status":0, "message":"","body":str(e)}

# , current_user_uuid:dict=Depends(get_current_user)
@router.post("/delete_webpage")
async def delete_item_by_metadata(internal_link):
    try:
        # if current_user_uuid["status"] == 0:
        #     return current_user_uuid
        db=get_database()
        client=db.connect()
            
        collection = client.get_collection(name=website_collection)
        available_linkdata=collection.get(where={"sub_link":internal_link})
        if available_linkdata['ids']==[]:
            return {"status":0, "message":"contentid not founds" ,"body":""}
        logger.info("Deleting")

        result=collection.delete(where=
            {
            "sub_link": {
                "$eq": internal_link}
            }
        )
        logger.info(f"delte:{result}")
        
        return {"status": 1, "message": "Content deleted successfuly", "body":result} 
    except Exception as e:
        logger.error(f"An error occurred while deleting the item: {str(e)}")
        return str(e)
    
@router.post("/delete_website")
async def delete_item_by_metadata(element_id):
    try:
        # if current_user_uuid["status"] == 0:
        #     return current_user_uuid
        db=get_database()
        client=db.connect()
            
        collection = client.get_collection(name=website_collection)
        logger.info("Deleting")

        available_content= collection.get(where={"content_id":element_id})
        if available_content['ids']==[]:
            return {"status":0, "message":"contentid not found" ,"body":""}

        result=collection.delete(where=
            {
            "content_id": {
                "$eq": element_id }
            }
        )
        logger.info(f"delte:{result}")
        
        return {"status": 1, "message": "Content deleted successfuly", "body":result} 
    except Exception as e:
        logger.error(f"An error occurred while deleting the item: {str(e)}")
        return str(e)
    
   
@router.get("/show_all_data")
async def show_all_data():
    try: 
        logger.info("\n show all data running")
        db= get_database()
        client= db.connect()         
        # collection=client.get_or_create_collection(name=pdf_collection)
        # existing_admin=collection.get(where={"email":admin_username})
        # logger.info(f"Existing_admin:{existing_admin}")
        # if existing_admin['ids']==[]:
        #     logger.error("Unauthorized admin ")
        #     return {"Admin not valid"}
        #     # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
        #     #                     detail=f"ADMIN NOT VALID")
        collection=client.get_or_create_collection(name=website_collection)
        data=collection.get()
        # logger.info(f"\n existing_file_data:{data}")
        if data['ids']==[]:
            logger.error(f"No data found")
            return {"status":0,"message":"Data not exists","body":""}
        
        return {"status":1,"message": "", "body": data}
    except Exception as e:
        logger.error("Exception occured while delting user %s", str(e))
        return {"status":0, "message":"","body":str(e)}

