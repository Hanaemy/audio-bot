import argparse
import logging
import os

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

GENRE, ARTIST, ALBUM, TRACK, SEARCH = range(5)


def help_command(update: Update, _: CallbackContext) -> None:
    update.message.reply_text('Если что-то пошло не так - отправьте /cancel и попробуйте еще раз. Извините, я работаю над тем, чтобы это исправить.'
                              ' Если это не сработало - напишите мне об этом @Hanaemy, и я постараюсь помочь вам как можно скорее.'
                              ' Так же, пожалуйста, не используйте русский язык в запросах - Spotify плохо его понимает,'
                              ' если вам нужен русский исполнитель - напишите транслитом.')


def start(update: Update, context: CallbackContext) -> None:
    context.user_data['r'] = {}
    context.user_data['d'] = {}
    reply_keyboard = [['/getmusic', '/getrecommended'], ['/help', '/cancel']]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)

    update.message.reply_text("Привет, я Аудио Бот, я помогу тебе подобрать музыку,"
                              " пожалуйста, выбери, что бы ты хотел:"
                              " /getrecommended - подобрать несколько треков, основываясь на выбранном артисте"
                              " или нескольких артистах, а так же треке или нескольким трекам"
                              " /getmusic поиск музыки по жанру, исполнителю, альбому и треку."
                              " Если нужна помощь - нажми /help."
                              " Если что-то пошло не так или ты просто передумал - нажми /cancel, чтобы завершить текущую операцию."
                              " Пожалуйста, используйте в запросах английский язык или напишите translitom", reply_markup=markup)


def getrecommended(update: Update, _: CallbackContext) -> int:
    update.message.reply_text(
        'Пожалуйста, введи исполнителя или нескольких исполнителей, через запятую'
    )

    return ARTIST


def artist_rec(update: Update, context: CallbackContext) -> int:
    context.user_data['r']['artist'] = update.message.text.split(',')
    update.message.reply_text('Теперь введи трек или несколько треков, через запятую')

    return TRACK


def track_rec(update: Update, context: CallbackContext):
    context.user_data['r']['track'] = update.message.text.split(',')

    return get_recommendations(update, context)


def get_recommendations(update: Update, context: CallbackContext):
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
    ids = {'artist': [], 'track': []}

    for i in range(0, len(context.user_data['r']['artist'])):
        if len(context.user_data['r']['artist']) + len(context.user_data['r']['track']) > 5:
            if len(ids['artist']) >= 2:
                break
        ids['artist'].append(get_artist(context.user_data['r']['artist'][i]))

    for i in range(0, len(context.user_data['r']['track'])):
        if len(context.user_data['r']['artist']) + len(context.user_data['r']['track']) > 5:
            if len(ids['track']) >= 2:
                break
        ids['track'].append(get_track(context.user_data['r']['track'][i]))

    results = spotify.recommendations(seed_tracks=ids['track'], seed_artists=ids['artist'], limit=10)

    items = results['tracks']

    for i in items:
        if type(i['preview_url']) is str and type(i['external_urls']['spotify']) is str:
            update.message.reply_text('Исполнитель : ' + i['artists'][0]['name'] + '\n' + 'Трек : ' +
                                      i['name'] + '\n' + 'Сэмпл : ' + i['preview_url'] + '\n'
                                      + 'Ссылка на трек : ' + i['external_urls']['spotify'])
    context.user_data['r'] = {}
    context.user_data['d'] = {}

    return ConversationHandler.END


def getmusic(update: Update, _: CallbackContext) -> int:
    update.message.reply_text(
        'Пожалуйста, введи жанр или нажми /skip, чтобы пропустить этот шаг.'
    )

    return GENRE


