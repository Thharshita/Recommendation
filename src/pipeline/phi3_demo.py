from fastapi import FastAPI
from llama_cpp import Llama
import time
import torch
from src.data_processing.text_processing import process_tat
from src.logger import logger
from src.utils import get_database
from src.config import (phi_response_collection, model_path,
                max_input_lenght, cpu_threads_count, gpu_layers_count, query_max_token, summ_max_token,
                qna_max_token, use_device_to_process)
import datetime
# model_path = "C:/Users/HM/.cache/huggingface/hub/models--microsoft--Phi-3-mini-4k-instruct-gguf/snapshots/999f761fe19e26cf1a339a5ec5f9f201301cbb83/Phi-3-mini-4k-instruct-q4.gguf"

if use_device_to_process=="gpu":
    device = torch.device("cuda" )
    # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
else:
    device = torch.device("cpu")

# torch.cuda.set_device(0)
# device = torch.device("cuda:0")
# torch.cuda.set_device(device) 
# torch.cuda.empty_cache()

print("device_type:-",device)
       
llm = Llama(
    model_path=model_path,
    n_ctx= int(max_input_lenght),       # Max sequence length
    n_threads= int(cpu_threads_count),      # Number of CPU threads to use
    n_gpu_layers= int(gpu_layers_count),  # Number of layers to offload to GPU (if available)
    main_gpu=1
)
# llm.to('cuda')
app = FastAPI()

def answer_the_question(context,query):
    
    output = llm(
        f"<|system|>\nYou have been provided with the context and a question, try to find out the answer to the query only using the context information. If the answer to the query is not found within the context, return Unable to understand.<|end|> <|user|>\n context:{context} \n question:{query}<|end|>\n<|assistant|>",
        max_tokens= int(query_max_token),  # Generate up to 256 tokens
        stop=["<|end|>"], 
        echo=False       # Do not echo the prompt in the output
    )
    logger.info("Wait!! Generating response")
    # logger.info(f"output:{output}")
    # logger.info(f"output_word_count:{len(output.split(''))}")
    return output["choices"][0]["text"]

def create_summary(context,query):
    output = llm(
        f"<|system|>\nYou have been provided with the context , Create a summary for the given context.<|end|> <|user|>\n context:{context} \n question:{query}<|end|>\n<|assistant|>",
        max_tokens= int(summ_max_token),  # Generate up to 256 tokens
        stop=["<|end|>"], 
        echo=False       # Do not echo the prompt in the output
    )
    logger.info("Wait!! Generating response")
    # logger.info(f"output:{output}")
    # logger.info(f"output_word_count:{len(output.split(''))}")
    return output["choices"][0]["text"]


def create_question_and_answer(context,query,count):
    output = llm(
        # f'<|system|>\nYou have been provided with the context. Generate {count} questions with respective answers from given context in format [{"question1":"","answer1":""},{"question2":"","answer2":""}] like this.<|end|> <|user|>\n context:{context} \n<|end|>\n<|assistant|>',
        f"<|system|>\n"
        "You have been provided with the context. "
        f"Generate {count} questions with respective answers from given context in format "
        "[{'question1':'','answer1':''},{'question2':'','answer2':''}] like this."
        "<|end|> "
        "<|user|>\n"
        f"Context: {context}"
        "<|end|>\n"
        "<|assistant|>",
        max_tokens= int(qna_max_token),
        stop=["<|end|>"],
        echo=False
    )
    logger.info("Wait!! Generating response")

    # logger.info(f"output:{output}")
    # logger.info(f"output_word_count:{len(output.split(''))}")
    return output["choices"][0]["text"]

import uuid

def store_response_in_collection(element_id, category, number_of_question, query, context,result):
    db = get_database()
    client = db.connect()
    collection = client.get_or_create_collection(name=phi_response_collection)
    documents=[result]
    metadatas=[{
        "context":context,
        "category": category,
        "number_of_question": number_of_question,
        "query": query ,
        "created_at":datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    }]
    ids=[str(uuid.uuid4())]
    insert_data={
                "documents": documents,
                "metadatas":metadatas,
                "ids":ids
            }
    
    insert_result=db.insert(phi_response_collection, insert_data)
    logger.info(f"Insert response of query: %s" %insert_result)
    return insert_result
    
def get_phi3_response(element_id, category, number_of_question, query, corpus):
    try:
        # logger.info(f"corpus:{corpus}")
        final_corpus=corpus
        logger.info(f"type_of_corpus:{type(corpus)}")
        tokens=len(corpus.split(' '))
        logger.info(f"Tokens in the corpus: {tokens}")
        if tokens>4096:
            logger.info(f"Corpus selected has tokens greater than 4096 , therefore only considering starting 4096 words.")
            corpus = corpus.split(' ')
            final_corpus =' '.join(corpus[:4096])
            logger.info(f"Updated corpus: {corpus}")
            logger.info(len(final_corpus))
        
        if category=='query':
            start_time = time.time()
            output = answer_the_question(final_corpus, query)
            if "Unable to understand" in output:
                return {"status":0, "message": "Insufficient Data", "Error":"Available context do not contain information related to your query."}
            end_time = time.time()
            processing_time = process_tat(start_time, end_time)
            logger.info(f"Total time taken for generating text:{processing_time}")
            logger.info(f"output_word_count:{len(output.split(' '))}")
            insert_response= store_response_in_collection(element_id, category, number_of_question,query, corpus, output)
            
            return {"status":1, "message": "success", "generated_response":output, "Tat":processing_time}
        
        elif category=='summary':
            start_time = time.time()
            output = create_summary(final_corpus, query)
            end_time = time.time()
            processing_time = process_tat(start_time, end_time)
            logger.info(f"output_word_count:{len(output.split(' '))}")
            logger.info(f"Total time taken for generating text:{processing_time}")
            insert_response= store_response_in_collection(element_id, category, number_of_question,query, corpus, output)
            
            return {"status":1, "message": "success", "generated_summary":output}
        else:
            start_time = time.time()
            output = create_question_and_answer(final_corpus, query,number_of_question)
            end_time = time.time()
            processing_time = process_tat(start_time, end_time)
            logger.info(f"output_word_count:{len(output.split(' '))}")
            logger.info(f"Total time taken for generating text:{processing_time}")
            insert_response= store_response_in_collection(element_id, category, number_of_question,query, corpus, output)
            
            return {"status":1, "message": "success", "generated_qna":output,"tat":processing_time}
        
    except Exception as e:
        return {"status":0, "message": "error", "body":str(e)}
    
# print(f"Is CUDA supported by this system? {torch.cuda.is_available()}")
# print(f"CUDA version: {torch.version.cuda}")
# cuda_id = torch.cuda.current_device()
# print(f"ID of current CUDA device:{torch.cuda.current_device()}")
# print(f"Name of current CUDA device:{torch.cuda.get_device_name(cuda_id)}")