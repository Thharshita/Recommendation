# from passlib.context import CryptContext
from src.logger import logger
from src.constant import SIMILARITY_RESPONSE
from src.config import DATABASE_TYPE,  chroma_host, chroma_port
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def transform_data(output,match_index,type):

    if match_index == []:
        return {"status":1, "message":"", "body":"No similar content was found. Please ensure you have entered correct query"}
    transformed_data = []
    for i in match_index:
        transformed_data.append({
            "score": output["distances"][0][i],
            "project_name": output["metadatas"][0][i]["project_name"],
            "project_id": output["metadatas"][0][i]["project_id"],
            "content_id": output["metadatas"][0][i]["content_id"],
            "sub_link": output["metadatas"][0][i]["sub_link"],  # Assuming a placeholder link for internal link
            "file_type": output["metadatas"][0][i]["file_type"],
            "similar_content": output["documents"][0][i],
            "page_number": output["metadatas"][0][i]["page_number"],
            "search_type": type
        })
    response=[{SIMILARITY_RESPONSE[k]:v for k,v in i.items() }for i in transformed_data]

    return {"status": 1, "message":"success", "body":response}



def transform_data_pdf(output,match_index,type):

    if match_index == []:
        return {"status":1, "message":"", "body":"No similar content was found"}
    transformed_data = []
    for i in match_index:
        transformed_data.append({
            "score": output["distances"][0][i],
            "project_name": output["metadatas"][0][i]["project_name"],
            "project_id": output["metadatas"][0][i]["project_id"],
            "content_id": output["metadatas"][0][i]["content_id"],
            "file_type": output["metadatas"][0][i]["file_type"],
            "similar_content": output["documents"][0][i],
            "search_type": type
        })
    response=[{SIMILARITY_RESPONSE[k]:v for k,v in i.items() }for i in transformed_data]
    logger.info(transformed_data)
    return {"status": 1, "message":"success", "body":response}

# Print the transformed data
# print(json.dumps(transformed_data, indent=2))
def get_database():
    try:
        if DATABASE_TYPE == 'chroma':
            from src.database_types.chroma_db_database import ChromaDatabase as DatabaseImpl
            db = DatabaseImpl(host=chroma_host, port=chroma_port)
            return db
    except Exception as e:
        logger.info(f"While connecting to server:{str(e)}")
        return {"status":0 , "message":"", "body":str(e)}


