import argparse
import logging
import os

import spotipy

from spotipy.oauth2 import SpotifyClientCredentials
from telegram import Update, ForceReply, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

GENRE, ARTIST, ALBUM, TRACK, SEARCH = range(5)


def help_command(update: Update, _: CallbackContext) -> None:
    update.message.reply_text('I DON\'T UNDERSTAND U, PLZ SEND /help WAN MOAR TIEM')


def start(update: Update, context: CallbackContext) -> None:
    context.user_data['r'] = {}
    context.user_data['d'] = {}
    reply_keyboard = [['/GetMusic', '/GetRecommended']]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)

    update.message.reply_text("OH HAI! IM AUDIO BOT. I CAN HALP U WIF MUSIC SEARCH. PLZ, CHOOSE, WUT DO U WANTS:"
                              "GIT RECOMMENDD MUSIC BY EXAMPLE TRACK OR ARTIST:"
                              "GIT SIMPLE MUSIC SEARCH BY GENRE, ARTIST, ALBUM AN TRACK", reply_markup=markup)


def start3(update: Update, _: CallbackContext) -> int:
    update.message.reply_text(
        'PLZ, SEND ARTIST OR SUM ARTISTZ, AT FURST'
    )

    return ARTIST


def artist_rec(update: Update, context: CallbackContext) -> int:
    context.user_data['r']['artist'] = update.message.text.split(',')
    update.message.reply_text('NAO, PLZ SEND ME TRACK OR SUM TRACKZ')

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
            update.message.reply_text('UR ARTIST BRO : ' + i['artists'][0]['name'] + '\n' + 'UR TRACK BRO : ' + i['name'] + '\n' + 'UR SAMPLE BRO : ' + i['preview_url'] + '\n' + 'UR LINK BRO : ' + i['external_urls']['spotify'])
    context.user_data['r'] = {}
    context.user_data['d'] = {}

    return ConversationHandler.END


def start2(update: Update, _: CallbackContext) -> int:
    update.message.reply_text(
        'PLZ SEND ME GENRE OR SEND /skip IF U DON\'T WANTS 2.'
    )

    return GENRE


def genre(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("Genre of %s: %s", user.first_name, update.message.text)
    context.user_data['d']['genre'] = update.message.text
    update.message.reply_text(
        'PLZ SEND ME ARTIST OR SEND /skip IF U DON\'T WANTS 2.'
    )

    return ARTIST


def skip_genre(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s did not send a genre.", user.first_name)
    context.user_data['d']['genre'] = 0
    update.message.reply_text(
        'NAO, SEND ME ARTIST PLZ, OR SEND /skip.'
    )

    return ARTIST


def artist(update: Update, context: CallbackContext) -> int:
    context.user_data['d']['artist'] = update.message.text
    update.message.reply_text('NICE! SEND ME ALBUM PLZ, OR SEND /skip IF U DON\T WANTS 2.')
    return ALBUM


def skip_artist(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s did not send a album.", user.first_name)
    context.user_data['d']['artist'] = 0
    update.message.reply_text(
        'NAO, SEND ME ALBUM PLZ, OR SEND /skip.'
    )

    return ALBUM


def album(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    context.user_data['d']['album'] = update.message.text
    logger.info(
        "Album of %s: %f / %f", user.first_name,  update.message.text)
    update.message.reply_text(
        'AT LAST, PLZ, SEND TRACK'
    )

    return TRACK


def skip_album(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    context.user_data['d']['album'] = 0
    logger.info("User %s did not send album.", user.first_name)
    update.message.reply_text(
        'I C, SEND ME TRACK PLZ OR SEND /skip'
    )

    return TRACK


def track(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Track of %s: %s", user.first_name,  update.message.text)
    context.user_data['d']['track'] = update.message.text

    return search(update, context)


def skip_track(update: Update, context: CallbackContext):
    context.user_data['d']['track'] = 0

    return search(update, context)


def cancel(update: Update, context: CallbackContext):
    context.user_data['r'] = {}
    context.user_data['d'] = {}
    update.message.reply_text(
        'BAI! I HOPE WE CAN TALK AGAIN SUM DAI.', reply_markup=ReplyKeyboardRemove()
    )

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
            update.message.reply_text('UR TRACK BRO : ' + i['name'] + '\n' + 'UR SAMPLE BRO : ' + i['preview_url'] +
                                      '\n' + 'YUR LINK BRO : ' + i['external_urls']['spotify'])
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
        artist = get_artist(context.args[0])
        spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
        results = spotify.recommendations(seed_artists=[artist])
        logger.info(results)
        update.message.reply_text('Recommendations for ' + artist['name'] + ":")
        for track_rec in results['tracks']:
            update.message.reply_text(track_rec['artists'][0]['name'])
    else:
        update.message.reply_text("vvedi artista ebantyay")


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(os.environ['TOKEN'])

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("rec", show_recommendations_for_artist))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("GetMusic", start2)],
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
        entry_points=[CommandHandler("GetRecommended", start3)],
        states={
            ARTIST: [MessageHandler(Filters.text & ~Filters.command, artist_rec), CommandHandler("skip", skip_artist)],
            TRACK: [MessageHandler(Filters.text & ~Filters.command, track_rec), CommandHandler("skip", skip_track)],
            SEARCH: [get_recommendations],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(conv_handler2)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
