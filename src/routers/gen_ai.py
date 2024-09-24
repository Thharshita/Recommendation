
from src.oauth2 import get_current_user
from fastapi import APIRouter, UploadFile,Depends
from src.logger import logger
from src.oauth2 import get_current_user
from src.pipeline.phi3_demo import get_phi3_response
from src.config import application_name, application_id, website_collection, chroma_paragraph_embedding_collection
from src.data_processing.store_complete_file_content import extract_and_store
from src.data_processing.store_complete_link_content import process_store_webpage
from src import schema
from src.scrapers.web_scraper_bs import check_link
from src.utils import get_database
router = APIRouter(tags=["Qna_summary_query"])


@router.post("/upload_file_select")
# , current_user_uuid:dict=Depends(get_current_user)
async def get_query_response(file: UploadFile, file_extension:str, element_id:str, category: str, number_of_question:int=3, query:str="What is this text about?", current_user_uuid:dict=Depends(get_current_user)):
    try:
        # if current_user_uuid["status"] == 0:
        #     return current_user_uuid
        file_name = file.filename
        logger.info("\n Reading File Bytes")
        file_bytes = await file.read()

        result= await extract_and_store(file_name,file_extension, file_bytes, application_name, application_id, element_id)
        # logger.info(f"result:{result}")
        logger.info(f'Tokens of corpus:{result["Word_tokens"]}')
        corpus= result["Document_text"]
        
        f_result=get_phi3_response(element_id, category, number_of_question, query, corpus)
        return f_result

    except Exception as e:
        logger.error(str(e))
        return  {"status":0, "message":"","body":str(e)}



@router.post("/generate_response_link/")
async def scrape_store_generate(crawl_content_id:str,element_id:str, category: str, number_of_question:int=3, query:str="What is this text about?", current_user_uuid:dict=Depends(get_current_user)):
    try:
        # if current_user_uuid["status"] == 0:
        #     return current_user_uuid
        logger.info("\n only extracting one link")
        link_status, links, use_selenium = await check_link(crawl_content_id)  #array of link
        if link_status==0:
            return links
        
        response=await process_store_webpage(links, use_selenium, application_name, application_id,crawl_content_id)
        logger.info(response)

        # return response
        
        db= get_database()
        client= db.connect()
        collection=client.get_or_create_collection(name=website_collection)
        data=collection.get(where={"sub_link": crawl_content_id})
        if data['ids']==[]:
            logger.error(f"No data found")
            return {"status":0,"message":"Data not exists","body":""}
        
        # logger.info(f'Tokens of corpus:{len(data["documents"].split(" "))}')
        corpus= data["documents"][0]
        
        
        f_result=get_phi3_response(element_id, category, number_of_question, query, corpus)
        return f_result
    except Exception as e:
        logger.info(f"An error occurred while scraping: {str(e)}")
        return {"status":0 , "message":"", "body":str(e)}


from src.data_processing.text_processing import generate_embedding, process_tat
from src.config import application_id, chroma_store_entire_page_collection
from src.utils import transform_data_pdf, transform_data
import time

# limit: int = 2, 
@router.post('/generate_answer_from_similar_content')
async def get_generated_answer(query: str, current_user_uuid:dict=Depends(get_current_user)):
    try:
        if current_user_uuid["status"] == 0:
            return current_user_uuid
        start_time = time.time()
        # if limit > 10 or limit < 1:
        #     return {"status_code": 0, "message": "Failure", "error": "Limit Value must be between 1 to 10"}
        
        db= get_database()
        limit=3
        result, match_index = await db.get_cosine_similarity(query, [0], application_id, limit,chroma_paragraph_embedding_collection )
        
        output=transform_data(result, match_index, "cosine")
        # logger.info(f"output:{output}")
        end_time = time.time()
        time_taken=process_tat(start_time, end_time)
        logger.info(f"Total time taken for searching:{time_taken}")
        output["tat"]=time_taken
        if output["message"]== '': #no similar content
            return output

        # logger.info(output["body"][0]["matching_content"])
        corpus=" "
        for i in range(len(output["body"])):
            corpus+=''.join((output["body"][i]["matching_content"]))

        # join_corpus= [output["body"][0]["matching_content"],output["body"][1]["matching_content"], output["body"][2]["matching_content"]]
        # corpus = ' '.join(join_corpus)
        # logger.info(f"corpus:{corpus}")
        logger.info(f'Number of tokens in corpus:{len(corpus.split(" "))}')

        
        f_result=get_phi3_response("searching", "query",0, query, corpus)
        return f_result
    except Exception as e:
        logger.info(f"An error occurred while scraping: {str(e)}")
        return {"status":0 , "message":"", "body":str(e)}


