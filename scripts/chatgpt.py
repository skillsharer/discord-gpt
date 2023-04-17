import json
import os
import sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "./vendored"))
import requests
import time
import openai


def chunk_words(string, chunk_size):
	words = string.split()
	chunks = []
	chunk = ""
	for word in words:
		if len(chunk) + len(word) + 1 > chunk_size:
			chunks.append(chunk)
			chunk = ""
		if chunk:
			chunk += " "
		chunk += word
	chunks.append(chunk.strip("\n"))
	return chunks

def send_message_to_discord(message, channel_id, http_key):
	message_chunks = chunk_words(message, 1800)
	url = f'https://discord.com/api/channels/{channel_id}/messages'
	headers = {
		'Authorization': f'Bot {http_key}',
		'Content-Type': 'application/json',
	}
	for message_chunk in message_chunks:
		try:
			data = {'content': message_chunk}
			requests.post(url, headers=headers, json=data)
		except Exception as e:
			print("ERROR at send_message_to_discord: ", e)
		time.sleep(0.1)

def get_text(prompt):
	try:
		model_engine = os.environ['MODEL_ENGINE']
		mode = os.environ['MODE']
		
		if mode == 1:
			max_tokens = os.environ['MAX_TOKENS']
			completion = openai.Completion.create(
				engine=model_engine,
				prompt=prompt,
				max_tokens=max_tokens,
				n=1,
				stop=None,
				temperature=0.1,
			)

			response = completion.choices[0].text
			response = response.replace('\n', '')
		elif mode == 2:
			data = {
			  "model": "gpt-3.5-turbo",
			  "messages": [
				{"role": "user", "content": prompt}
			  ]
			}

			headers = {'Content-Type': 'application/json'}
			response = requests.post('https://chatgpt-api.shn.hk/v1/', headers=headers, data=json.dumps(data))
			response = json.loads(response.text)["choices"][0]["message"]["content"].replace('\n', '')
		else:
			data = {
			  "model": "gpt-3.5-turbo",
			  "messages": [
				{"role": "user", "content": prompt}
			  ]
			}

			headers = {'Content-Type': 'application/json', 'Authorization': "Bearer " + str(os.environ['OPENAI_API_KEY'])}
			response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, data=json.dumps(data))
			response = json.loads(response.text)["choices"][0]["message"]["content"].replace('\n', '')

	except Exception as e:
		print("WARN at get_text: ", e)
		response = ""

	return response

def answer_to_prompt(event, context):
	message = event['message']
	channel_id = event['channel_id']
	http_key = event['http_key']
	interaction_token = event['interaction_token']
	response = get_text(message)
	send_message_to_discord(response, channel_id, http_key)
	return {"statusCode": 200}
