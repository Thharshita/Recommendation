from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import  datetime,timedelta,timezone
import src.schema
from src.logger import logger
from src.utils import get_database
from src.config import user_collection, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def create_access_token(data:dict):  #has uuid_user which is string
    logger.info("creating access token")
    # logger.info(f"data:{data}")
    to_encode= data.copy()
    expire = datetime.now(timezone.utc)+ timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp":expire})
    encoded_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    db= get_database()
    client= db.connect()
    collection= client.get_collection(name=user_collection)
    # yes=collection.update_one({"UUID":data.get('user_UUID')},{"$set":{"Token":encoded_jwt,"Token_status":"OK"}}) #{"user_id":existing_user["_id"],"user_UUID":existing_user["UUID"]}
    # print(yes)
    update_token= collection.update(ids=[data.get("user_UUID")], metadatas=[{"token":encoded_jwt, "Token_status": "OK"}])
    # logger.info(f"update token:{update_token}")
    # if yes.modified_count ==1:

    logger.info("Lets Check")
    check=collection.get(ids=[data.get("user_UUID")])
    # logger.info(f"update check:{check}")
    logger.info("Token saved in the database")
    return encoded_jwt
    # else:
    #     logger.error("Token not saved in the database")

def verify_access_token(token,credential_exception):
    try:   
        # print("working") 
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        # print("payload",payload)
        UUID=payload.get("user_UUID")

        if UUID==None:
            raise credential_exception
        
        else:
            token_data=src.schema.Token_Data(UUID=UUID)
            print("token_data",token_data)

        # Check token status in the database
        db= get_database()
        client= db.connect()
        collection= client.get_collection(name=user_collection)
        user = collection.get(ids=UUID)
        # logger.info(f"user whom to verify:{user}")
        
        if user['ids']==[]:
            return {"status":0,"message":"", "body":"No id found , invalid token"}
        
        if user['metadatas'][0]["Token_status"] == "Revoked":
            logger.info("Your Token is terminated")
            return {"status":0,"message":"Your token is terminated", "body":""}

        return {"status":1, "token_data":token_data}
    
    except jwt.ExpiredSignatureError:
        logger.error("Please renew your token")
        # Handle token expiration
        return {"status":0, "message":"", "body":"Please renew your token"}
    
    # except JWTError:
    #     # Handle invalid token
    #     logger.error("Invalid token")
    #     raise credential_exception
    
    except Exception as e:
        logger.error(f"verification error {str(e)}")


def get_current_user(token = Depends(oauth2_scheme)):
    try:
    
        credential_exception=HTTPException(status_code= status.HTTP_401_UNAUTHORIZED,detail=f"Could not validate credentials",headers={"WWW-Authenticate":"Bearer"})
        token_data=verify_access_token(token,credential_exception)
        return token_data
    except Exception as e:
        logger.error(f"get_current_user error {str(e)}")