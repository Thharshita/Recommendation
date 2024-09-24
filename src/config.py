from configparser import ConfigParser

config=ConfigParser()
config.read("config.ini")

# from dotenv import load_dotenv
# load_dotenv()

#rnv
# database=os.getenv('database')
# host=os.getenv('host')
# paragraph_embedding_collection=os.getenv('paragraph_embedding_collection')
# uploaded_file_collection=os.getenv('uploaded_file_collection')
# paragraph_embedding_history_collection= os.getenv('paragraph_embedding_history_collection')
# reccomendation_collection= os.getenv('recommendation_collection')
# port=os.getenv('port')
# embedded_field_name=os.getenv("embedded_field_name")
# username=os.getenv("username")
# password=os.getenv("password")

#  configuration


# uploaded_file_collection = config["Store_file"]["uploaded_file_collection"]
# paragraph_embedding_history_collection = config["Db"]["paragraph_embedding_history_collection"]
recommendation_collection = config["Store_recommendation"]["recommendation_collection"]
cosine_threshold = config["Cosine_similarity"]["threshold"]
euclidean_threshold = config["Euclidean_similarity"]["threshold"]
# username = config["Db"]["username"]
# password = config["Db"]["password"]
Model_name = config["Model"]["model_name"]
spacy_model=config["Model"]["spacy_model"]
# user_database= config["User"]["database"]
user_collection= config["User"]["user_collection"]
adminn_collection= config["Admin"]["admin_collection"]
query_embedding_field= config["Store_recommendation"]["query_embedding_field"]


DATABASE_TYPE =config["Database_type"]["use_db"]


chroma_databse=config["Chromadb"]["database"]
chroma_port=config["Chromadb"]["port"]
chroma_host=config["Chromadb"]["host"]
chroma_paragraph_embedding_collection = config["Chromadb"]["paragraph_embedding_collection"]
chroma_embedded_field_name = config["Chromadb"]["embedded_field_name"]
chroma_store_entire_page_collection=config["Chromadb"]["store_entire_page_collection"]



application_name = config["Parameters"]["application_name"]
application_id = config["Parameters"]["application_id"]
element_id = config["Parameters"]["element_id"]
server_path= config["Chroma_storage"]["server_path"]


pdf_collection=config["Pdf_data"]["pdf_collection"]


website_collection = config["Website_data"]["website_collection"]


phi_response_collection=config["Gen_ai_phi3"]["phi_response_collection"]

SECRET_KEY = config["Oauth2_parameters"]["SECRET_KEY"]
ALGORITHM = config["Oauth2_parameters"]["ALGORITHM"]
ACCESS_TOKEN_EXPIRE_MINUTES =config["Oauth2_parameters"]["ACCESS_TOKEN_EXPIRE_MINUTES"]

model_path=config["Phi_3_Model"]["model_path"]
max_input_lenght=config["Phi_3_Model"]["max_input_lenght"]
cpu_threads_count=config["Phi_3_Model"]["cpu_threads_count"]
gpu_layers_count=config["Phi_3_Model"]["gpu_layers_count"]
query_max_token=config["Phi_3_Model"]["query_max_token"]
summ_max_token=config["Phi_3_Model"]["summ_max_token"]
qna_max_token=config["Phi_3_Model"]["qna_max_token"]
use_device_to_process=config["Phi_3_Model"]["use_device_to_process"]



