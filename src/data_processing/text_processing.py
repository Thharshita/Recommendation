import re
import os
from src.logger import logger

from sklearn.feature_extraction.text import CountVectorizer
from sentence_transformers import SentenceTransformer
from src.config import Model_name
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer
from langchain_community.document_transformers import Html2TextTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter


model= SentenceTransformer(Model_name)
#model.save("all-MiniLM-L6-v2")
# model= SentenceTransformer(Model_name)
def generate_embedding(text:str):
    try:
        logger.info("Generating embedding")
        t = model.encode(text)     
        return t.tolist()  
    except Exception as e:
        logger.error(f"Embedding generation failed:{str(e)}")
        logger.error(str(e))

# async def get_tokenized_content(item):
#     try:
#         clean_data=[]
#         link_data=[]
#         embeddings=[]
#         paragraphs = re.split(r'\.\r\n',item["content"])
    

#         for para in paragraphs:
#             cleantext = re.sub(r'[^\w\s.]',' ', para)
#             cleantext = re.sub(r'\s+',' ', cleantext) 
#             cleantext = re.sub(r'\.{2,}', '.', cleantext)
            
#             while len(cleantext) > 60535:
#                 split_point = cleantext.rfind('.', 30000, 60535)
#                 if split_point == -1:  
#                     split_point = 60535
                
#                 chunk = cleantext[:split_point]
#                 clean_data.append(chunk)
#                 link_data.append(item["link"])
#                 embeddings.append(list(generate_embedding(chunk)))
#                 cleantext = cleantext[split_point:].strip()  # Remaining text

#             clean_data.append(cleantext)
#             link_data.append(item["link"])
#             embeddings.append(list(generate_embedding(cleantext)))
#         return clean_data, link_data, embeddings
    
#     except Exception as e:
#         logger.error(str(e).encode('utf-8'))
#         return 0


# 
def process_raw_text(text):
    try:
        logger.info('\n\n Cleaning raw text')
        raw_text = re.sub(r'\s+', ' ', text).strip()
        return raw_text
    except Exception as e:
        logger.error(f"An error occurred while processing raw text: {str(e)}")
        return 0
    
def clean_page_text(text):
    try:
        logger.info('Cleaning pg text')
        raw_text = re.sub(r'\s+', ' ', text).strip()
        # raw_text=re.sub(r'\', ' ', text).strip()
        return raw_text
    except Exception as e:
        logger.error(f"An error occurred while processing raw text: {str(e)}")
        return 0
# async def process_text(items):
#     try:
#         logger.info('Processing text')
#         paragraphs_list= []
#         link_list= []
#         embeddings_list=[]

#         for item in items: 
#             clean_data, link_data, embeddings=await get_tokenized_content(item)
#             if not clean_data:
#                 logger.info("Tokeniztion unsuccessful")

#             paragraphs_list.extend(clean_data)
#             link_list.extend(link_data)
#             embeddings_list.extend(embeddings)
        
#         if len(paragraphs_list)== len(link_list) == len(embeddings_list):
#             logger.info("Website data are tokenized and embedded successfully")
#             return paragraphs_list, link_list, embeddings_list
#         else:
#             return 0,0, "processing failed"
        
#     except Exception as e:
#         logger.error("An error occurred: %s", str(e))
#         return 0,0, "processing failed"

def process_text(items):
    try:
        logger.info('processing text')
        pattern = re.compile(r'\([^)]*\)')
        paragraph_list= []
        link_list= []
        embeddings_list=[]
        
        # logger.info(f"content0:{items[0]['content']}")
        # logger.info(f"link0:{items[0]['link']}")
        
        for i in range(len(items)):
            cleaned_page_content=pattern.sub('',items[i]['content'])
            splitted_text= text_splitter_lc(cleaned_page_content,400)

            for j in splitted_text:
                paragraph_list.append(j)
                link_list.append(items[i]['link'])
                # embeddings_list.append(list(generate_embedding(j)))
        

        if  len(paragraph_list)>=0 and len(link_list)>=0 and  len(paragraph_list) == len(link_list):
            logger.info("paragraph_list, link_list, embeddings_list obtained")
            return paragraph_list, link_list, embeddings_list 
        else:
            logger.error("Error while cleaning and splitting raw")
            return 0,0, "Error while cleaning and splitting raw"
        
    except Exception as e:
        logger.error("While processing and cleaning text: %s", str(e))
        return 0,0, str(e)
    

