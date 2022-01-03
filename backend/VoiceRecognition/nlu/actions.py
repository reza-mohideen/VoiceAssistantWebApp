from .watson import Watson
from .word2math import preprocessed, math
from .word2stocks import company_stock
from .word2weather import weather
from .word2wiki import wiki


class Action:
    def __init__(self):
        self.watson = Watson()

    def take_action(self, command):
        result_str = ""
        intent = "default"
        confidence = 0
        response = self.watson.send_message(command)
        print("response", response)
        try:
            intent = self.watson.get_intents(response)[0]["intent"]
            confidence = self.watson.get_intents(response)[0]['confidence']
        except IndexError:
            intent = 'default'

        print("intent:", intent)
        print("confidence:", confidence)
        if confidence > 0.30:
            if intent == "stocks":
                result_str = company_stock(command)
            elif intent == "Weather":
                result_str = weather(command)
            elif intent == "wikipedia":
                result_str = wiki(command)
                # TODO wiki.py needs work
            elif intent == "math":
                result_str = math(preprocessed(command))
            elif intent == 'default':
                result_str = "I didn't understand. You can try rephrasing."
        else:
            result_str = "I didn't understand. You can try rephrasing."

        print("answer:", result_str)

        return result_str



if __name__ == '__main__':
    action_obj = Action()
    print(action_obj.take_action("What five times five"))