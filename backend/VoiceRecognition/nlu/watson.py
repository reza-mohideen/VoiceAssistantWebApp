import os
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from dotenv import load_dotenv

load_dotenv()
class Watson():
    def __init__(self):
        authenticator = IAMAuthenticator(os.getenv('KEY'))

        self.assistant = AssistantV2(
            version=os.getenv('VERSION'),
            authenticator=authenticator
        )
        self.assistant.set_service_url(os.getenv('URL'))
        self.assistant.set_disable_ssl_verification(True)

        self.session_id = None
        self.create_session()

    def create_session(self):
        response = self.assistant.create_session(
            assistant_id=os.getenv('ASSISTANT_ID')
        ).get_result()
        self.session_id = response["session_id"]

        return response

    def delete_session(self):
        response = self.assistant.delete_session(
            assistant_id=os.getenv('ASSISTANT_ID'),
            session_id=self.session_id
        ).get_result()

    def send_message(self, input):
        response = self.assistant.message_stateless(
            assistant_id=os.getenv('ASSISTANT_ID'),
            input={
                'message_type': 'text',
                'text': input
        }).get_result()

        return response

    def get_entities(self, response):
        return response["output"]["entities"]

    def get_intents(self, response):
        return response["output"]["intents"]

if __name__ == "__main__":
    watson = Watson()
    response = watson.send_message("what is the current price of apple stock")
    print(watson.get_intents(response))