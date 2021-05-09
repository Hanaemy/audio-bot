import logging
import string
from email.mime import audio
from lib2to3.fixes.fix_input import context

import spotipy, base64, json

from spotipy.oauth2 import SpotifyClientCredentials
from telegram import Update, ForceReply, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

GENRE, ARTIST, ALBUM, TRACK, SEARCH = range(5)

d = {}

# Define a few command handlers. These usually take the two arguments update and
# context.
#def start(update: Update, _: CallbackContext) -> None:
#    """Send a message when the command /start is issued."""
#    user = update.effective_user
#    update.message.reply_markdown_v2(
#        f'Hi {user.mention_markdown_v2()}\!',
#        reply_markup=ForceReply(selective=True),
#    )


def help_command(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Пийшов нахуй')


def echo(update: Update, _: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def test(update: Update, context: CallbackContext) -> None:
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
    artist = context.args[0]
    results = spotify.search(q='artist:' + artist, type='artist', limit=2)
    items = results['artists']['items']

    update.message.reply_text(items)
    update.message.reply_text(spotify.me())


    #while results['next']:
     #   results = spotify.next(results)
      #  albums.extend(results['items'])
    #for album in albums:
     #   update.message.reply_text(album['name'])


def start2(update: Update, _: CallbackContext) -> int:
    #reply_keyboard = [['Rock', 'Rap']]

    update.message.reply_text(
        'Hi! My name is Audio Bot. I will help you find music. '
        'Please send me a genre or send /skip if you don\'t want to.'#,
        #reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return GENRE


def genre(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("Genre of %s: %s", user.first_name, update.message.text)
    d['genre'] = update.message.text
    update.message.reply_text(
        'I see! Please send me a artist or send /skip if you don\'t want to.'#,
       # reply_markup=ReplyKeyboardRemove(),
    )

    return ARTIST


def skip_genre(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s did not send a genre.", user.first_name)
    d['genre'] = 0
    update.message.reply_text(
        'Now, send me artist please, or send /skip.'
    )

    return ARTIST


def artist(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    #spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
    #album = context.args[0]
    d['artist'] = update.message.text
    #results = spotify.search(q='album:' + album, type='album', limit=2)
    #items = results['albums']['items']
    logger.info("Album of %s: %s", user.first_name)
    update.message.reply_text('Gorgeous! Now, send me album please, or send /skip if you don\'t want to.')


    #update.message.reply_text(items)
    #update.message.reply_text(spotify.me())

    return ALBUM


def skip_artist(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s did not send a album.", user.first_name)
    d['artist'] = 0
    update.message.reply_text(
        'Now, send me album please, or send /skip.'
    )

    return ALBUM


def album(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    d['album'] = update.message.text
    logger.info(
        "Album of %s: %f / %f", user.first_name,  update.message.text)
    update.message.reply_text(
        'Please, send a track'
    )

    return TRACK


def skip_album(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    d['album'] = 0
    logger.info("User %s did not send album.", user.first_name)
    update.message.reply_text(
        'You seem a bit paranoid! At last, send me a track or send /skip'
    )

    return TRACK


def track(update: Update, _: CallbackContext):
    user = update.message.from_user
    logger.info("Track of %s: %s", user.first_name,  update.message.text)
    d['track'] = update.message.text

    return search(update, _)


def skip_track(update: Update, _: CallbackContext):
    user = update.message.from_user
    d['track'] = 0
    logger.info("User %s did not send album.", user.first_name)
    update.message.reply_text(
        'Screw you guys, Im going home.'
    )

    return search(update, _)


def cancel(update: Update, _: CallbackContext):
    user = update.message.from_user
    logger.info("User %s canceled the search.", user.first_name,  update.message.text)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def search(update: Update, _: CallbackContext):
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
    #genre = str_replace(d['genre'])
    #q = 'genre:' + genre
    q = ''

    if d['genre'] == 0:
        genre = ''
    else:
        genre = d['genre']
        q = q + 'genre:' + genre

    if d['artist'] == 0:
        artist = ''
    else:
        artist = d['artist']
        q = q + ' artist:' + artist

    if d['album'] == 0:
        album = ''
    else:
        album = d['album']
        q = q + ' album:' + album

    if d['track'] == 0:
        track = ''
    else:
        track = d['track']
        q = q + ' track:' + track

    print(q)

    results = spotify.search(q=q, type='track', limit=1)

    print(results)

    items = results['tracks']['items']

    for i in items:
        if type(i['preview_url']) is str and type(i['external_urls']['spotify']) is str:
            update.message.reply_text('track : ' + i['name'] + '\n' + 'sample : ' + i['preview_url'] + '\n' + 'link : ' + i['external_urls']['spotify'])

    return ConversationHandler.END

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("1746736800:AAEHr00Wfcm1BxiuYd5YcUSZsat6eOsUXn4")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    #dispatcher.add_handler(CommandHandler("start", start))
    #dispatcher.add_handler(CommandHandler("start2", start2))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("test", test))

    # on non command i.e message - echo the message on Telegram
    #dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start2", start2)],
        states={
            GENRE: [MessageHandler(Filters.text & ~Filters.command, genre), CommandHandler("skip", skip_genre)],
            ARTIST: [MessageHandler(Filters.text & ~Filters.command, artist), CommandHandler("skip", skip_artist)],
            ALBUM: [MessageHandler(Filters.text & ~Filters.command, album), CommandHandler("skip", skip_album)],
            TRACK: [MessageHandler(Filters.text & ~Filters.command, track), CommandHandler("skip", skip_track)],
            SEARCH: [search],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
