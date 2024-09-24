import fitz
from io import BytesIO
from src.logger import logger
from src.data_processing.text_processing import clean_file_data, clean_text_data
from src.data_processing.text_processing import clean_page_text
from src.logger import logger
from src.constant import SUPPORTED_FILE_TYPES
import os
from src.config import DATABASE_TYPE,chroma_host, chroma_port
from src.data_processing.text_processing import clean_file_data, clean_text_data, clean_pg_blocks, process_tat
from src.data_processing.similarity_chunking import get_similar_chunks
from src.utils import get_database
import time


class Pdf_ingestion:
    def __init__(self):
         pass
    
    async def store_pdf_content(self, file_bytes, file_name, file_extension,
                                project_id, content_id, project_name):
        try:
            db= get_database()
            pdf_file_obj = fitz.open(stream=BytesIO(file_bytes))
            logger.info(len(pdf_file_obj))

            check_db= db.check_file_data_exist(project_id, content_id)
            if check_db["status"]==0:
                return check_db
            
            corpus=[]
            start_time= time.time()
            
            for page_num in range(len(pdf_file_obj)):
                page = pdf_file_obj.load_page(page_num)
                pg_text = page.get_text()
                clean_pg_text = clean_page_text(pg_text)
                # logger.info(f"\n { clean_pg_text}")
                corpus.append(clean_pg_text)

            full_text= " ".join(corpus)
            word_count= full_text.split(" ")
            # logger.info(f"wod_Count: {word_count}")
            total_word_Count= len(word_count)


            result=db.save_complete_pdf(file_name, file_extension,
                                project_id, content_id, project_name, full_text)
            if result["status"]==0:
                return result
            
            end_time = time.time()
            total_time=process_tat(start_time, end_time)
            logger.info(f"Total time taken for storing:{total_time}")
            
            return {"status_code": 1, "message": result["message"], "Document_text": full_text, "Word_tokens":total_word_Count}
        except Exception as e:
            logger.error(f"Error occurred while extracting file content: {str(e)}")
            return {"status_code": 0, "message": ".", "body":str(e) }
        
    async def store_txt_content(self,file_bytes, file_name, file_extension, project_id, content_id, project_name):
        try:
            db= get_database()
            logger.info("inside store txt content")
    
            start_time= time.time()
            pg_text = BytesIO(file_bytes).read().decode("utf-8")
    
            result=db.save_complete_pdf(file_name, file_extension,
                                project_id, content_id, project_name, pg_text)
            if result['status']==0:
                return result
            
            end_time = time.time()
            total_time=process_tat(start_time, end_time)

            logger.info(f"Total time taken for storing:{total_time}")
            return result
        
        except Exception as e:
            logger.error(f"Error occurred while extracting file content: {str(e).encode('utf-8')}")
            return {"staus":0, "message":"", "body":str(e)}


    async def process_file_bytes(self,file_name, file_extension, file_bytes, project_name, project_id, content_id):
            logger.info("\n Inside process_file_bytes")
            
            calculated_filetype = file_name.split(".")[-1].lower()
            file_extension = file_extension.lower()
            
            if file_extension != calculated_filetype:
                logger.info(f"file_type :{calculated_filetype}, file_extension mentioned by user:{file_extension}")
                return {"status_code": 0, "message": "Failure", "error": "File type and extension do not match"}
            logger.info("file_extension: %s", file_extension)
            
            if calculated_filetype not in SUPPORTED_FILE_TYPES:
                return {"status_code": 0, "message": "Failure", 
                        "error": f"Unsupported file type. Only {SUPPORTED_FILE_TYPES} files are supported."}
                    
            file_size=len(file_bytes)
            logger.info(f"File size :{file_size}\n")
    
            if calculated_filetype == "txt":
                result= await self.store_txt_content(file_bytes, file_name, file_extension, 
                                                project_id, content_id, project_name)
                return result
            else:
                result= await self.store_pdf_content(file_bytes, file_name, file_extension,
                                                 project_id, content_id, project_name)
                return result
                    
p= Pdf_ingestion()           
async def extract_and_store(file_name,file_extension, file_bytes, application_name, application_id, element_id):
    result=await p.process_file_bytes(file_name, file_extension, file_bytes, application_name, application_id, element_id)
    return result