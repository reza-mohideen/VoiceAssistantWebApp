from os import name
from bs4 import BeautifulSoup
import requests
import spacy

def search_entities(dict, keyword):
    for key in dict.keys():
        if keyword in key:
            return key

    return None

def clean_text(text):
    nlp = spacy.load('en_core_web_trf')
    named_entities = {}
    topic = None
    doc = nlp(text)

    for ent in doc.ents:
        named_entities[ent.text] = (ent.start_char, ent.end_char)

    for token in doc:
        if token.dep_ == "pobj":
            topic = search_entities(named_entities, token.text)
            if topic:
                return topic.replace(" ", "_")
            else:
                return token.text.replace(" ", "_")
            
    if named_entities:
        return next(iter(named_entities.keys())).replace(" ", "_")

    return None
        

def wiki(user_question):
    
    try:
        topic = clean_text(user_question)
        response = requests.get(url="https://en.wikipedia.org/wiki/" + topic)
        # print(response.status_code)

        soup = BeautifulSoup(response.content, 'lxml')
        title = soup.find(id="firstHeading")
        print(title.string)

        body = soup.find(id="mw-content-text").findAll("p")

        paragraph = body[1].get_text()
        last_char = paragraph[-1]
        list_elements = soup.find(id="mw-content-text").find("ul").findAll("li")

        result = ""
        if len(list_elements) > 0 and len(paragraph.split()) < 15:
            for bullets in list_elements:
                result += bullets.get_text()
                print(bullets.get_text())

        else:
            result = paragraph
            print(paragraph)

        return result

    except Exception as e:
        return "Sorry. I have no information about this topic"
        print(e)

if __name__ == "__main__":
    wiki("tell me a little bit about india")
    wiki("give me facts about oranges")
    wiki("who is tom brady")
    wiki("tell me about betty white")
    wiki("give me facts about cottage cheese")
    wiki("give me facts about kit kat")
    wiki("give me facts about teeth")