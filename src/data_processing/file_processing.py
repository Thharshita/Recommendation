import fitz
from io import BytesIO
from src.logger import logger
from src.data_processing.text_processing import clean_file_data, clean_text_data
from src.logger import logger
from src.constant import SUPPORTED_FILE_TYPES
import os
from src.config import DATABASE_TYPE,chroma_host, chroma_port
from src.data_processing.text_processing import clean_file_data, clean_text_data, clean_pg_blocks, process_tat
from src.data_processing.similarity_chunking import get_similar_chunks
from src.utils import get_database
import time


async def get_pdf_content(file_bytes, text, file_name, file_extension, project_id, content_id, project_name):
    try:
        db= get_database()
        logger.info("inside get pdf content")
        pdf_file_obj = fitz.open(stream=BytesIO(file_bytes))
        # logger.info(len(pdf_file_obj))
        
        file_content = []
        paragraph_pg_num = []
        file_type = []

        result= db.check_project_content_document(project_id, content_id)
        if result["status"]==0:
            return 0, result, "."
        
        start_time= time.time()
        for page_num in range(len(pdf_file_obj)):
            page = pdf_file_obj.load_page(page_num)
            pg_text = page.get_text()
            # logger.info(f"\n { pg_text}")
            
            await db.save_page_content(pg_text, page_num,file_name, file_extension, project_id, content_id, project_name)
            # cleaned_paragraphs = clean_file_data(pg_text)
            # page_blocks= page.get_text("blocks")
            # logger.info(page_blocks)
            # cleaned_paragraphs= clean_pg_blocks(page_blocks)
            cleaned_paragraphs= get_similar_chunks(pg_text)
            total_paragraph = len(cleaned_paragraphs)
            file_content.extend(cleaned_paragraphs)   
            
            file_type.extend([file_name]*total_paragraph)
            paragraph_pg_num.extend([page_num+1]*(total_paragraph))
        
        pdf_file_obj.close()
        end_time = time.time()
        total_time=process_tat(start_time, end_time)
        clean_text = clean_text_data(text)
        if clean_text == 0:
            return 0, {"status":0, "message":".", "body":"Error while cleaning text"}, "."
        
        file_content.extend(clean_text)
        
        text_list = ['text'] * len(clean_text)
        file_type.extend(text_list)

        paragraph_pg_num.extend([0]*len(clean_text))

        if len(file_type) != len(paragraph_pg_num) != len(file_content):
            logger.error("Mismatch between file_type and paragraph_pg_num and file_content lengths")
            return 0,{"status":0,"message":0,"body":"Length mismatch error"},""
        logger.info("paragraph , file_type, paragraph_pg_num are extracted successfully")

        logger.info("File data and text are tokenized successfully")

        logger.info(f"Total time taken in storing entire page and chunking:{total_time}")
        return file_content, file_type, paragraph_pg_num
    
    except Exception as e:
        logger.error(f"Error occurred while extracting file content: {str(e).encode('utf-8')}")
        return 0,{"status":0,"message":0,"body":str(e)},"."
    

async def get_txt_content(file_bytes, text, file_name, file_extension, project_id, content_id, project_name) :
    try:
        db= get_database()
        logger.info("inside get txt content")
        file_content = []
        paragraph_pg_num = []
        file_type=[]
        start_time= time.time()
        pg_text = BytesIO(file_bytes).read().decode("utf-8")

        await db.save_page_content(pg_text, 0,file_name, file_extension, project_id, content_id, project_name)
        
        cleaned_paragraphs= get_similar_chunks(pg_text)
        total_paragraph = len(cleaned_paragraphs)
        file_content.extend(cleaned_paragraphs)

        file_type.extend([file_name]*total_paragraph)
        paragraph_pg_num.extend([0]*(total_paragraph))
        
        end_time = time.time()
        total_time=process_tat(start_time, end_time)
        
        clean_text = clean_text_data(text)
        if clean_text == 0:
            return 0,{"status":0, "message":"", "body":"Error while cleaning text"},"."
        
        file_content.extend(clean_text)
        
        text_list = ['text'] * len(clean_text)
        file_type.extend(text_list)

        paragraph_pg_num.extend([0]*len(clean_text))

        if len(file_type) != len(paragraph_pg_num) != len(file_content):
            logger.error("Mismatch between file_type and paragraph_pg_num and file_content lengths")
            return 0,{"status":0, "message":"", "body":"Length mismatch error"},"."
        logger.info("paragraph , file_type, paragraph_pg_num are extracted successfully")

        logger.info("File data and text are tokenized successfully")

        logger.info(f"Total time for embedding and storing:{total_time}")
        return file_content, file_type, paragraph_pg_num
    
    except Exception as e:
        logger.error(f"Error occurred while extracting file content: {str(e).encode('utf-8')}")
        return 0, {"status":0, "message":"", "body":str(e)}, "."
 
 
async def process_file_bytes(file_name, file_extension, file_bytes, project_name, project_id, content_id, text=""):
        db= get_database()

        logger.info("\n Inside process_file_bytes")
        calculated_filetype = file_name.split(".")[-1].lower()
        file_extension = file_extension.lower()
        
        if file_extension != calculated_filetype:
            logger.info(f"file_type :{calculated_filetype}, file_extension mentioned by user:{file_extension}")
            return {"status_code": 0, "message": "Failure", "error": "File type and extension do not match"}

        
        if calculated_filetype not in SUPPORTED_FILE_TYPES:
            return {"status_code": 0, "message": "Failure", 
                    "error": f"Unsupported file type. Only {SUPPORTED_FILE_TYPES} files are supported."}
        
        logger.info(f"file bytes :{type(file_bytes)}")
        
        file_size=len(file_bytes)
        logger.info(f"File size :{file_size}\n")

        if calculated_filetype == "txt":
            paragraphs_list, file_type_list, paragraph_pg_num = await get_txt_content(file_bytes, text, file_name, file_extension, 
                                            project_id, content_id, project_name)
        else:
            paragraphs_list, file_type_list, paragraph_pg_num = await get_pdf_content(file_bytes, text, file_name, file_extension,
                                             project_id, content_id, project_name)

        if paragraphs_list == 0:
            return file_type_list

        check_status =await db.insert_file_document(project_name, project_id, content_id, paragraphs_list, file_type_list, paragraph_pg_num)
        return check_status
        

def save_file_locally(file_name, file_bytes):
    try:
        os.makedirs("uploaded-files", exist_ok=True)
        file_path = os.path.join("uploaded-files", file_name)
        with open(file_path,"wb") as buffer:
            buffer.write(file_bytes)
        return file_path
    except Exception as e:
        logger.error(f"Unable to store file locally:{str(e).encode('utf-8')}")
        return 0
