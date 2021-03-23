import json

from pathlib import Path

import re
from functools import partial

fix_mojibake_escapes = partial(
	re.compile(rb'\\u00([\da-f]{2})').sub,
	lambda m: bytes.fromhex(m.group(1).decode()))

MESSAGE_JSON_PATTERN = 'message_*.json'
ME = 'Ofek Gila'
CONNECTED_MESSAGE = 'You are now connected on Messenger'
URI_MAP = {
	'messages/stickers_used/39178562_1505197616293642_5411344281094848512_n_369239263222822.png': '👍',
	'messages/stickers_used/851587_369239346556147_162929011_n_369239343222814.png': '👍',
	'messages/stickers_used/851582_369239386556143_1497813874_n_369239383222810.png': '👍',
	'messages/stickers_used/851577_246547505491999_862435009_n_227878347358915.png': '👍',
	'messages/stickers_used/851586_126361877548609_1351776047_n_126361874215276.png': '🙂',
	'messages/stickers_used/851575_126361970881933_2050936102_n_126361967548600.png': '😄',
	'messages/stickers_used/69979540_1554334978031524_4210588200999059456_n_526120230853009.png': 'LGTM',
	'messages/stickers_used/69999026_1554333024698386_411738139342667776_n_526120200853012.png': 'HOTFIX',
	'messages/stickers_used/851586_126362104215253_1651254063_n_126362100881920.png': '<3',
	'messages/stickers_used/10173489_298592853654247_1888832205_n_298592850320914.png': 'YAY!'
}


MILLISECONDS = 1
SECONDS = MILLISECONDS * 1000
MINUTES = SECONDS * 60
HOURS = MINUTES * 60
DAYS = 24 * HOURS

SOS_TOKEN = '<sos>'
EOS_TOKEN = '<eos>'
ME_TOKEN = '<me>'
OTHER_TOKEN = '<other>'


def get_dialogue_dict(directory_path: Path, max_participants: int = 2) -> { int: (bool, str) }:
	dialogue_dict = dict()

	for message_path in directory_path.glob(MESSAGE_JSON_PATTERN):
		with message_path.open('rb') as file:
			repaired = fix_mojibake_escapes(file.read())
			data = json.loads(repaired, strict = False)

			if len(data['participants']) > max_participants:
				continue

			for message in data['messages']:
				if 'sticker' in message and message['sticker']['uri'] in URI_MAP:
					message['content'] = URI_MAP[message['sticker']['uri']]

				if not 'content' in message or message['is_unsent']:
					continue

				if message['content'] == CONNECTED_MESSAGE:
					continue

				dialogue_dict[message['timestamp_ms']] = (message['sender_name'] == ME, message['content'])

	return dialogue_dict

def sort_dict(d: dict) -> dict:
	return {k: d[k] for k in sorted(d)}

def is_new_dialogue(last_timestamp: int, timestamp: int, max_message_delay_ms: int) -> bool:
	return last_timestamp < 0 or timestamp - last_timestamp > max_message_delay_ms

def get_speaker_token(is_me: bool) -> str:
	return ME_TOKEN if is_me else OTHER_TOKEN

def get_dialogues(directory_path: Path, max_participants: int = 2, max_message_delay_ms: int = 1 * HOURS) -> [[str]]:
	dialogue_dict = get_dialogue_dict(directory_path, max_participants)
	sorted_dialogue_dict = sort_dict(dialogue_dict)

	dialogues = list()
	last_timestamp = -1

	for timestamp, (is_me, message) in sorted_dialogue_dict.items():
		augmented_message = f'{get_speaker_token(is_me)} {message}'

		if is_new_dialogue(last_timestamp, timestamp, max_message_delay_ms):
			dialogues.append([augmented_message])
		else:
			dialogues[-1].append(augmented_message)

		last_timestamp = timestamp

	return dialogues

def get_all_dialogues(inbox_path: Path, max_participants: int = 2, max_message_delay_ms: int = 1 * HOURS) -> [[str]]:
	dialogues = list()

	for file in inbox_path.iterdir():
		if not file.is_dir():
			continue

		dialogues += get_dialogues(file, max_participants, max_message_delay_ms)

	return dialogues

if __name__ == '__main__':
	# print(get_dialogues(Path('/home/ofekih/Documents/chatbot/inbox/alanbrody_vegvneqdaw')))
	# dialogues = get_dialogues(Path('/home/ofekih/Downloads/messages/inbox/bryontjanaka_9q9h13dsta'))
	# print(dialogues[12])
	#
	dialogues = get_all_dialogues(Path('/home/ofekih/Downloads/messages/inbox/'))
	num_messages = sum((len(dialogue) for dialogue in dialogues))

	print(len(dialogues), num_messages)

