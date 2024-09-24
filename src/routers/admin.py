from src.logger import logger
import datetime
from fastapi import HTTPException,status,Depends
from fastapi import APIRouter
from src.utils import get_password_hash, get_database
from src.oauth2 import get_current_user
import uuid
import src.schema
from src.config import adminn_collection, user_collection

#CREATE_USER
router= APIRouter(tags=["Admin"])

#Create Admin
@router.post("/admin")
async def create_admin(new_admin: src.schema.Admin):
    try:
        db= get_database()
        client= db.connect()
        collection=client.get_or_create_collection(name=adminn_collection)
        existing_admin = collection.get(where={"email":new_admin.email})
        logger.info(f"Existing admin result:{existing_admin}")
        if existing_admin['ids']!=[]:
            logger.error(f"Unable to create admin as Admin with email {new_admin.email} already exists")
            return {"status":1,"message":f"Admin with email {new_admin.email} already exists","body":""}
        
        hashed_password= get_password_hash(new_admin.password)

        documents=[]
        metadatas=[]
        ids=[]

        documents.append(new_admin.email)
        metadatas.append({"email":new_admin.email,"password":hashed_password, "type":"admin", "token":"None", "Token_status": "None", "created_at":f"{datetime.datetime.now().strftime('%m-%d-%Y_%H:%M:%S')}"})
        ids.append(str(uuid.uuid4()))

        insert_data={
            "documents": documents,
            "metadatas":metadatas,
            "ids":ids
        }

        new=collection.add(**insert_data)
        logger.info(f"inserting new admin data: {new}")
        logger.info("new_admin created")

        return {"status":1,"message":"","body":"New admin created"}
    except Exception as e:
        logger.error(f"Error occured while creating admin: {str(e)}")
        return {"status":0, "message":f"Error occurred while creating project id: {str(e)}","body":""}
#Get user
@router.get("/get_user")
async def get_all_user(admin_username:str):
    try: 
        db= get_database()
        client= db.connect()         
        collection=client.get_or_create_collection(name=adminn_collection)
        existing_admin=collection.get(where={"email":admin_username})
        logger.info(f"Existing_admin:{existing_admin}")
        if existing_admin['ids']==[]:
            logger.error("Unauthorized admin ")
            return {"status":0,"message":" ","body":"Admin not valid"}
            # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
            #                     detail=f"ADMIN NOT VALID")
        
        collection_user=client.get_or_create_collection(name=user_collection)
        user=collection_user.get()
        logger.info(f"existing_user:{user}")
        if user==[]:
            logger.error(f"User not found")
            return {"status":0,"message":"User not exists", "body":""}
        
        return {"status":1,"message": "User are :", "body": user}
    except Exception as e:
        logger.error("Exception occured while delting user %s", str(e))
        return {"status":0, "message":"","body":str(e)}


# # get User
# @router.get("/get_user")
# async def get_user(current_user:str=Depends(get_current_user)):
#     try:
#         # print("current_user",current_user)
#         check_admin=collection_user.find_one({'UUID':current_user["UUID"]})
#         if check_admin==None:
#             logger.error("Admin trying to get data is not available")
#             return{"message":"Unregisterd Admin"}
#         if check_admin["Type"]!="Admin":
#             logger.error("Admin not valid")
#             logger.error("Unauthorized admin access")
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                                 detail=f"ADMIN not valid")
    
#         existing_user=collection_user.find()
#         a=[]
#         if existing_user:
#             for record in existing_user:
#                 record["_id"]=str(record["_id"])
#                 a.append(record)
#             logger.info("User shown as requested")
#             return a
#         # if existing_user:
#         #     return [{"_id":str(i["_id"])} for i in existing_user] 
#         else:
#             logger.error("No users found")
#             return {"message":"No users found"}
        
#     except Exception as e:
#         logger.exception("An error occurred while checking users user",str(e))
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

#show_userss


#Delete User
@router.delete("/delete_user")
async def delete_user(admin_username:str,user_UUID: str):
    try: 
        db= get_database()
        client= db.connect()         
        collection=client.get_or_create_collection(name=adminn_collection)
        existing_admin=collection.get(where={"email":admin_username})
        logger.info(f"Existing_admin:{existing_admin}")
        if existing_admin['ids']==[]:
            logger.error("Unauthorized admin ")
            return {"status":0, "message":"Admin not valid", "body":" "}
            # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
            #                     detail=f"ADMIN NOT VALID")
        
        collection_user=client.get_or_create_collection(name=user_collection)
        user=collection_user.get(ids=[user_UUID])
        logger.info(f"existing_user:{user}")
        if user['ids']==[]:
            logger.error(f"User with UUID {user_UUID} not found")
            return {"status":0, "message":"No user exist with that uuid", "body":""}
        
        result = collection_user.delete(ids=[user_UUID])
        logger.info("User deleted successfully")
        return {"status":1,"message": "User is successfully deleted", "body":""}
    except Exception as e:
        logger.error("Exception occured while delting user %s", str(e))
        return {"status":0, "message":"","body":str(e)}
        