def genre(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("Genre of %s: %s", user.first_name, update.message.text)
    context.user_data['d']['genre'] = update.message.text
    update.message.reply_text(
        'Пожалуйста, введи исполнителя или нажми /skip, чтобы пропустить этот шаг.'
    )

    return ARTIST


def skip_genre(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s did not send a genre.", user.first_name)
    context.user_data['d']['genre'] = 0
    update.message.reply_text(
        'Пожалуйста, введи исполнителя или нажми /skip, чтобы пропустить этот шаг.'
    )

    return ARTIST


def artist(update: Update, context: CallbackContext) -> int:
    context.user_data['d']['artist'] = update.message.text
    update.message.reply_text('Пожалуйста, введи альбом или нажми /skip, чтобы пропустить этот шаг.')
    return ALBUM


def skip_artist(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s did not send a album.", user.first_name)
    context.user_data['d']['artist'] = 0
    update.message.reply_text(
        'Пожалуйста, введи альбом или нажми /skip, чтобы пропустить этот шаг.'
    )

    return ALBUM


def album(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    context.user_data['d']['album'] = update.message.text
    logger.info(
        "Album of %s: %f / %f", user.first_name,  update.message.text)
    update.message.reply_text(
        'Пожалуйста, введи название трека'
    )

    return TRACK


def skip_album(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    context.user_data['d']['album'] = 0
    logger.info("User %s did not send album.", user.first_name)
    update.message.reply_text(
        'Пожалуйста, введи название трека или нажми /skip, чтобы пропустить этот шаг.'
    )

    return TRACK


def track(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Track of %s: %s", user.first_name,  update.message.text)
    context.user_data['d']['track'] = update.message.text

    return search(update, context)


def skip_track(update: Update, context: CallbackContext):
    context.user_data['d']['track'] = 0
    update.message.reply_text('You send nothing - you get nothing')
    return search(update, context)


def cancel(update: Update, context: CallbackContext):
    context.user_data['r'] = {}
    context.user_data['d'] = {}
    update.message.reply_text('Пока! Буду рад помочь тебе снова!', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def search(update: Update, context: CallbackContext):
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
    q = ''

    if context.user_data['d']['genre'] == 0:
        genre = ''
    else:
        genre = context.user_data['d']['genre']
        q = q + 'genre:' + genre

    if context.user_data['d']['artist'] == 0:
        artist = ''
    else:
        artist = context.user_data['d']['artist']
        q = q + ' artist:' + artist

    if context.user_data['d']['album'] == 0:
        album = ''
    else:
        album = context.user_data['d']['album']
        q = q + ' album:' + album

    if context.user_data['d']['track'] == 0:
        track = ''
    else:
        track = context.user_data['d']['track']
        q = q + ' track:' + track

    print(q)

    results = spotify.search(q=q, type='track', limit=10)

    print(results)

    items = results['tracks']['items']

    for i in items:
        if type(i['preview_url']) is str and type(i['external_urls']['spotify']) is str:
            update.message.reply_text('Трек : ' + i['name'] + '\n' + 'Сэмпл : ' + i['preview_url'] +
                                      '\n' + 'Ссылка на трек в Spotify : ' + i['external_urls']['spotify'])
    context.user_data['r'] = {}
    context.user_data['d'] = {}

    return ConversationHandler.END


def get_args():
    parser = argparse.ArgumentParser(description='Recommendations for the '
                                     'given artist')
    parser.add_argument('-a', '--artist', required=True, help='Name of Artist')
    return parser.parse_args()


def get_artist(name):
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
    results = spotify.search(q='artist:' + name, type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        return items[0]['id']
    else:
        return None


def get_track(name):
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
    results = spotify.search(q='track:' + name, type='track')
    print(results)
    items = results['tracks']['items']
    if len(items) > 0:
        return items[0]['id']
    else:
        return None


def show_recommendations_for_artist(update: Update, context: CallbackContext):

    if len(context.args) > 0:
        artist_recom = get_artist(context.args[0])
        spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
        results = spotify.recommendations(seed_artists=[artist_recom])
        logger.info(results)
        update.message.reply_text('Recommendations for ' + artist_recom['name'] + ":")
        for track_recom in results['tracks']:
            update.message.reply_text(track_recom['artists'][0]['name'])
    else:
        update.message.reply_text("vvedi artista ebantyay")


def main() -> None:
    updater = Updater(os.environ['TOKEN'])

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("rec", show_recommendations_for_artist))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("getmusic", getmusic)],
        states={
            GENRE: [MessageHandler(Filters.text & ~Filters.command, genre), CommandHandler("skip", skip_genre)],
            ARTIST: [MessageHandler(Filters.text & ~Filters.command, artist), CommandHandler("skip", skip_artist)],
            ALBUM: [MessageHandler(Filters.text & ~Filters.command, album), CommandHandler("skip", skip_album)],
            TRACK: [MessageHandler(Filters.text & ~Filters.command, track), CommandHandler("skip", skip_track)],
            SEARCH: [search],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    conv_handler2 = ConversationHandler(
        entry_points=[CommandHandler("getrecommended", getrecommended)],
        states={
            ARTIST: [MessageHandler(Filters.text & ~Filters.command, artist_rec), CommandHandler("skip", skip_artist)],
            TRACK: [MessageHandler(Filters.text & ~Filters.command, track_rec), CommandHandler("skip", skip_track)],
            SEARCH: [get_recommendations],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(conv_handler2)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
