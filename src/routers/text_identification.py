from src.logger import logger
from src import schema
from fastapi import APIRouter
from src.logger import logger
from src.config import application_name, application_id, website_collection
from src.data_processing.store_complete_link_content import process_store_webpage
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd


router=APIRouter(tags=["Text_Identification"])
# , current_user_uuid:dict=Depends(get_current_user)

@router.post("/language/")
async def identify_language(text:str):

        # if current_user_uuid["status"] == 0:
        #     return current_user_uuid
    from langdetect import detect_langs
    try: 
        langs = detect_langs(text) 
        for item in langs: 
            # The first one returned is usually the one that has the highest probability
            return {"status":1,"message": "", "language":item.lang, "item_probability":item.prob }
        
    except Exception as e:
        logger.info(f"An error occurred while scraping: {str(e)}")
        return {"status":0 , "message":"", "body":str(e)}
  

analyser = SentimentIntensityAnalyzer()

@router.post("/sentiment_analysis/")
def print_sentiment_scores(tweets:str):
    vadersenti = analyser.polarity_scores(tweets)
    logger.info(pd.Series([vadersenti['pos'], vadersenti['neg'], vadersenti['neu'], vadersenti['compound']]))
    if vadersenti['compound'] >= 0.5:
        return {"status":1 , "message":"", "body":"Positive"}
    elif vadersenti['compound'] > -0.5:
        return {"status":1 , "message":"", "body":"Nuetral"}
    else:
        return {"status":1 , "message":"", "body":"Negative"}
       

# text = 'This goes beyond party lines.  Separating families betrays our values as Texans, Americans and fellow human beings'
