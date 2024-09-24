# from src.scrapers.web_scraper_bs import fetch_links, extract_contents
# from src.scrapers.web_scraper_selenium import selenium_fetch_links, extract_contents_selenium
# from src.data_processing.text_processing import process_text, text_splitter_lc
# from src.logger import logging
# import datetime
# from src import schema
# from fastapi import HTTPException,status,Depends
# from fastapi import Query,APIRouter
# # from src.oauth2 import get_current_user
# from src.logger import logging
# from src.config import DATABASE_TYPE,chroma_host, chroma_port

# from pymilvus import connections


# router=APIRouter(tags=["EXTRA"])


# if DATABASE_TYPE == 'chroma':
#     from src.database_types.chroma_db_database import ChromaDatabase as DatabaseImpl
#     db = DatabaseImpl(host=chroma_host, port=chroma_port)


# @router.post("/create_collections/")  #client.count_collections()
# async def list_coll():
#     try:
#         client=db.connect()
#         result=client.create_collection("new_collection")
#         return result
#     except Exception as e:
#         logging.info(f"An error occurred while listing_collection: {str(e)}")
#         return str(e)
    
# @router.post("/list_collections/")
# async def list_coll():
#     try:
#         client=db.connect()
#         result=client.list_collections()
#         return result
#     except Exception as e:
#         logging.info(f"An error occurred while listing_collection: {str(e)}")
#         return str(e)


# @router.post("/delete_collections/")
# async def delete_collection_name(cname:str):
#     try:
#         client=db.connect()
#         result=client.delete_collection(name=cname)  
#         return result

#     except Exception as e:
#         logging.info(f"An error occurred while deleting content: {str(e)}")
#         return str(e)

# # batch = collection.get(
# #         include=["metadatas", "documents", "embeddings"],
# #         limit=batch_size,
# #         offset=i)