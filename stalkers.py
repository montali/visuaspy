'''
This python module looks for stalkers aka people who
look at your instagram stories but do not follow you.
'''
import argparse
import codecs
import json
import os.path
import sys

# TODO there has to be a better way of importing instagram_private_api
from telegram.ext import Updater, CommandHandler

try:
    from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)


def to_json(python_object):
    '''python-obj to json conversion'''
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def from_json(json_object):
    '''json to python-obj conversion'''
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object


def on_login(api, settings_path):
    '''create/refresh api settings'''
    cache_settings = api.settings
    with open(settings_path, 'w+') as settings:
        json.dump(cache_settings, settings, default=to_json)
        print('SAVED: {0}'.format(settings_path))


def start(update, context):
    '''reply to /start cmd'''
    print(update.message.chat_id)
    context.bot.send_message(chat_id=update.message.chat_id,
                             text="Correctly printed your chat ID\n")


class User:
    '''Generic instagram user'''
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.followers = []

    def set_followers(self, followers_dict):
        '''set followers given the dict'''
        for follower in followers_dict:
            self.followers.append(follower['pk'])


class StalkerFinder:
    '''
    Main class of the module, looks for stalkers and
    notify their presence via terminal or telegram
    '''
    def __init__(self):
        self.args = None
        self.setup_args()
        self.user = User(self.args.username, self.args.password)
        if self.args.token is not None:
            self.updater = Updater(token=self.args.token, use_context=True)
            dispatcher = self.updater.dispatcher
            dispatcher.add_handler(CommandHandler("start", start))
            self.updater.start_polling()
        self.user = User(self.args.username, self.args.password)
        self.settings_path = '{0}.json'.format(self.user.username)
        self.api = None
        self.device_id = None
        self.setup_api()
        self.stalkers = {}
        self.setup_stalkers()
        self.story = self.api.user_story_feed(self.api.authenticated_user_id).get('reel', [])

    def setup_args(self):
        '''Parse the given arguments'''
        parser = argparse.ArgumentParser()
        parser.add_argument('-u', '--username', dest='username', type=str, required=True)
        parser.add_argument('-p', '--password', dest='password', type=str, required=True)
        parser.add_argument('-t', '--token', dest='token', type=str)
        parser.add_argument('-c', '--chat', dest='chat', type=str)
        self.args = parser.parse_args()

    def setup_api(self):
        '''
        isitialise self.api for the given user
        reusing or creating new settings
        '''
        try:
            with open(self.settings_path) as settings_file:
                cached_settings = json.load(settings_file, object_hook=from_json)
                self.device_id = cached_settings.get('device_id')
                print('Reusing settings: {0}'.format(self.settings_path))
                self.api = Client(self.user.username,
                                  self.user.password,
                                  settings=cached_settings)
        except (ClientCookieExpiredError, ClientLoginRequiredError, FileNotFoundError) as ex:
            print(str(ex))
            # Login expired, renew cookie upon login
            self.api = Client(self.user.username,
                              self.user.password,
                              on_login=lambda x: on_login(x, self.settings_path))
        except ClientLoginError as ex:
            print('ClientLoginError {0!s}'.format(ex))
            sys.exit(9)
        except ClientError as ex:
            print('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(ex.msg,
                                                                            ex.code,
                                                                            ex.error_response))
            sys.exit(9)
        except Exception as ex:
            print('Unexpected Exception: {0!s}'.format(ex))
            sys.exit(99)

    def setup_stalkers(self):
        '''
        create stalkers file if it doesn't exist
        '''
        if not os.path.isfile('stalkers.json'):
            with open('stalkers.json', 'w+') as new_file:
                new_file.write('{}')
        with open("stalkers.json", "r") as stalkers_file:
            self.stalkers = json.load(stalkers_file)

    def find_em(self):
        '''
        check who watched your story but does not follow you
        and print it
        '''
        if self.story is None:
            print('You do not have any stories.')
            self.stop_bot()
            return
        uuid = self.api.generate_uuid()
        followers = []
        followers_dict = self.api.user_followers(self.api.authenticated_user_id, uuid)
        followers.extend(followers_dict['users'])
        last_id = followers_dict['next_max_id']
        while last_id is not None:
            followers_dict = self.api.user_followers(self.api.authenticated_user_id,
                                                     uuid,
                                                     max_id=last_id)
            followers.extend(followers_dict['users'])
            last_id = followers_dict['next_max_id']
        self.user.set_followers(followers)
        for element in self.story.get('items', []):
            viewers_dict = self.api.story_viewers(element.get('id', []))
            story_viewers = viewers_dict['users']
            last_id = viewers_dict['next_max_id']
            while last_id is not None:
                viewers_dict = self.api.story_viewers(element.get('id', []), max_id=last_id)
                story_viewers.extend(viewers_dict['users'])
                last_id = viewers_dict['next_max_id']
            for stalker in story_viewers:
                # if he's not a follower
                if not stalker['pk'] in self.user.followers:
                    stalker_info = self.api.user_info(stalker['pk'])['user']
                    # if he's not a bot
                    if stalker_info['mutual_followers_count'] > 0:
                        # new stalker found
                        stalker_uname = stalker_info['username']
                        if not stalker_uname in self.stalkers:
                            self.print_stalker(stalker_info, False)
                            self.stalkers[stalker_uname] = {}
                            self.stalkers[stalker_uname]['stories'] = []
                            self.stalkers[stalker_uname]['stories'].append(element.get('id', []))
                        # recurrent stalker found
                        elif element.get('id', []) not in self.stalkers[stalker_uname]['stories']:
                            self.print_stalker(stalker_info, True)
                            self.stalkers[stalker_uname]['stories'].append(element.get('id', []))
        with open('stalkers.json', 'w') as stalkers_file:
            json.dump(self.stalkers, stalkers_file)
        self.stop_bot()


    def stop_bot(self):
        '''Cleanup self.updater'''
        if self.args.token is not None:
            self.updater.stop()
            self.updater.is_idle = False


    def print_stalker(self, user, recurrent):
        '''print the stalker on stdout and send a message through the bot'''
        msg = ''
        if recurrent:
            msg = 'Recurrent'
        msg += ('Stalker found!\n' +
                'Uname:{}\n' +
                'Full name:{}\n' +
                'Followers:{}\n' +
                'Following:{}').format(user['username'],
                                       user['full_name'],
                                       user['follower_count'],
                                       user['following_count'])
        print(msg)
        if self.args.token is not None:
            self.updater.bot.send_photo(chat_id=self.args.chat,
                                        photo=user['profile_pic_url'],
                                        caption=msg)

def main():
    '''Create a stalkerFinder and run it'''
    s_finder = StalkerFinder()
    s_finder.find_em()
    sys.exit(0)


if __name__ == '__main__':
    main()
    