from src.data_processing.text_processing import generate_embedding, process_tat
from src.config import application_id, chroma_store_entire_page_collection
from src.utils import transform_data_pdf, transform_data
import time


#from chroma_store_entire_page collection, applied similarity in entire_page_data
@router.post('/generate_answer_similar_page')
async def get_generated_answer(query: str, current_user_uuid:dict=Depends(get_current_user)):
    try:
        if current_user_uuid["status"] == 0:
            return current_user_uuid
        start_time = time.time()
   
        
        db= get_database()
        limit=3
        result, match_index = await db.get_cosine_similarity(query, [0], application_id, limit, chroma_store_entire_page_collection)
        
        output=transform_data(result, match_index, "cosine")
        
        logger.info(f"output:{output}")
        sim_links=[]
        for i in range(len(output["body"])):
            logger.info(f'similar text {i} found in page:{output["body"][i]["internal_link"]}')
            sim_links.append(output["body"][i]["internal_link"])
     
        end_time = time.time()
        time_taken=process_tat(start_time, end_time)
        logger.info(f"Total time taken for searching:{time_taken}")
        output["tat"]=time_taken
        output["tat"]=time_taken
        if output["message"]== '': #no similar content
            return output
        
        logger.info(output["body"][0]["matching_content"])
        corpus=output["body"][0]["matching_content"]

        logger.info(f'Number of tokens in corpus:{len(corpus.split(" "))}')

        
        f_result=get_phi3_response("searching", "query",0, query, corpus)
        # f_result["similar_links"]=sim_links
        # f_result["selected_text"]=corpus
        return f_result
    except Exception as e:
        logger.error(str(e))
        return {"status_code": 0, "message": "", "body":str(e)}
  
    
#from chroma_embeddingcollection, applied similarity test on chks and tene 1st recieved page data to generate responsefrom model.
@router.post('/generate_answer_chunk_page')
async def get_generated_answer(query: str, current_user_uuid:dict=Depends(get_current_user)):
    try:
        if current_user_uuid["status"] == 0:
            return current_user_uuid
        start_time = time.time()
       
        db= get_database()
        limit=3
        result, match_index = await db.get_cosine_similarity(query, [0], application_id, limit, chroma_paragraph_embedding_collection)
        
        output=transform_data(result, match_index, "cosine")
        logger.info(f"output:{output}")
        end_time = time.time()
        time_taken=process_tat(start_time, end_time)
        
        logger.info(f"Total time taken for searching:{time_taken}")
        output["tat"]=time_taken
        output["tat"]=time_taken
        if output["message"] == '': #no similar content
            return output
        # logger.info(f"output after adding tat:{output}")
        logger.info(output["body"][0])
        logger.info("-------------------------------")
        logger.info(output["body"][0]["page_count"])
        
        for i in range(len(output["body"])):
            logger.info(f'similar text {i} found in page:{output["body"][i]["page_count"]}')

        # logger.info(f'Number of tokens in corpus:{len(corpus.split(" "))}')
        
        #getting 1st similar page

        page_number=output["body"][0]["page_count"] 
        content_id=output["body"][0]["element_id"]
        sub_link=output["body"][0]["internal_link"]
         

        client = db.connect()
        collection = client.get_or_create_collection(name=chroma_store_entire_page_collection)
        
        data=collection.get(where={"$and": [{"content_id": content_id}, {"sub_link":sub_link},{"page_number": page_number}]})
    
        logger.info(f'data:{data}')
        corpus= data['documents'][0]

        f_result=get_phi3_response("searching", "query",0, query, corpus)
        return f_result

    except Exception as e:
        logger.info(f"An error occurred while scraping: {str(e)}")
        return {"status":0 , "message":"", "body":str(e)}

  
    