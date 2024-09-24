from src.logger import logger
from fastapi import HTTPException,status,Depends
from fastapi import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from src.oauth2 import create_access_token
from typing import Annotated
from src.utils import get_database, verify_password
from src.config import user_collection
from jose import JWTError, jwt
router = APIRouter(tags=["Authentication"])


@router.post("/login")
# async def login(users_credentials:OAuth2PasswordRequestForm=Depends()):
async def login(users_credentials: OAuth2PasswordRequestForm=Depends()):
        # logger.info(f"user_Credentials: %s" % users_credentials)
        db= get_database()
        client=db.connect()
        # logger.info(f"{users_credentials.username}")
        collection= client.get_collection(name= user_collection)
        existing_user=collection.get(where={"email":users_credentials.username})
        logger.info(f"exiting_user:{existing_user}")
        # logger.info(f"Existing_user:{existing_user}")
        if existing_user['ids']==[]:
            logger.error("INVALID USER")
            # return {"status":0, "message":"", "body": "USERNAME NOT FOUND"}
            raise HTTPException(status_code=400, detail={"status":0,"message":"", "body":"Incorrect username or password"})
        
        if not verify_password(users_credentials.password, existing_user['metadatas'][0]["password"]):
            logger.error("INVALID PASSWORD")
            # return {"status":0, "message":"", "body": "EMAIL NOT FOUND"}
            raise HTTPException(status_code=400, detail={"status":0,"message":"", "body":"Incorrect username or password"})
        
        if existing_user['metadatas'][0]['Token_status']== "Revoked":
            logger.info("Your Token is terminated")
            # return {"status":0,"message":"Your token is terminated", "body":""}
        
        # if existing_user['metadatas'][0]['token']=="None":
        access_token=create_access_token({"user_UUID":existing_user['ids'][0]})  #id sent is a string
        return {"access_token":access_token,"token_bearer":"bearer"}
    
