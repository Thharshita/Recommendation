import chromadb
from src.logger import logger
from src.database_types.general_database import Database
import uuid
import datetime
from src.config import website_collection,pdf_collection,euclidean_threshold, chroma_paragraph_embedding_collection, chroma_store_entire_page_collection
from chromadb.config import Settings
from fastapi import HTTPException,status,Depends
from src.data_processing.text_processing import process_text, text_splitter_lc, process_tat
from src.config import DATABASE_TYPE,chroma_host, chroma_port, server_path



class ChromaDatabase(Database):
    def __init__(self, host, port):
        self.host = host
        self.port = port
       
    
    def connect(self):
        try:
            client = chromadb.PersistentClient(path=server_path, settings=Settings(anonymized_telemetry=False))
            # client = chromadb.HttpClient(host=self.host, port=self.port,settings=Settings(anonymized_telemetry=False))
            return client
        except Exception as e:
            logger.error(f"Error while connecting to db: {str(e)}")


    def insert(self, collection_name, data):
        try:
            client=self.connect()
            collection = client.get_or_create_collection(name=collection_name)
            result=collection.add(**data) 
            # logger.info(f"insertion_result:{result}")
            return result
        except Exception as e:
            logger.error(f"Error while inserting data: {str(e)}")


    async def query(self):
        pass


    def delete(self, collection_name, data):
        try:
            client=self.connect()
            collection = client.get_or_create_collection(name=collection_name)
            result=collection.delete(**data) 
            return result
        except Exception as e:
            logger.error(f"Error while deleting data: {str(e)}")


    async def close(self):
        pass


    async def search(self,collection_name, data):
        try:
            client=self.connect()
            collection = client.get_or_create_collection(name=collection_name)
            result= collection.query(**data )
            return result
        except Exception as e:
            logger.error(f"Error while searching data: {str(e)}")


    def check_and_delete_project_id(self,project_id, sub_link):
        try:
            client=self.connect()
            logger.info(f"Checking whether project_id and main_link exist in embedding collection")
            collection = client.get_or_create_collection(name=chroma_paragraph_embedding_collection)
            result= collection.get(where={"$and": [{"project_id": project_id}, {"sub_link":sub_link}]})
            
            data={'where':{"$and": [{"project_id": project_id}, {"sub_link":sub_link}]}}
            
            if result['ids']==[]:
                logger.info("No data with similar project_id and content_id in embedding collection")
                

            else:
                logger.info(f"Document found with same project_id and main_link in embedding collection")
                res = self.delete(chroma_paragraph_embedding_collection,data)
                logger.info(f"res_deleted :{res}")
                
           
            logger.info(f"Checking whether project_id and main_link exist in RAW corpuss collection")    
            collection= client.get_or_create_collection(name=chroma_store_entire_page_collection)
            result= collection.get(where={"$and": [{"project_id": project_id}, {"sub_link":sub_link}]})
            
            if result['ids']==[]:
                logger.info("No data with similar project_id and content_id in RAW Corpus collection")
                
            else:
                logger.info(f"Document found with same project_id and content_id")
                res = self.delete(chroma_store_entire_page_collection, data)
                logger.info(f"res_deleted:{res}")
            
            return {"status":1, "message": "", "body":""}
        except Exception as e:
            logger.error(f"Error while deleting data: {str(e)}")
            return {"status":0, "message":f"Error occurred while deleting project id: {str(e)}"}
        
        

    def store_raw_corpus(self, raw_text, crawl_application_name, crawl_application_id,crawl_link):
        try:
            result=self.check_and_delete_project_id(crawl_application_id, raw_text[0]["link"])
            if result["status"] == 0:
                    return result
            client=self.connect()
   
            documents = []
            metadatas=[]
            ids=[]

            for i in range (len(raw_text)):
                logger.info(f"storing raw corpus of link:{raw_text[i]['link']}")
                documents.append(raw_text[i]["content"])
                metadatas.append({"project_name":crawl_application_name, "project_id":crawl_application_id, "content_id": crawl_link,
                "sub_link":raw_text[i]["link"], "file_type": "website","page_number":i, 
                "created_at":datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")})
                ids.append(str(uuid.uuid4()))

        
            insert_data ={
                "documents": documents,
                "metadatas":metadatas,
                "ids":ids
            }
        
            insert_result=self.insert(chroma_store_entire_page_collection, insert_data)
            logger.info(f"Insert store raw corpus result: %s" %insert_result)
            
            # if result.inserted_id is None:
            #     logger.error("RAW corpus Pragraph not stored in database")
            #     return {"status":0 , "message":"unable to insert RAW paragraph to database"}
            # else:
            #     logger.info("RAW corpus Pragraph stored in database")

            return {"status":1, "message": "","body":""}

    
        except Exception as e:
            logger.error(f"Error while inserting data in store_raw_corpus: {str(e)}")
            return {"status":0, "message":"", "body":f"Error occurred while storing raw corpus: {str(e)}"}

 
                                
    async def save_page_content(self,pg_text,page_num,file_name, file_extension, project_id, content_id, project_name):
        try:
            client=self.connect()
            # logger.info("Saving page content")
            
            insert_data= {
                "metadatas":[{"project_name":project_name, "project_id":project_id, "content_id":content_id, "sub_link":"", 
                        "file_type":file_name, "page_number":page_num, "created_at": datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}],
                "documents":[pg_text],
                "ids":[str(uuid.uuid4())]
                }
        
            result=self.insert(chroma_store_entire_page_collection, insert_data)
    

            # if result.inserted_id is None:
            #     logger.error("RAW corpus Pragraph not stored in database")
            #     return {"status":0 , "message":"unable to insert paragraph to database"}
            # else:
            #     logger.info("RAW corpus Pragraph stored in database")

            return {"status":1, "message": "Data stored successfully"}
        
        except Exception as e:
            logger.error(f"Error while inserting data: {str(e)}")
            return {"status":0, "message": "", "body":""}
     
        
    def insert_paragraph_embeddings(self,paragraphs_list, link_list, embeddings_list,
                            crawl_application_name, crawl_project_id,crawl_link):
        try:
            client=self.connect()
            metadatas =[]
            ids=[]

            for i in range(len(paragraphs_list)):
                metadatas.append({"project_name":crawl_application_name, "project_id":crawl_project_id, "content_id": crawl_link,
                "sub_link":link_list[i], "file_type": "website","page_number":0, 
                "created_at":datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")})
                ids.append(str(uuid.uuid4()))


            insert_data ={
                "documents":paragraphs_list ,
                "metadatas":metadatas,
                "ids":ids
            }
            logger.info("inserting chunked paragraphs")

            insert_result=self.insert(chroma_paragraph_embedding_collection, insert_data)
            logger.info(f"Insert_result: {insert_result}")

            # if insert_response.inserted_id is None:
            #         logger.error("Pragraph and embedding not stored in database")
            #         return {"status":0 , "message":"unable to insert paragraph and embedding to database","body":""}
            
            logger.info("Pragraph and embedding storing in collection embedding database")

            return {"status":1, "message": "Pragraph and embedding stored in database","body":""}

        except Exception as e:
            logger.error(f"Error while inserting data: {str(e)}")
            return {"status":0, "message": "","body":str(e)}
        

    async def insert_file_document(self, project_name, project_id, content_id, content, file_type, paragraph_pg_num):
        try:
            import time
            logger.info("About to insert paragraph and embedding")
            start_time = time.time()
           
            metadatas =[]
            ids=[]

            for i in range(len(content)):
                metadatas.append({"project_name":project_name, "project_id":project_id, "content_id":content_id, "sub_link":"", 
                "file_type":file_type[i], "page_number":paragraph_pg_num[i], "created_at":datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")})

                ids.append(str(uuid.uuid4()))

            insert_data ={
                "documents": content,
                "metadatas":metadatas,
                "ids":ids
            }

            client=self.connect()
            insert_response=self.insert(chroma_paragraph_embedding_collection, insert_data)
            logger.info("Insert_result: %s", insert_response)


            # if insert_response.inserted_id is None:
            #     logger.error("Pragraph and embedding not stored in database")
            #     message={"status":0 , "message":"unable to insert paragraph and embedding to database"}
            # else: 
            #     message="Pragraph and embedding stored in database"
            #     logger.info("Pragraph and embedding stored in database")
            logger.info("Pragraph and embedding stored in database")
            end_time = time.time()
            time_taken=process_tat(start_time, end_time)
            logger.info(f"time_taken to insert file in embedding collection:{time_taken}")          
            return {"status":1, "message": "Pragraph and embedding stored in database","body":""}
        
        except Exception as e:
            logger.error(f"Error while inserting data: {str(e)}")
            return {"status":0,"message":"","body":str(e)}

    
    async def get_cosine_similarity(self,query, embedded_query, web_id, limit,search_collection=chroma_paragraph_embedding_collection): 
        try:
            logger.info("Getting cosine similarity")
            client=self.connect()

            logger.info("Get_cosine_similarity")
            data= {
                "query_texts": query,
                "n_results": limit,
                "where":{"project_id":web_id}
            }

            result=await self.search(search_collection, data)
            # logger.info(f"search result:{result}")
            match_index= await self.threshold_search(result)
            
            return result, match_index
        
        except Exception as e:
            logger.error(str(e))
            return {"status_code":0,"message":"Failure","error":str(e)}, " ."
    
    async def threshold_search(self, result):
        try:
#search result:{'ids': [['d52883c3-90ae-4941-a47f-197885da7eb5', '2da37e53-fec3-42d9-ae8c-196aeb90f06e', '5a986a26-4781-4e2d-9f3d-8f289e98fb00', 'ea4d1570-5d85-4833-b15b-1e03b0b9b435', '2b6e7855-df17-45a5-a87a-febd07ff6d0e']], 'distances': [[1.6360032558441162, 1.6487722396850586, 1.665622591972351, 1.6851296424865723, 1.701249122619629]], 'metadatas': [[{'content_id': 'fastag issuance', 'created_at': '2024-08-20-17-55-51', 'file_type': 'FASTag Issuance to Customers.pdf', 'page_number': 3, 'project_id': 'kms@123', 'project_name': 'Kms', 'sub_link': ''}, {'content_id': 'fastag issuance', 'created_at': '2024-08-20-17-55-51', 'file_type': 'FASTag Issuance to Customers.pdf', 'page_number': 5, 'project_id': 'kms@123', 'project_name': 'Kms', 'sub_link': ''}, {'content_id': 'fastag issuance', 'created_at': '2024-08-20-17-55-51', 'file_type': 'FASTag Issuance to Customers.pdf', 'page_number': 5, 'project_id': 'kms@123', 'project_name': 'Kms', 'sub_link': ''}, {'content_id': 'fastag issuance', 'created_at': '2024-08-20-17-55-51', 'file_type': 'FASTag Issuance to Customers.pdf', 'page_number': 4, 'project_id': 'kms@123', 'project_name': 'Kms', 'sub_link': ''}, {'content_id': 'fastag issuance', 'created_at': '2024-08-20-17-55-51', 'file_type': 'FASTag Issuance to Customers.pdf', 'page_number': 2, 'project_id': 'kms@123', 'project_name': 'Kms', 'sub_link': ''}]], 'embeddings': None, 'documents': [['3', '14.', '15.', '4', '3.']], 'uris': None, 'data': None, 'included': ['metadatas', 'documents', 'distances']}
            match_index=[]
            for i in range(len(result['distances'][0])):
                if result['distances'][0][i]<float(euclidean_threshold):
                    match_index.append(i)
            # logger.info(f'match_index: {match_index}')
            return match_index

        except Exception as e:
            logger.error(f"Error while threshold_search: {str(e)}")
            return {"status_code":0,"message":"Failure","error":str(e)}
    
    async def delete_content(self, project_id, content_id, col_name=chroma_paragraph_embedding_collection):
        try:
            client=self.connect()
            
            collection = client.get_collection(name=col_name)
            logger.info(f"collection :{collection}")

            find_content=collection.get(where={"content_id":content_id})
            logger.info(f"find_content: {find_content}")
            if find_content['ids']==[]:
                return {"status": 1, "message": "Content id not found", "body":""}

            logger.info("Deleting")
            result=collection.delete(where={"$and": [
            {
            "project_id": {
                "$eq": project_id}
            },
            {
            "content_id": {
                "$eq": content_id }
            }
            ]
            }
) 
            logger.info(f"delte:{result}")
            
            return {"status": 1, "message": "Content deleted successfuly", "body":result}
            
        except Exception as e:
            logger.error(f"Error while deletng content: {str(e)}")
            return {status:0, "message":"", "body":str(e)}

    def check_project_content_document(self,project_id, content_id):
        try:
            logger.info(f"Checking whether project_id and content_id exist in embedding collection")
            client=self.connect()
            collection = client.get_or_create_collection(name=chroma_paragraph_embedding_collection)
            result= collection.get(where={"$and": [{"project_id": project_id}, {"content_id": content_id}]})
            # logger.info(f"Result: {result}")

            data={'where':{"$and": [{"project_id": project_id}, {"content_id": content_id}]}}
 
            if result['ids']==[]:
                logger.info("No data with similar project_id and content_id in chroma_paragraph_embedding_collection")
                
            else:
                logger.info(f"Document found with same project_id and content_id")
                res = self.delete(chroma_paragraph_embedding_collection, data)
                logger.info(f"res_deleted:{res}")
                

            logger.info(f"Checking whether project_id and content_id exist in RAW corpuss collection")    
            collection= client.get_or_create_collection(name=chroma_store_entire_page_collection)
            result= collection.get(where={"$and": [{"project_id": project_id}, {"content_id": content_id}]})
            # logger.info(f"Result of finding same project_id and content_id:{result}")
            
            if result['ids']==[]:
                logger.info("No data with similar project_id and content_id in RAW Corpus collection")
                
                
            else:
                logger.info(f"Document found with same project_id and content_id")
                res = self.delete(chroma_store_entire_page_collection, data)
                logger.info(f"deleted res:{res}")
                

            return {"status":1, "message": "", "body":""}
        except Exception as e:
            logger.error(f"Error while deleting data: {str(e)}")
            return {"status":0, "message":f"Error occurred while deleting project id: {str(e)}"}
        
    def check_file_data_exist(self,project_id, content_id, collection_name=pdf_collection):
        try:
            logger.info(f"Checking whether project_id and content_id exist in pdf collection")
            client=self.connect()
            collection = client.get_or_create_collection(name=collection_name)
            result= collection.get(where={"$and": [{"project_id": project_id}, {"content_id": content_id}]})
            # logger.info(f"Result: {result}")

            data={'where':{"$and": [{"project_id": project_id}, {"content_id": content_id}]}}
 
            if result['ids']==[]:
                logger.info("No data with similar project_id and content_id in chroma_paragraph_embedding_collection")
                
            else:
                logger.info(f"Document found with same project_id and content_id")
                res = self.delete(pdf_collection, data)
                logger.info(f"res_deleted:{res}")

            return {"status":1, "message": "", "body":""}
        except Exception as e:
            logger.error(f"Error while deleting data: {str(e)}")
            return {"status":0, "message":f"Error occurred while deleting project id: {str(e)}"}


        
    def save_complete_pdf(self,file_name, file_extension,
                                project_id, content_id, project_name, full_text, collection_name=pdf_collection):
        try:
            client=self.connect()
            import time
            logger.info("Inserting pdf content")
            start_time = time.time()
           

            insert_data ={
                "documents": [full_text ],
                "metadatas":{"project_name":project_name, "project_id":project_id, "content_id":content_id, 
                "file_name":file_name,"file_type":file_extension,"created_at":datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")},
                "ids":str(uuid.uuid4())
            }
            insert_response=self.insert(collection_name,insert_data)
            logger.info("Insert_result: %s", insert_response)
            end_time = time.time()
            time_taken=process_tat(start_time, end_time)
            logger.info(f"time_taken:{time_taken}")          
            return  {"status":1, "message":"File stored in database", "body":""}
        
        except Exception as e:
            logger.error(f"Error while inserting data: {str(e)}")
            return {"status":0, "message":str(e), "error":""}
        

    def store_web_page(self, raw_text, crawl_application_name, crawl_application_id,crawl_link):
        try:
            result=self.delete_web_page(crawl_application_id, raw_text[0]["link"])
            if result["status"] == 0:
                    return result
            client=self.connect()
   
            documents = []
            metadatas=[]
            ids=[]

            for i in range (len(raw_text)):
                logger.info(f"storing raw corpus of link:{raw_text[i]['link']}")
                documents.append(raw_text[i]["content"])
                metadatas.append({"project_name":crawl_application_name, "project_id":crawl_application_id, "content_id": crawl_link,
                "sub_link":raw_text[i]["link"], "file_type": "website",
                "created_at":datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")})
                ids.append(str(uuid.uuid4()))

        
            insert_data ={
                "documents": documents,
                "metadatas":metadatas,
                "ids":ids
            }
    
        
            insert_result=self.insert(website_collection, insert_data)
            logger.info(f"Insert store raw corpus result: %s" %insert_result)
            
            # if result.inserted_id is None:
            #     logger.error("RAW corpus Pragraph not stored in database")
            #     return {"status":0 , "message":"unable to insert RAW paragraph to database"}
            # else:
            #     logger.info("RAW corpus Pragraph stored in database")

            return {"status":1, "message": "Web_page inserted successfully","body":""}

    
        except Exception as e:
            logger.error(f"Error while inserting data: {str(e)}")
            return {"status":0, "message":f"Error occurred while storing raw corpus: {str(e)}"}
        

    def delete_web_page(self, project_id, sub_link):
        try:
            client=self.connect()
            logger.info(f"Checking whether project_id{project_id} and sub_link{sub_link} exist in Website collection")    
            collection= client.get_or_create_collection(name=website_collection)
            result= collection.get(where={"$and": [{"project_id": project_id}, {"sub_link":sub_link}]})
            
            data={'where':{"$and": [{"project_id": project_id}, {"sub_link": sub_link}]}}
            if result['ids']==[]:
                logger.info("No data with similar project_id and content_id in RAW Corpus collection")
                
            else:
                logger.info(f"Document found with same project_id and content_id")
                res = self.delete(website_collection, data)
                logger.info(f"res_deleted:{res}")
            return {"status":1, "message": "", "body":""}
        except Exception as e:
            logger.error(f"Error while deleting data: {str(e)}")
            return {"status":0, "message":f"Error occurred while deleting project id: {str(e)}"}
        