# Revoke user token
@router.post("/revoke_token")
def revoke_token(user_UUID:str):
    try:       
        # print("current user",current_user)   
        db= get_database()
        client= db.connect()
        collection=client.get_or_create_collection(name=user_collection)
        existing_user=collection.get(ids=[user_UUID])
        logger.info(f"existing_user: {existing_user}")

        if existing_user['ids']==[]:
            logger.info("Token you are trying to revoke does not exist")
            return {"status":0,"message":"User not exists","body":""}
        else:
            update_token= collection.update(ids=[user_UUID], metadatas=[{ "Token_status": "Revoked"}])
            logger.info("User Revoked %s",update_token)
            return {"status":1,"message":"User Revoked","body":""}

    except Exception as e:
        logger.error("Error occured while revoking token %s",str(e))

@router.post("/unrevoke_token")
def unrevoke_token(user_UUID:str):
    try:       
        # print("current user",current_user)   
        db= get_database()
        client= db.connect()
        collection=client.get_or_create_collection(name=user_collection)
        existing_user=collection.get(ids=[user_UUID])
        logger.info(f"existing_user: {existing_user}")

        if existing_user['ids']==[]:
            logger.info("Token you are trying to revoke does not exist")
            return {"status":0,"message":"User not exists","body":""}
        else:
            update_token= collection.update(ids=[user_UUID], metadatas=[{ "Token_status": "OK"}])
            logger.info("User Unevoked %s",update_token)
            return {"status":1,"message":"User Unrevoked","body":""}

    except Exception as e:
        logger.error("Error occured while revoking token %s",str(e))

        
        
# #Valid the token

# @router.post("/valid_the_token")
# def revoke_token(user_UUID:str,current_user=Depends(get_current_user)):
#     try:       
#         # print("current user",current_user)   
#         check_admin=collection_user.find_one({'UUID':current_user["UUID"]})
#         # print("check_admin",check_admin)
#         if check_admin==None:
#             print("hii1")
#             logger.error("Admin not found")
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                                 detail=f"ADMIN NOT VALID")

#         if check_admin["Type"]!="Admin":
#             print("hii2")
#             logger.error("You are not authorized to delete any users") 
#             return {"message":"Not an Admin"}
        
#         user=collection_user.find_one({'UUID':user_UUID})
#         print(user)

#         if user==None:
#             logger.info("Token you are trying to acknowledge not exist")
#             return {"message":"User not exists"}
#         else:
#             a=collection_user.update_one({"UUID": user_UUID}, {"$set": {"Token_status": "OK"}})
#             logger.info("Token Status Changed to OK %s",a)
#             return {"message":"Token_Status Changed to OK"}

#     except Exception as e:
#         logger.error("Error occured while acklwoleding token status %s",str(e))




# #Disable or Enable User Account

# #View A list of All Users

# #Search for User By email or UUID

# #Assign Role or permission to User

# # Token Management:

# # Expire user access tokens
# # Revoke user access tokens
# # View active user sessions
# # View token usage logs or history



# #Create User
# # @router.post("/admin_create_user")
# # async def create_user(new_user:schema.User):
# #     try:
# #         existing_user=collection_user.find_one({"email":new_user.email})
# #         if existing_user:
# #             return {"message":"User with email already exists"}
# #         hashed_password= get_password_hash(new_user.password)
# #         new_user.password=hashed_password
# #         print("new_user:",new_user)
# #         new_user=dict(new_user)
# #         new_user["created_at"]=f"{datetime.datetime.now().strftime('%m-%d-%Y_%H:%M:%S')}"
# #         new_user["UUID"]=str(uuid.uuid4())
# #         print("new_user after adding 2 thing",new_user)
# #         new=collection_user.insert_one(new_user)
# #         if new.inserted_id:
# #             logger.info("new_user created")
# #             return {"message":"user_created"}
# #         else:
# #             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Failed tocreate new user")
# #     except Exception as e:
# #         logger.exception("An error occurred while creating a new user",str(e))
# #         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    

    
# # #Update Existing User Details {Email, Password,Profile Information}