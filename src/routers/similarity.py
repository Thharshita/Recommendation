from src.logger import logger
from fastapi import APIRouter, HTTPException, status
from fastapi import Depends
from src.data_processing.text_processing import generate_embedding, process_tat
# from src.database import collection_web_embedding
from src.config import DATABASE_TYPE, chroma_port, chroma_host, application_id
from src.utils import transform_data
import time
from src.oauth2 import get_current_user

if DATABASE_TYPE == 'chroma':
    from src.database_types.chroma_db_database import ChromaDatabase as DatabaseImpl
    db = DatabaseImpl(host=chroma_host, port=chroma_port)


router = APIRouter(tags=["File_Extraction"])

# ,current_user:dict=Depends(get_current_active_user)
@router.post('/search_ai_query_csn')
async def cosine_similar_text(query: str, limit: int = 2, current_user_uuid:dict=Depends(get_current_user)):
    try:
        if current_user_uuid["status"] == 0:
            return current_user_uuid
        start_time = time.time()
        if limit > 10 or limit < 1:
            return {"status_code": 0, "message": "Failure", "error": "Limit Value must be between 1 to 10"}

        # embedded_query = generate_embedding(query)
        # logger.info("Embedding of query is generated")
        result, match_index = await db.get_cosine_similarity(query, [0], application_id, limit)
        output=transform_data(result, match_index, "cosine")
        end_time = time.time()
        time_taken=process_tat(start_time, end_time)
        logger.info(f"Total time taken for searching:{time_taken}")
        output["tat"]=time_taken
        return output

    except Exception as e:
        logger.error(str(e))
        return {"status_code": 0, "message": "", "body":str(e)}
  
    
# @router.post('/search_ai_query_ecl')
# async def euclidean_similar_text(query: str, limit: int = 2 ):
#     try:
#         if limit > 10 or limit < 1:
#             return {"status_code": 0, "message": "Failure", "error": "Limit Value must be between 1 to 10"}

#         embedded_query = generate_embedding(query)
#         logger.info("Embedding of query is generated")
#         result =await db.get_cosine_similarity(query, embedded_query, application_id, limit)
#         return result

#     except Exception as e:
#         logger.error(str(e))
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
