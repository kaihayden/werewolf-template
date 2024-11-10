import json
import ast
import re

from parser_prompts import moderator_parse_prompt, user_parse_prompt

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
            # "content": f"You are {self._name}, an expert player in the game Werewolf (Mafia). You will be assigned one of these roles: Villager, Werewolf, Seer, or Doctor. Adapt your strategy based on your role:\n\n- Villager: Find and eliminate werewolves. Observe and vote carefully.\n- Werewolf: Eliminate villagers and blend in. Coordinate with your team during the night. Keep night actions private and avoid mentioning them during day discussions.\n- Seer: Identify werewolves. Use info wisely, avoid early exposure.\n- Doctor: Protect players. Keep your role hidden if possible.\n\nThe game alternates between Night (private actions) and Day (discussion and voting). Your goal is to lead your team to victory using logic, persuasion, and strategic thinking. Always contribute and vote thoughtfully."
            # "content": f"You are {self._name}. You are an expert at the conversational game Werewolf, also known as Mafia. Your goal is to use logic, deception, and persuasive reasoning to achieve victory for your assigned role. If you are a werewolf, your goal is to mislead the villagers and avoid being discovered. If you are a villager, your goal is to uncover the werewolves and protect the village. Always actively participate in discussions, and when prompted for any kind of vote, make a thoughtful decision based on the information available. Use clever tactics to either create doubt or expose inconsistencies in others' stories, depending on your role. Remember to be convincing and adaptable in your arguments to influence others effectively. If you refuse to vote or contribute, you will be penalized."
            "content": f"You are {self._name}, an expert Werewolf (Mafia) player. You will be assigned one of the following roles: Villager, Werewolf, Seer, or Doctor. Play strategically based on your role: Villager: Identify and eliminate werewolves. Observe behavior, discuss, and vote carefully. Werewolf: Eliminate villagers and blend in during discussions. Coordinate privately during the night but do not mention night actions during the day.Seer: Identify werewolves. Use gathered information strategically and avoid exposing your role early. Doctor: Protect players. Keep your role hidden to avoid being targeted.The game alternates between Night (private actions) and Day (public discussion and voting). Always participate actively, make logical decisions, and adapt your strategy to lead your team to victory."
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
        
    # ==================================== #
    # ==================================== #
    # ==================================== #

    def parse_message(self, message, openai_client):

        sender = message.header.sender
        sender = str(sender).title()

        channel = message.header.channel
        text = message.context.text

        if sender == 'Moderator':
        
            message = moderator_parse_prompt.substitute(moderator_message=text)

            response = openai_client.chat.completions.create(
                model="Llama31-70B-Instruct",
                messages=[{"role":"system", "content": message}],
            )

            output = response.choices[0].message.content

            json_output = self.parse_json_from_string(output)

            self.parse_moderator_prompt_output(json_output)

        else:
        
            message = user_parse_prompt.substitute(user_message=text)

            response = openai_client.chat.completions.create(
                model="Llama31-70B-Instruct",
                messages=[{"role":"system", "content": message}],
            )

            output = response.choices[0].message.content

            json_output = self.parse_json_from_string(output)

            if isinstance(output, list):
                
                for json_item in output:
                    self.parse_user_prompt_output(json_output)

            elif isinstance(output, dict):
                self.parse_user_prompt_output(json_output)

    def parse_moderator_prompt_output(self, output):

        if output['action'] == "record_night_phase_death":
            self.game_state.record_night_phase_death(
                player_name = ['player_name']
            )

        elif output['action'] == "record_lynch":
            self.game_state.record_lynch(
                player_name = output['player_name'],
                player_role = output['player_role']
            )

        elif output['action'] == "init_role":
            self.game_state.init_role(player_role=output['player_role'])

        elif output['action'] == 'record_check':
            self.game_state.record_check(
                checked_player_name = output['checked_player_name'],
                is_good = output['is_good']
            )

        elif output['action'] == 'init_partner_wolf':
            self.game_state.init_partner_wolf(player_name = output['player_name'])

    def parse_user_prompt_output(self, output):

        if 'action' in output:

            if output['action'] == "record_vote":
                self.game_state.record_vote(
                    from_player_name = output.get('from_player_name'),
                    voted_player_name = output.get('voted_player_name')
                )
            elif output['action'] == "claim_seer":
                self.game_state.claim_seer(
                    player_name = output.get('player_name')
                )
            elif output['action'] == "claim_doctor":
                self.game_state.claim_doctor(
                    player_name = output.get('player_name')
                )
            elif output['action'] == "claim_checked":
                self.game_state.claim_checked(
                    player_name = output.get('player_name'), 
                    player_checked_name = output.get('player_checked_name'), 
                    player_role = output.get('player_role'), 
                    round_checked = output.get('round_checked')
                )
            elif output['action'] == "claim_saved":
                self.game_state.claim_saved(
                    player_name = output.get('player_name'), 
                    saved_player_name = output.get('saved_player_name'), 
                    round_saved = output.get('round_saved')
                )
            elif output['action'] == "player_suggests":
                self.game_state.player_suggests(
                    player_name = output.get('player_name'), 
                    player_suggested_name = output.get('player_suggested_name'), 
                    suggested_role = output.get('suggested_role'), 
                    certainty = output.get('certainty')
                )
        
        if 'suspicious' in output:

            pass

    def parse_json_from_string(self, input_string):
        """
        Parses any potential JSON or dictionary format from a string.
        Handles json-like strings, dictionaries, and lists of dictionaries.

        Args:
            input_string (str): The input string potentially containing JSON or dict format.

        Returns:
            dict | list | None: Parsed JSON object (dict or list) if successful, None otherwise.
        """
        # Step 1: Trim json''' ''' wrapper if it exists
        match = re.search(r"json'''(.*?)'''", input_string, re.DOTALL)
        if match:
            input_string = match.group(1).strip()

        # Step 2: Try JSON parsing directly
        try:
            return json.loads(input_string)
        except json.JSONDecodeError:
            pass

        # Step 3: Try ast.literal_eval for handling dictionary/list syntax
        try:
            return ast.literal_eval(input_string)
        except (ValueError, SyntaxError):
            pass

        # Step 4: Handle common malformed JSON corrections (e.g., single quotes to double quotes)
        try:
            formatted_string = re.sub(r"'", '"', input_string)
            return json.loads(formatted_string)
        except json.JSONDecodeError:
            pass

        # Step 5: Fallback: Try to extract JSON or dict content via regex and parse it
        match = re.search(r"(\{.*\}|\[.*\])", input_string, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                try:
                    return ast.literal_eval(match.group(1))
                except (ValueError, SyntaxError):
                    pass

        # If parsing fails, return None
        return None

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


