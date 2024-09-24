from src.logger import logger
from bson import ObjectId
import datetime
import src.schema
from fastapi import HTTPException,status,Depends
from fastapi import APIRouter
from src.utils import  get_database, get_password_hash
# from oauth2 import create_access_token,get_current_user
import uuid
from src.config import user_collection
#CREATE_USER
router= APIRouter(tags=["Users"])

@router.post("/create_user")
async def create_user(new_user:src.schema.User):
    try:
        db= get_database()
        client= db.connect()
        collection=client.get_or_create_collection(name=user_collection)
        existing_user=collection.get(where={"email":new_user.email})
        logger.info("Existing user result: %s", existing_user)
        if existing_user['ids']!=[]:
            return {"status":1,"message":"User with email already exists","body":""}
        
        hashed_password= get_password_hash(new_user.password)
        new_user.password=hashed_password

        documents=[]
        metadatas=[]
        ids=[]

        documents.append(new_user.email)
        metadatas.append({"email":new_user.email,"password":new_user.password, "type":"user", "token":"None", "Token_status": "None", "created_at":f"{datetime.datetime.now().strftime('%m-%d-%Y_%H:%M:%S')}"})
        ids.append(str(uuid.uuid4()))

        insert_data={
            "documents": documents,
            "metadatas":metadatas,
            "ids":ids
        }
        new=collection.add(**insert_data)
        logger.info(f"inserting new user data: {new}")
        logger.info("new_user created")

        return {"status":1,"message":"","body":"New user created"}
            
    except Exception as e:
        logger.exception("An error occurred while creating a new user",str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    
# #Delete User 
# @router.delete("/user")
# async def delete_document(UUID: str,current_user=Depends(get_current_user)):
#     db= get_database()
#     collection=db.get_or_create_collection(name=user_collection)
#     user=collection.get(where={'UUID':UUID})
#     logger.info(f"get_user_with_same_uuid: {user}")
#     if user==None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                             detail=f"{UUID} does not exist")

#     if user["UUID"]!=current_user["user_UUID"]:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not Authorized to perform this action")
#     result = collection.delete(where={'UUID': UUID})
#     if result:
#         return {"message": "User is successfully deleted"}

    
# @router.post("/get_token")
# def generate_new_token(uuid:str, id:str):
#     db= get_database()
#     yes=db.get(where={"UUID":uuid})
#     logger.info(f"get_user_with_same_uuid: {yes}")
    
#     if yes and yes["Token_status"] =="OK":
#         new_token=create_access_token({"user_id":id,"user_UUID":uuid})
#         logger.info("New token created")
#         return {"mesage":f"Your new token is available {new_token}"}
#     else:
#         logger.info("User credential does not match")
#         return{"mesage":"Invalid UUID/id"}