async def get_page_content(links):
    try:
        loader = AsyncChromiumLoader(links)
        docs =await loader.load()
        logger.info(docs)
        
        logger.info("links are processing, data are loaded")

        bs_transformer = BeautifulSoupTransformer()
        docs_transformed = bs_transformer.transform_documents(docs)
        logger.info("Web page content are fetched and transformed successfully using bs_transformer")
      
        html2text = Html2TextTransformer()
        docs_transformed = html2text.transform_documents(docs)
        logger.info("Web page content are fetched and transformed successfully using html2text")
       
        return 1,docs_transformed
    
    except Exception as e:
        logger.error(f"An error occurred while getting page content: {str(e)}")
        return 0, str(e)


def text_splitter_lc(cleaned_page_content, chunk_length):
    try:  
        logger.info('splitting_text')  
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_length,
            chunk_overlap=0,
            length_function=len,
            separators=['\n\n','\n','.']
            )
        splitted_text = splitter.split_text(cleaned_page_content)
        return splitted_text
    
    except Exception as e:
        logger.error(f"An error occurred while splitting text: {str(e)}")
        return 0, str(e)


async def process_raw_document(docs_transformed):
        try:
            pattern = re.compile(r'\([^)]*\)')
            paragraph_list=[]
            embeddings_list=[]
            link_list=[]

            for i in range(len(docs_transformed)):
                cleaned_page_content=pattern.sub('',docs_transformed[i].page_content)
                splitted_text= await text_splitter_lc(cleaned_page_content)

                for j in splitted_text:
                    paragraph_list.append(j)
                    link_list.append(docs_transformed[i].source)
                    embeddings_list.append(list(generate_embedding(j)))
        
            return paragraph_list, link_list, embeddings_list
        
        except Exception as e:
            logger.error(f"An error occurred while processing raw document: {str(e)}")
            return 0, str(e), ""
       
def clean_file_data(text):
    try:
        logger.info("breaking page data")
        paragraphs = re.split(r'\n \n|\n\n|\n\s\s+',text)
        cleaned_paragraphs = [re.sub(r'\s+|\"',' ', para.strip()) for para in paragraphs]
        cleaned_paragraphs = [re.sub(r'\.+|\n','', para) for para in cleaned_paragraphs]
        cleaned_paragraphs =  [para for para in cleaned_paragraphs if len(para)>5]
        return cleaned_paragraphs
    except Exception as e:
        logger.error(str(e).encode('utf-8'))
        return 0

def clean_pg_blocks(blocks):
    paragraphs=[]
    for i in range(len(blocks)):
        paragraphs.append(blocks[i][4])
    cleaned_paragraphs= [re.sub(r'\s+|\"',' ', para.strip())for para in paragraphs]
    cleaned_paragraphs = [re.sub(r'\.+|\n','', para) for para in cleaned_paragraphs]
    logger.info(f"Clened_block_pg:{cleaned_paragraphs}")
    return cleaned_paragraphs


def clean_text_data(text):
    try:
        logger.info("Cleaning text data")
        paragraphs = re.split(r'\\n \\n|\\n\\n|\\n\s\s+',text)
        cleaned_paragraphs = [re.sub(r'\s+|\"',' ', para.strip()) for para in paragraphs]
        cleaned_paragraphs = [re.sub(r'\.+|\n', '', para) for para in cleaned_paragraphs]
        cleaned_paragraphs = [para for para in cleaned_paragraphs if len(para)>5]
        return cleaned_paragraphs
    except Exception as e:
        logger.error(str(e).encode('utf-8'))
        return 0
    
def process_tat(start, end):
    tat=(end - start)
    return tat