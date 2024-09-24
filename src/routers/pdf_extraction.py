from fastapi import APIRouter, UploadFile, HTTPException, status
from src.logger import logger
from fastapi import Depends
from src.oauth2 import get_current_user
#from src.schema import Base64_string
from src.constant import SUPPORTED_FILE_TYPES
from src.data_processing.file_processing import process_file_bytes
from src.config import application_name, application_id

router = APIRouter(tags=["File_Extraction"])

# current_user_uuid:dict=Depends(get_current_active_user)
@router.post("/upload_file")
async def handle_file_upload(file: UploadFile, file_extension:str, element_id:str, text: str, current_user_uuid:dict=Depends(get_current_user)):
    try:
        if current_user_uuid["status"] == 0:
            return current_user_uuid
        file_name = file.filename
        logger.info("Reading File Bytes")
        file_bytes = await file.read()

        result= await process_file_bytes(file_name,file_extension, file_bytes, application_name, application_id, element_id, text)
        return result
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

# import base64
# @router.post("/upload_file_binary")
# async def handle_file_upload( data:Base64_string, current_user:dict=Depends(get_current_active_user)):
#     try:
#         file_bytes= base64.b64decode(data.base64_encoded_str) #original binary form
#         result= await process_file_bytes(data.file_name, data.file_extension, file_bytes, data.application_name, data.application_id, data.element_id, data.text)
#         return result
#     except Exception as e:
#         logger.error(str(e))
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
