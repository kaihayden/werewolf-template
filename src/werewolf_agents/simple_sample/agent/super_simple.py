from openai import OpenAI
import logging
from sentient_campaign.agents.v1.api import IReactiveAgent
from sentient_campaign.agents.v1.message import ActivityMessage, ActivityResponse, MimeType, ActivityMessageHeader, MessageChannelType, TextContent

# Set up logging
logger = logging.getLogger("simple_agent")
level = logging.DEBUG
logger.setLevel(level)
logger.propagate = True
handler = logging.StreamHandler()
handler.setLevel(level)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class SimpleReactiveAgent(IReactiveAgent):
    
    def __init__(self):
        pass
    
    # initialize is a required method for the IReactiveAgent interface
    def __initialize__(self, name: str, description: str, config: dict = None):
        self._name = name
        self._description = description
        self._config = config or {}

        # This comes from the runner, it has a method to set these configs with a key you provide there: 
        self.llm_config = self.sentient_llm_config["config_list"][0]
        self.openai_client = OpenAI(
            api_key=self.llm_config["api_key"],
            base_url=self.llm_config["llm_base_url"],
        )

        ########################### System Prompt ###########################
        # Here we create a simple list for storing message history
        # In the first entry of this list we put the system prompt. 
        # The easiest way to modify this message is to edit this system prompt!     

        self.message_history = [{
            "role": "system",
            "content": f"You are {self._name}, an expert player in the game Werewolf (Mafia). You will be assigned one of these roles: Villager, Werewolf, Seer, or Doctor. Adapt your strategy based on your role:\n\n- Villager: Find and eliminate werewolves. Observe and vote carefully.\n- Werewolf: Eliminate villagers and blend in. Coordinate with your team during the night. Keep night actions private and avoid mentioning them during day discussions.\n- Seer: Identify werewolves. Use info wisely, avoid early exposure.\n- Doctor: Protect players. Keep your role hidden if possible.\n\nThe game alternates between Night (private actions) and Day (discussion and voting). Your goal is to lead your team to victory using logic, persuasion, and strategic thinking. Always contribute and vote thoughtfully."
            # "content": f"You are {self._name}. You are an expert at the conversational game Werewolf, also known as Mafia. Your goal is to use logic, deception, and persuasive reasoning to achieve victory for your assigned role. If you are a werewolf, your goal is to mislead the villagers and avoid being discovered. If you are a villager, your goal is to uncover the werewolves and protect the village. Always actively participate in discussions, and when prompted for any kind of vote, make a thoughtful decision based on the information available. Use clever tactics to either create doubt or expose inconsistencies in others' stories, depending on your role. Remember to be convincing and adaptable in your arguments to influence others effectively. If you refuse to vote or contribute, you will be penalized."
        }]
        logger.debug(f"Initialized {self._name} with config: {self._config}")

    # this is another required method, this is the method that the game controller will call to notify your agent of something when no response is needed
    async def async_notify(self, message: ActivityMessage):

        # here we add the message to the message history, extracting relevant information from the ActivityMessage object it came in
        message_text = f"[From - {message.header.sender}| {message.header.channel}]: {message.content.text}"
        self.message_history.append({
            "role": "user",
            "content": message_text
        })
        logger.debug(f"Message added to history: {message_text}")

    # this is a required method, this is the method that the game controller will call to notify your agent of something when a response is needed
    async def async_respond(self, message: ActivityMessage) -> ActivityResponse:

        message_text = f"[From - {message.header.sender}| {message.header.channel}]: {message.content.text}"
        self.message_history.append({
            "role": "user",
            "content": message_text
        })
        logger.debug(f"Message added to history: {message_text}")
        
        logger.debug("Generating response from OpenAI...")
        response = self.openai_client.chat.completions.create(
            model=self.llm_config["llm_model_name"],
            messages=self.message_history,
        )
        
        assistant_message = f"[From {self._name} (me) | {message.header.channel}]: {response.choices[0].message.content}"
        self.message_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        logger.debug(f"Assistant response added to history: {assistant_message}")
        
        return ActivityResponse(response.choices[0].message.content)

# Testing the agent: Make sure to comment out this code when you want to actually run the agent in some games. 

# # Since we are not using the runner, we need to initialize the agent manually using an internal function:
# agent = SimpleReactiveAgent()
# agent._sentient_llm_config = {
#     "config_list": [{
#             "llm_model_name": "", # add model name here, should be: Llama31-70B-Instruct
#             "api_key": "", # add your api key here
#             "llm_base_url": "https://hp3hebj84f.us-west-2.awsapprunner.com"
#         }]  
# }
# agent.__initialize__("Fred", "A werewolf player")


# # Simulate receiving and responding to a message
# import asyncio

# async def main():
#     message = ActivityMessage(
#         content_type=MimeType.TEXT_PLAIN,
#         header=ActivityMessageHeader(
#             message_id="456",
#             sender="User",
#             channel="direct",
#             channel_type=MessageChannelType.DIRECT
#         ),
#         content=TextContent(text="Tell me about yourself")
#     )

#     response = await agent.async_respond(message)
#     print(f"Agent response: {response.response.text}")

# asyncio.run(main())
