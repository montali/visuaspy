import json
import codecs
import datetime
import os.path
import logging
import argparse
import telegram.ext
from telegram.ext import Updater
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram import (User, Message, Update, Chat, ChatMember, UserProfilePhotos, File,
                      ReplyMarkup, TelegramObject, WebhookInfo, GameHighScore, StickerSet,
                      PhotoSize, Audio, Document, Sticker, Video, Animation, Voice, VideoNote,
                      Location, Venue, Contact, InputFile, ParseMode, KeyboardButton, ReplyKeyboardMarkup,
                      InlineKeyboardButton, ChatAction, Bot, CallbackQuery, InlineKeyboardMarkup, ForceReply)
try:
    from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)


def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def from_json(json_object):
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object


def onlogin_callback(api, new_settings_file):
    cache_settings = api.settings
    with open(new_settings_file, 'w') as outfile:
        json.dump(cache_settings, outfile, default=to_json)
        print('SAVED: {0!s}'.format(new_settings_file))


def start (update, context):
    print(update.message.chat_id)
    context.bot.send_message(chat_id=update.message.chat_id, text="Correctly printed your chat ID\n")
    


#updater.idle()

if __name__ == '__main__':

    logging.basicConfig()
    logger = logging.getLogger('instagram_private_api')
    logger.setLevel(logging.WARNING)

    # Example command:
    # python examples/savesettings_logincallback.py -u "yyy" -p "zzz" -settings "test_credentials.json"
    parser = argparse.ArgumentParser(description='login callback and save settings demo')
    parser.add_argument('-settings', '--settings', dest='settings_file_path', type=str, required=True)
    parser.add_argument('-u', '--username', dest='username', type=str, required=True)
    parser.add_argument('-p', '--password', dest='password', type=str, required=True)
    parser.add_argument('-t', '--token', dest='token', type=str)
    parser.add_argument('-c', '--chat', dest='chat', type=str)


    parser.add_argument('-debug', '--debug', action='store_true')
    args = parser.parse_args()
    if(args.token != None):
        updater = Updater(token=args.token, use_context=True)
        dispatcher = updater.dispatcher
        dispatcher.add_handler(CommandHandler("start", start))
        updater.start_polling()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    print('Client version: {0!s}'.format(client_version))

    device_id = None
    try:

        settings_file = args.settings_file_path
        if not os.path.isfile(settings_file):
            # settings file does not exist
            print('Unable to find file: {0!s}'.format(settings_file))

            # login new
            api = Client(
                args.username, args.password,
                on_login=lambda x: onlogin_callback(x, args.settings_file_path))
        else:
            with open(settings_file) as file_data:
                cached_settings = json.load(file_data, object_hook=from_json)
            print('Reusing settings: {0!s}'.format(settings_file))

            device_id = cached_settings.get('device_id')
            # reuse auth settings
            api = Client(
                args.username, args.password,
                settings=cached_settings)

    except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
        print('ClientCookieExpiredError/ClientLoginRequiredError: {0!s}'.format(e))

        # Login expired
        # Do relogin but use default ua, keys and such
        api = Client(
            args.username, args.password,
            device_id=device_id,
            on_login=lambda x: onlogin_callback(x, args.settings_file_path))

    except ClientLoginError as e:
        print('ClientLoginError {0!s}'.format(e))
        exit(9)
    except ClientError as e:
        print('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response))
        exit(9)
    except Exception as e:
        print('Unexpected Exception: {0!s}'.format(e))
        exit(99)

    # Show when login expires
    cookie_expiry = api.cookie_jar.auth_expires
    print('Cookie Expiry: {0!s}'.format(datetime.datetime.fromtimestamp(cookie_expiry).strftime('%Y-%m-%dT%H:%M:%SZ')))
    saved_stalkers = {}
    if not os.path.isfile('stalkers.json'):
        with open ('stalkers.json', 'w+') as newFile:
            newFile.write('{}')
        print("stalkers.json not existing. Creating it.")
#    saved_stalkers = [line.rstrip('\n') for line in open('stalkers.txt')]
    with open("stalkers.json", "r") as stalkersFile:
        saved_stalkers = json.load(stalkersFile)
    print(saved_stalkers)
    story_feed = api.user_story_feed(api.authenticated_user_id)
    my_feed = story_feed.get('reel', [])
    uuid = api.generate_uuid()
    my_followers = []
    followers_result = api.user_followers(api.authenticated_user_id, uuid)
    my_followers.extend(followers_result['users'])
    last_id = followers_result['next_max_id']
    while (last_id != None):
        followers_result = api.user_followers(api.authenticated_user_id, uuid, max_id = last_id)
        my_followers.extend(followers_result['users'])
        last_id = followers_result['next_max_id']
    my_followers_ids = []
    for follower in my_followers:
        my_followers_ids.append(follower['pk'])
    for stor in my_feed.get('items', []):
        # If we find a stalker, we'll want to save the story ID too. This lets us check if a user re-spies us.
        viewers_result = api.story_viewers(stor.get('id', []))
        story_viewers = viewers_result['users']
        last_id = viewers_result['next_max_id']
        while (last_id != None):
            viewers_result = api.story_viewers(stor.get('id', []), max_id = last_id)
            story_viewers.extend(viewers_result['users'])
            last_id = viewers_result['next_max_id']
        for stalker in story_viewers:
            if (not stalker['friendship_status']['following']):
                if not stalker['pk'] in my_followers_ids:
                    user_info = api.user_info(stalker['pk'])
                    if (user_info['user']['mutual_followers_count']>1):
                        if(args.token != None):
                            # Check if the stalker is found in the saved ones: if so, check if the story we're checking was already there.
                            if user_info['user']['username'] in saved_stalkers:
                                if not stor.get('id', []) in saved_stalkers[user_info['user']['username']]["stories"]:
                                    updater.bot.send_photo(chat_id=args.chat, photo = user_info['user']['profile_pic_url'], caption="Found a stalker!\n" + "Username: "+user_info['user']['username']+"\nFull name: "+user_info['user']['full_name']+"\nFollowers: "+str(user_info['user']['follower_count'])+"\nFollowing: "+str(user_info['user']['following_count'])+"\nURL: http://instagram.com/"+str(user_info['user']['username']))
                                    saved_stalkers[user_info['user']['username']]["stories"].append(stor.get('id', []))
                            #else:
                                #updater.bot.send_photo(chat_id=args.chat, photo = user_info['user']['profile_pic_url'], caption="Found a recessive stalker!\n" + "Username: "+user_info['user']['username']+"\nFull name: "+user_info['user']['full_name']+"\nFollowers: "+str(user_info['user']['follower_count'])+"\nFollowing: "+str(user_info['user']['following_count'])+"\nURL: http://instagram.com/"+str(user_info['user']['username']))
                             #   saved_stalkers[user_info['user']['username']] = {}
                               # saved_stalkers[user_info['user']['username']]["stories"] = []
                                #saved_stalkers[user_info['user']['username']]["stories"].append(stor.get('id', []))
                        else:
                            if not user_info['user']['username'] in saved_stalkers:
                                print("Found a stalker!\n" + "Username: "+user_info['user']['username']+"\nFull name: "+user_info['user']['full_name']+"\nFollowers: "+str(user_info['user']['follower_count'])+"\nFollowing: "+str(user_info['user']['following_count']))
                                saved_stalkers[user_info['user']['username']]["stories"].append(stor.get('id', []))
    print(saved_stalkers)
    # Saving and closing
    with open('stalkers.json', 'w') as stalkers_file:
        json.dump(saved_stalkers, stalkers_file)

    if (args.token!=None):
        updater.stop()
        updater.is_idle = False
    print('All ok')


