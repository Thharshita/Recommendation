from fastapi import APIRouter, UploadFile, HTTPException, status
from src.logger import logger
from fastapi import Depends
from src.oauth2 import get_current_user
#from src.schema import Base64_string
from src.constant import SUPPORTED_FILE_TYPES
from src.data_processing.file_processing import process_file_bytes
from src.config import application_name, application_id, pdf_collection
from src.data_processing.store_complete_file_content import extract_and_store
from src.utils import get_password_hash, get_database

router = APIRouter(tags=["Store_Complete_pdf_data"])


@router.post("/store_pdf_content")
# , current_user_uuid:dict=Depends(get_current_user)
async def handle_file_upload(file: UploadFile, file_extension:str, element_id:str):
    try:
        # if current_user_uuid["status"] == 0:
        #     return current_user_uuid
        file_name = file.filename
        logger.info("\n Reading File Bytes")
        file_bytes = await file.read()

        result= await extract_and_store(file_name,file_extension, file_bytes, application_name, application_id, element_id)
        
        return result
    except Exception as e:
        logger.error(str(e))
        return  {"status":0, "message":"","body":str(e)}

@router.get("/get_all_file_data")
async def get_information():
    try: 
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
        collection=client.get_or_create_collection(name=pdf_collection)
        data=collection.get()
        logger.info(f"\n existing_file_data:{data}")
        if data==[]:
            logger.error(f"No data found")
            return {"message":"User not exists"}
        
        return {"status":1,"message": "FILE CONTENTS", "body": data}
    except Exception as e:
        logger.error("Exception occured while delting user %s", str(e))
        return {"status":0, "message":"","body":str(e)}

@router.post("/delete_file_content")
async def delete_item_by_metadata(content_id):
    try:
        # if current_user_uuid["status"] == 0:
        #     return current_user_uuid
        db=get_database()
        result=await db.delete_content(application_id, content_id, pdf_collection)
        return result    
    except Exception as e:
        logger.error(f"An error occurred while deleting the item: {str(e)}")
        return str(e)

