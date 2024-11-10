#  - Record a vote (from player name, voted player name)
#  - Claim seer (player name)
#  - Claim doctor (player name)
#  - Claim checked (player_name, player_checked_name, player_role, round_checked)
#  - Claim saved  (player name, saved player name, round saved)
#  - Player suggests (player_name, player_suggested_role_name, suggested_role, certainty)

import json
import ast
import re

from parser_prompts import moderator_parse_prompt, user_parse_prompt

def parse_message(message, openai_client):

    sender = message.header.sender
    sender = str(sender).title()

    channel = message.header.channel
    text = message.context.text

    if sender == 'Moderator':
       
        prompt = moderator_parse_prompt.substitute(moderator_message=text)

        response = openai_client.chat.completions.create(
            model="Llama31-70B-Instruct",
            messages=[{"role":"system", "content": message}],
        )

        output = response.choices[0].message.content

        json_output = parse_json_from_string(output)

        parse_moderator_prompt_output(json_output)

    else:
       
        prompt = user_parse_prompt.substitute(user_message=text)

        response = openai_client.chat.completions.create(
            model="Llama31-70B-Instruct",
            messages=[{"role":"system", "content": message}],
        )

        output = response.choices[0].message.content

        json_output = parse_json_from_string(output)

        if isinstance(output, list):
            
            for json_item in output:
                parse_user_prompt_output(json_output)

        elif isinstance(output, dict):
            parse_user_prompt_output(json_output)

def parse_moderator_prompt_output(output):

    if output['action'] == "record_night_phase_death":
        record_night_phase_death(
            player_name = ['player_name']
        )

    elif output['action'] == "record_lynch":
        record_lynch(
            player_name = output['player_name'],
            player_role = output['player_role']
        )

    elif output['action'] == "init_role":
        init_role(player_role=output['player_role'])

    elif output['action'] == 'record_check':
        record_check(
            checked_player_name = output['checked_player_name'],
            is_good = output['is_good']
        )

    elif output['action'] == 'init_partner_wolf':
        init_partner_wolf(player_name = output['player_name'])

def parse_user_prompt_output(output):

    if 'action' in output:

        if output['action'] == "record_vote":
            record_vote(
                from_player_name = output.get('from_player_name'),
                voted_player_name = output.get('voted_player_name')
            )
        elif output['action'] == "claim_seer":
            claim_seer(
                player_name = output.get('player_name')
            )
        elif output['action'] == "claim_doctor":
            claim_doctor(
                player_name = output.get('player_name')
            )
        elif output['action'] == "claim_checked":
            claim_checked(
                player_name = output.get('player_name'), 
                player_checked_name = output.get('player_checked_name'), 
                player_role = output.get('player_role'), 
                round_checked = output.get('round_checked')
            )
        elif output['action'] == "claim_saved":
            claim_saved(
                player_name = output.get('player_name'), 
                saved_player_name = output.get('saved_player_name'), 
                round_saved = output.get('round_saved')
            )
        elif output['action'] == "player_suggests":
            player_suggests(
                player_name = output.get('player_name'), 
                player_suggested_name = output.get('player_suggested_name'), 
                suggested_role = output.get('suggested_role'), 
                certainty = output.get('certainty')
            )
    
    if 'suspicious' in output:

        pass

def parse_json_from_string(input_string):
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