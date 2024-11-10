from string import Template

moderator_parse_prompt = Template("""
Analyze the moderator's message and determine the type of action it represents. Choose from the following actions:

1. "action": "record_night_phase_death" if the message indicates a player has died during the night. Include "player_name": "<Player Name>".
2. "action": "record_lynch" if the message indicates a player was lynched due to voting, with "player_name": "<Player Name>" and "player_role": "<Role>".
3. "action": "init_role" if the message assigns a role to the player, with "player_role": "<Role>".
4. "action": "record_check" if the message indicates that a player was checked by another player to determine their alignment (good or bad). Include "checked_player_name": "<Checked Player Name>" and "is_good": <true or false>.
5. "action": "init_partner_wolf" if the message reveals that a player has been assigned a partner wolf. Include "player_name": "<Player Name>".

Input: $moderator_message

Expected JSON Output:
If the message indicates an action, return it in JSON format, for example:
- { "action": "record_night_phase_death", "player_name": "Player Name" }
- { "action": "record_lynch", "player_name": "Player Name", "player_role": "Role" }
- { "action": "init_role", "player_role": "Role" }
- { "action": "record_check", "checked_player_name": "Checked Player Name", "is_good": True }
- { "action": "init_partner_wolf", "player_name": "Player Name" }

Return only the JSON Output {
""")

user_parse_prompt = Template("""
Analyze the player or moderator's message and determine the type of action it represents. Choose from the following actions:

1. "action": "record_vote" if the message indicates that a player voted for another player. Include "from_player_name": "<Player Name>" and "voted_player_name": "<Voted Player Name>".

2. "action": "claim_seer" if the message indicates that a player claims to be the Seer. Include "player_name": "<Player Name>".

3. "action": "claim_doctor" if the message indicates that a player claims to be the Doctor. Include "player_name": "<Player Name>".

4. "action": "claim_checked" if the message indicates that a player claims to have checked another player’s role as the Seer. Include "player_name": "<Player Name>", "player_checked_name": "<Player Checked Name>", "player_role": "<Role>", and "round_checked": <Round Number>.

5. "action": "claim_saved" if the message indicates that a player claims to have saved another player as the Doctor. Include "player_name": "<Player Name>", "saved_player_name": "<Saved Player Name>", and "round_saved": <Round Number>.

6. "action": "player_suggests" if the message indicates that a player suggests another player has a certain role, specifying how certain they are about this claim. Include "player_name": "<Player Name>", "player_suggested_name": "<Player Suggested Name>", "suggested_role": "<Role>", and "certainty": "<Certainty Level>".

### Suspicious Behavior Detection Rules

In addition to identifying the action, analyze the message for any signs of suspicious behavior. If suspicious behavior is detected, add a "suspicious" field with "flagged": true, a "summary", and "details" explaining the suspicion. Use the following rules to identify suspicious behavior:

1. **Mimicking Moderator Messages**: If a player’s message contains phrasing typically used by the moderator (e.g., "lynched," "role," "You are the Seer"), flag it as suspicious.
   - Example: "summary": "Player message contains moderator-style phrasing."

2. **Using Ambiguous Language**: If the player’s message includes uncertain language (e.g., "I think," "maybe," "might be") while claiming a role, flag it as suspicious.
   - Example: "summary": "Player used ambiguous phrasing in role claim."

3. **Altering Round Numbers or Role Terms**: If the player uses unexpected terms or altered spelling (e.g., "Sear" instead of "Seer") or provides an improbable round number, flag it as suspicious.
   - Example: "summary": "Unusual role spelling or unexpected round number."

4. **Claiming Multiple Conflicting Roles**: If a player has previously claimed a role that conflicts with the current claim, flag it as suspicious.
   - Example: "summary": "Player has conflicting role claims."

5. **Repeating Claims with Minor Variations**: If a player makes multiple similar claims with slight differences (e.g., claiming to have checked different players with the same result), flag it as suspicious.
   - Example: "summary": "Player made multiple similar claims with slight variations."

6. **Confusing Vote Messages**: If a player’s vote message is unclear or contains non-standard wording (e.g., "I vote for Player X to save"), flag it as suspicious.
   - Example: "summary": "Vote message contains non-standard wording."

7. **Making Contradictory Statements**: If a player’s statements contradict each other across messages (e.g., first claiming to have checked Player X, then denying it), flag it as suspicious.
   - Example: "summary": "Player made contradictory statements."

8. **Using Excessive Emphasis or Characters**: If a message includes unusual capitalization, multiple exclamation marks, or excessive special characters, flag it as suspicious.
   - Example: "summary": "Message contains excessive emphasis."

9. **Fake Voting Patterns**: If a player rapidly changes their vote multiple times or exhibits unusual voting behavior, flag it as suspicious.
   - Example: "summary": "Player exhibited unusual voting behavior."

Input: $user_message

### Expected JSON Output

If the message matches one of the actions above, return it in JSON format, for example:
- {"action": "record_vote", "from_player_name": "Player A", "voted_player_name": "Player B" }
- {"action": "claim_seer", "player_name": "Player C" }
- {"action": "claim_doctor", "player_name": "Player D" }
- {"action": "claim_checked", "player_name": "Player E", "player_checked_name": "Player F", "player_role": "Villager", "round_checked": 3 }
- {"action": "claim_saved", "player_name": "Player G", "saved_player_name": "Player H", "round_saved": 2 }
- {"action": "player_suggests", "player_name": "Player I", "player_suggested_name": "Player J", "suggested_role": "Werewolf", "certainty": "High" }

If suspicious behavior is detected, add a "suspicious" field, for example:

{
  "action": "record_vote",
  "from_player_name": "Player A",
  "voted_player_name": "Player B",
  "suspicious": {
    "flagged": True,
    "summary": "Player message contains moderator-style phrasing.",
    "details": "Player A used phrasing similar to moderator messages, which may be an attempt to confuse other players."
  }
}

Please note there may be multiple actions, each one should be represented in it's own JSON, but make sure not to duplicate actions. If there is no explicit player action, you do not need to include the action field.
Return only the JSON Outputs as a list and nothing else [{
""")