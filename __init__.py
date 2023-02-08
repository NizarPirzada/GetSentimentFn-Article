import logging
import json
import azure.functions as func
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from newspaper import Article 
from newspaper import Config

from GoogleNews import GoogleNews
import requests

user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
config = Config()
config.browser_user_agent = user_agent

key = "ee183bea759a4cf0b92e435ce03d9551"
endpoint = "https://hctextanalytics.cognitiveservices.azure.com/"

def authenticate_client():
    ta_credential = AzureKeyCredential(key)
    text_analytics_client = TextAnalyticsClient(
            endpoint=endpoint, 
            credential=ta_credential)
    return text_analytics_client

client = authenticate_client()

def sentiment_analysis_example(client, documents):
    try:
        response = client.analyze_sentiment(documents=documents)[0]
        sentiment = {}
        sentiment["Document Sentiment"] = response.sentiment
        sentiment["Positive Confidence"] = response.confidence_scores.positive
        sentiment["Neutral Confidence"] = response.confidence_scores.neutral
        sentiment["Negative Confidence"] = response.confidence_scores.negative
        return sentiment
    except:
        return None


def key_phrase_extraction_example(client, documents):
    
    try:

        response = client.extract_key_phrases(documents = documents)[0]

        if not response.is_error:
            return response.key_phrases
            # for phrase in response.key_phrases:
            #     print("\t\t", phrase)
        else:
            return None

    except Exception as err:
        return None

def entity_recognition_example(client, documents):
    
    try:
        result = client.recognize_entities(documents = documents)[0]
        NERs = []
        for entity in result.entities:
            NER = {}
            NER["text"] = entity.text
            NER["category"] = entity.category
            if entity.subcategory is not None:
                NER["category"] += "-" + entity.subcategory
            NERs.append(NER)
        return NERs
    except Exception as err:
        return None

def getSentimentAnalysis(articles):
    for article in articles:
        
        articlelink = "https://" + article["link"]
        directlink = ""
        NERs = None
        keyphrase = None
        sentiments = None
        try:
            response = requests.get(articlelink, stream=True, timeout=5)
            directlink = response.url
            
            newsArticle = Article(directlink,config=config)
            newsArticle.download()
            newsArticle.parse()
            documents = [newsArticle.text]
            if documents:
                NERs = entity_recognition_example(client, documents)
                # print(NERs)
                keyphrase = key_phrase_extraction_example(client, documents)
                # print("keypharase : ", keypharase)
                sentiments = sentiment_analysis_example(client, documents)
                # print("sentiments : ", sentiments)
        except:
            directlink = ""
        article["directlink"] = directlink
        article["NERs"] = NERs
        article["keyphrase"] = keyphrase
        article["sentiments"] = sentiments
    return articles

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    articles = req.params.get('Articles')
    keyword = req.params.get('keyword')
    if not articles:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            articles = req_body.get('Articles')
            keyword = req_body.get('keyword')

    if articles:
        
        results = getSentimentAnalysis(articles)
        data = {"Articles": results, "keyword":keyword}
        return func.HttpResponse( json.dumps(data, indent=4, sort_keys=True, default=str),status_code=200 )
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
