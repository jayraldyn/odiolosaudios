import json
import os
import sys

here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "./vendored"))

import requests
import telebot
import boto3
import speech_recognition as sr

TOKEN = os.environ['TELEGRAM_TOKEN']
BASE_URL = "https://api.telegram.org/bot{}".format(TOKEN)
permitidos = ['XXXXX', 'YYYYY']
FFMPEG = "/opt/ffmpeg/ffmpeg"

bot = telebot.TeleBot(TOKEN)

# ----------------------------------------------------------------------------------------------------
# Comunes
# ----------------------------------------------------------------------------------------------------

def check_permitido(func):

    def inner(message):
        if message.from_user.username in permitidos:
            return func(message)
        else:
            bot.reply_to(message, 'Lo siento, este bot sólo lo pueden usar determinadas personas. Si quieres ser una de ellas, habla con @XXXXX')
            print("Intento de acceso del usuario " + message.from_user.username + " bloqueado.")
            return
    return inner

# ----------------------------------------------------------------------------------------------------
# SSM
# ----------------------------------------------------------------------------------------------------

def _get_lang_ssm():

    ssm = boto3.client('ssm')
    try:
        parameter = ssm.get_parameter(Name='/odiolosaudios/lang_config')
        config_string = parameter['Parameter']['Value']
    except:
        print("Error, suponemos que el parámetro no existe")
        config_string = "{}"
    config_json = json.loads(config_string)
    return config_json

def _set_lang_ssm(config_json):

    ssm = boto3.client('ssm')
    try:
        ssm.put_parameter(Name='/odiolosaudios/lang_config', Value=json.dumps(config_json), Type='String', Overwrite=True)
    except Exception as e:
        print("Error al guardar el parámetro, excepción: " + str(e))
    return

def get_lang_ssm(usuario):

    config_json = _get_lang_ssm()
    if usuario in config_json:
        return config_json[usuario]
    else:
        return "es-ES"

def set_lang_ssm(usuario, idioma):

    config_json = _get_lang_ssm()
    config_json[usuario] = idioma
    _set_lang_ssm(config_json)
    return

# ----------------------------------------------------------------------------------------------------
# Hooks mensajes
# ----------------------------------------------------------------------------------------------------

def tratar_audio(message):

    try:
        file_info = bot.get_file(message.audio.file_id)
        nombre_fichero = "/tmp/" + message.audio.file_name
        file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(TOKEN, file_info.file_path), allow_redirects=True)
        open(nombre_fichero, 'wb').write(file.content)

        # Llamar a ffmpeg para convertir a WAV
        wav = nombre_fichero + ".wav"
        os.system(FFMPEG + " -y -i '" + nombre_fichero + "' -vn '" + wav + "'")

        print("WAV creado, llamo al recognizer")
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav) as source:
            ad = recognizer.record(source)
            texto = recognizer.recognize_google(ad, language=get_lang_ssm(message.from_user.username))
            bot.reply_to(message, texto)
        print("Todo OK, borro los ficheros")

        os.system("rm " + nombre_fichero)
        os.system("rm " + wav)
    except:
        print("Algo raro ha sucedido, no puedo traducir el audio")
        bot.reply_to(message, "Lo siento, algo raro ha pasado y no puedo leer el audio.")
    return

def cambio_idioma(message):

    # Primero informar del idioma del usuario
    try:
        print ("Cambio idioma, usuario " + message.from_user.username)
        lang = get_lang_ssm(message.from_user.username)
        bot.send_message(message.chat.id, "Tu idioma actual es " + lang)
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton('Castellano', callback_data='set_castellano'),
            telebot.types.InlineKeyboardButton('Català', callback_data='set_catala')
        )
        bot.send_message(message.chat.id, 'Elige el idioma', reply_markup=keyboard)
    except Exception as e:
        print("Error al intentar cambiar de idioma: " + str(e))
    return

# ----------------------------------------------------------------------------------------------------------------
# Tratamiento de los mensajes
# ----------------------------------------------------------------------------------------------------------------

@check_permitido
def mensaje_texto(message):

    # Comprobar si se trata de un comando
    if message.text == "/start":
        bot.reply_to(message, '¡ Hola hola ! Envíame audios y los leeré para tí')
    if message.text == "/lang":
        cambio_idioma(message)
    return

@check_permitido
def mensaje_audio(message):

    tratar_audio(message)
    return

# ----------------------------------------------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------------------------------------------

def telegram_bot(event, context):

    if 'body' in event:
        update = telebot.types.Update.de_json(event['body'])

        try:
            if update.message is not None:
                if update.message.text is not None:
                    mensaje_texto(update.message)
                elif update.message.audio is not None:
                    mensaje_audio(update.message)
            elif update.callback_query is not None:
                if update.callback_query.data == 'set_catala':
                    set_lang_ssm(update.callback_query.from_user.username, 'ca-ES')
                    bot.send_message(update.callback_query.message.chat.id, 'Idioma canviat a català')
                elif update.callback_query.data == 'set_castellano':
                    set_lang_ssm(update.callback_query.from_user.username, 'es-ES')
                    bot.send_message(update.callback_query.message.chat.id, 'Idioma cambiado a castellano')
            else:
                print ("Tipo de mensaje no soportado")
                print (json.dumps(update.message))
                bot.reply_to(update.message, 'Lo siento, aquí sólo nos interesan comandos o audios')
        except Exception as e:
            bot.reply_to(update.message, 'Lo siento, algo ha salido mal: ' + str(e))

    return {"statusCode": 200}
