import json
import os
import sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "./vendored"))
import requests
import time
import boto3
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

PUBLIC_KEY = os.environ['DISCORD_TOKEN']
HTTP_KEY = os.environ['DISCORD_BOT_HTTP']
OPENAI_PROCESSOR_ARN = os.environ['OPENAI_PROCESSOR_ARN']

def get_channel_id(payload):
	if 'channel_id' in payload:
		return payload['channel_id']
	return ""

def get_sender_username(payload):
		if 'member' in payload and 'user' in payload['member']:
				user = payload['member']['user']
				if 'username' in user:
						return user['username']
		return ""

def verify_signature(headers, body):
	signature = headers['x-signature-ed25519']
	timestamp = headers['x-signature-timestamp']

	verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
	message = timestamp.encode() + body.encode()

	try:
		verify_key.verify(message, bytes.fromhex(signature))
		return True
	except BadSignatureError:
		return False

def handler(event, context):
	try:
		headers = {k.lower(): v for k, v in event['headers'].items()}
		body = event['body']
		if not verify_signature(headers, body):
			return {'statusCode': 401, 'headers': {'Content-Type': 'text/plain'},'body': 'Invalid request signature'}

		body = json.loads(body)
		t = body['type']
		if t == 1:
			return {
				'statusCode': 200,
				'headers': {'Content-Type': 'application/json'},
				'body': json.dumps({'type': 1})
			}
		elif t == 2:
			channel_id = get_channel_id(body)
			first_name = get_sender_username(body)
			prompt_message = next(option for option in body['data']['options'] if option['name'] == 'text')
			prompt_message = prompt_message['value']
			lambda_client = boto3.client('lambda')
			lambda_payload = {"message": prompt_message, "channel_id": channel_id, "http_key": HTTP_KEY, "interaction_token": body["token"]}
			lambda_client.invoke(
					 FunctionName=OPENAI_PROCESSOR_ARN, 
					 InvocationType='Event',
					 Payload=json.dumps(lambda_payload)
					)
			return {
				'statusCode': 200,
				'headers': {'Content-Type': 'application/json'},
				'body': json.dumps({'type': 4, 'data': {'content': first_name + ": " + prompt_message}})
			}
		else:
			return {
				'statusCode': 400,
				'headers': {'Content-Type': 'text/plain'},
				'body': json.dumps('unhandled request type')
			}
	except:
		raise
