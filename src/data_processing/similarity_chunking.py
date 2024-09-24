from sentence_transformers import SentenceTransformer, util
from typing import List
from src.logger import logger
import spacy
from src.config import Model_name, spacy_model, cosine_threshold

class SentenceTransformersSimilarity:
    def __init__(self, model_name=Model_name, similarity_threshold=float(cosine_threshold)):
        self.model = SentenceTransformer(model_name)
        self.similarity_threshold = similarity_threshold
        
    def similarities(self, sentences: List[str]):
        embeddings = self.model.encode(sentences)
        # Calculate Cosine similarity for neighboring sentences
        similarities = []
        for i in range(1, len(embeddings)):
            sim = util.pytorch_cos_sim(embeddings[i-1], embeddings[i]).item()
            similarities.append(sim)
        return similarities
    
class SpacySentenceSplitter:
    def __init__(self):
        self.nlp = spacy.load(spacy_model)

    def split(self, text: str):
        doc = self.nlp(text)
        return [str(sent).strip() for sent in doc.sents]

class SimilarSentenceSplitter:
    def __init__(self, similarity_model, sentence_splitter):
        self.model = similarity_model
        self.sentence_splitter = sentence_splitter

    def split_text(self, text: str, group_max_sentence=10):
        sentences = self.sentence_splitter.split(text)
        # logger.info(f"Sentences:{sentences}")

        if len(sentences) == 0:
            return []
        
        similarities = self.model.similarities(sentences)

        # Initialize groups with the first sentence
        groups = [[sentences[0]]]

        for i in range(1, len(sentences)):
            if len(groups[-1]) >= group_max_sentence:
                groups.append([sentences[i]])
            elif similarities[i-1] > self.model.similarity_threshold:
                groups[-1].append(sentences[i])
            else:
                groups.append([sentences[i]])
        
        groups_= [' '.join(g) for g in groups]
        # logger.info(f"Groups:{ [' '.join(g) for g in groups]}")

        return groups_
    

model= SentenceTransformersSimilarity()
sentence_splitter= SpacySentenceSplitter()
splitter= SimilarSentenceSplitter(model, sentence_splitter)
                                  
def get_similar_chunks(text):
    similar_chunks=splitter.split_text(text)
    # logger.info(f"Similar chunks:{similar_chunks}")
    return similar_chunks