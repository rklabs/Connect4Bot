#!/usr/bin/env python
import logging
import os
import re
import sys
import time
import websocket

from collections import namedtuple

from slackclient import SlackClient

from connect4 import Connect4

log = logging.getLogger(__name__)

BOT_NAME = 'connect4bot'
SUCCESS = 0
FAILURE = 1

BOT_LOOP_SLEEP = 1  # second(s)

# Slack message tuple
SlackMessage = namedtuple('SlackMessage', 'mtype user text channel ts action')


class SlackApi:

    def __init__(self):
        self.api_token = None
        self.slack_client = None

    def init_slack_client(self):
        """Initialize SlackClient to invoke slack api's"""
        self.api_token = os.environ.get('SLACK_BOT_API_TOKEN')

        if self.api_token is False:
            log.error('Please setup SLACK_BOT_API_TOKEN env var')
            return False

        try:
            self.slack_client = SlackClient(self.api_token)
        # XXX Handle specific exception
        except Exception as e:
            log.error('SlackClient() %s' % e)
            return False

        if not self.slack_client:
            log.error('SlackClient() failed!')
            return False

        return True

    def get_users(self, user_properties=('first_name', 'last_name', 'name'),
                  is_bot=False):
        """Return all users(with certain properties) in the team"""
        try:
            slack_api = self.slack_client.api_call('users.list')
        # XXX Need to catch specific exception(s)
        except Exception as e:
            log.error(e)
            return False

        group_users = {}

        if not slack_api.get('ok'):
            log.error('users.list call failed')
            return False

        users = slack_api.get('members')
        if len(users) == 0:
            log.error('users.members failed')
            return False

        for user in users:
            # Ignore 'slackbot'
            if user['name'] == 'slackbot':
                continue

            # Ignore bot user
            if user['is_bot'] and not is_bot:
                continue

            group_users[user['id']] = {}
            for user_property in user_properties:
                if user_property == 'name':
                    group_users[user['id']][user_property] = \
                        user[user_property]
                else:
                    group_users[user['id']][user_property] = \
                        user['profile'][user_property]

        print('Bot users')
        print(group_users)
        return group_users

    def post_slack_message(self, channel, text):
        """Post message to slack channel(can be user or bot)"""
        try:
            result = self.slack_client.api_call('chat.postMessage',
                                                channel=channel,
                                                text=text,
                                                as_user=True)
            print(result)
        # XXX Need to catch specific exception(s)
        except Exception as e:
            log.error(e)


class RTMHandler:

    def __init__(self, slack_client):
        self.slack_client = slack_client

    def connect(self):
        """Connect to slack websocket server"""
        if not self.slack_client.rtm_connect():
            log.error('rtm_connect failed!')
            return False

        return True

    def read(self):
        """Reads websocket messages and returns to caller as list of dict"""
        try:
            msg = self.slack_client.rtm_read()
        # Websocket connection maybe closed due to unexpected reason(s)
        except websocket._exceptions.WebSocketConnectionClosedException as e:
            log.error(e)
            return False

        return msg


class Connect4Bot:

    def __init__(self):
        self.slack_api = None
        self.rtm_handler = None
        self.connect4 = None
        self.initiator = None
        self.opponent = None
        self.game_over = False
        self.current_player = None
        self.players = {}
        self.user_mapping = {}

    def init_game_connect4(self):
        """Initialize Connect4 game and assign player identifier"""
        self.connect4 = Connect4()

        self.connect4.player_a = ':red_circle:'
        self.connect4.player_b = ':black_circle:'
        self.connect4.empty_block = ':white_square:'

        self.connect4.build_new_board()

    def init_slack_rtmhandler(self):
        """Create RTMHandler object for connecting and reading websocket"""
        self.rtm_handler = RTMHandler(self.slack_api.slack_client)

    def init_slack_bot(self):
        """Initialize slack bot"""
        self.slack_api = SlackApi()

        if not self.slack_api.init_slack_client():
            log.error('Error setting up slack api client')
            return False

        self.init_game_connect4()

        self.init_slack_rtmhandler()

        self.players = self.slack_api.get_users()

        if not self.players:
            log.error('No users found in slack channel!')
            return False

        return True

    def start_game_connect4(self, slack_message):
        """Start Connect4 game when user executes command 'play'"""
        self.game_over = False
        self.initiator = slack_message.user

        match = re.search('play.*<@(?P<id>[0-9a-zA-Z]{9})>',
                          slack_message.text, re.IGNORECASE)
        if match and match.group('id'):
            self.opponent = match.group('id')
        else:
            log.error('User regex match failed!')
            return False

        print('Game started by {} with {}'.format(
            self.players[self.initiator]['name'],
            self.players[self.opponent]['name'])
        )

        # Map game initiator and opponent to connect4 players
        self.user_mapping = {
            self.initiator: self.connect4.player_a,
            self.opponent:  self.connect4.player_b
        }

        self.send_new_game_board()

        print(slack_message)
        return slack_message

    def select_board_column(self, slack_message):
        """Sets board state when user selects column"""
        if not self.players.get(slack_message.user):
            log.info('Unexpected message')
            return

        match = re.search('column.*(?P<column>\d+)',
                          slack_message.text, re.IGNORECASE)
        if match and match.group('column'):
            column = int(match.group('column')) - 1

            if self.current_player != slack_message.user:
                self.slack_api.post_slack_message(
                    channel='@' + self.players[slack_message.user]['name'],
                    text='Not your turn, gotta wait!'
                )
                return

            print('column {} was selected by {}'.format(
                column, self.players[slack_message.user]['name'])
            )

            # If user selects column which is full inform the user
            if self.connect4.is_column_full(column) and \
                    not self.connect4.is_board_full():
                self.slack_api.post_slack_message(
                    channel='@' + self.players[slack_message.user]['name'],
                    text='Column is full'
                )
                return

            # Update game state by selecting column
            self.connect4.make_move(
                self.user_mapping[self.current_player],
                column
            )

            # Send current game board to both users
            self.send_game_board()
        else:
            log.error('column regex failed!')
            return False

        return True

    def handle_game_play(self, slack_message):
        """Start the game when user execute play command"""
        self.current_player = slack_message.user
        self.start_game_connect4(slack_message)

        print('play')
        print(slack_message)

    def handle_game_select_column(self, slack_message):
        """Handler function which is called from user
        executes 'column' command"""
        if not self.current_player:
            log.info('Game not yet started')
            return

        # Make move
        if not self.select_board_column(slack_message):
            return

        if self.connect4.check_winner(self.user_mapping[self.current_player]):
            winner = self.players[self.current_player]['name']
            print('Player {} won!'.format(winner))
            for player in self.players:
                if player == self.initiator or player == self.opponent:
                    self.slack_api.post_slack_message(
                        channel='@' + self.players[player]['name'],
                        text='Player @{} won!\nEnd game.'.format(winner)
                    )
            self.game_over = True
            return SUCCESS

        if self.connect4.is_board_full():
            for player in self.players:
                if player == self.initiator or player == self.opponent:
                    self.slack_api.post_slack_message(
                        channel='@' + self.players[player]['name'],
                        text='It\'s a tie!'
                    )
            self.game_over = True
            return SUCCESS

        # Swap players
        if self.current_player == self.initiator:
            self.current_player = self.opponent
        elif self.current_player == self.opponent:
            self.current_player = self.initiator

        # Send message and board to opponent

    def handle_game_help(self, slack_message):
        """Handles 'help' command from user """
        msg = 'Hello ' + '<@' + slack_message.user + '>' + \
              '. Below are the rules of Connect4 game\n'
        msg += '1. Enter \'play @user\' to start Connect4\n'
        msg += '2. Enter \'column n\' to select column, n must be 1-7\n'
        msg += '3. Current board state will be displayed after each command\n'
        msg += '4. Player with 4 same colored circles in horizontal or' \
               ' vertical or diagonal line wins the game\n'
        msg += 'Good luck!'

        self.slack_api.post_slack_message(channel=slack_message.channel,
                                          text=msg)

    def parse_slack_messages(self, rtm_msgs):
        """Parses slack messages returned by rtm read()
        and sets up slack_message which appropriate action"""
        if len(rtm_msgs) == 0:
            return False

        for msg in rtm_msgs:
            if not msg or 'text' not in msg or not msg.get('user'):
                log.info("Not the msg that I'm looking for")
                log.info(msg)
                continue

            # XXX Need a better way of handling commands
            if 'play' in msg['text'].lower() and \
                    'rules' not in msg['text'].lower() and \
                    'won' not in msg['text'].lower():
                return SlackMessage(msg['type'], msg['user'],
                                    msg['text'], msg['channel'],
                                    msg['ts'], 'play')
            elif 'column' in msg['text'].lower():
                # and self.current_player is the user
                return SlackMessage(msg['type'], msg['user'],
                                    msg['text'], msg['channel'],
                                    msg['ts'], 'select_column')
            elif 'help' in msg['text'].lower():
                return SlackMessage(msg['type'], msg['user'],
                                    msg['text'], msg['channel'],
                                    msg['ts'], 'help')
            else:
                print(msg)
        return None

    def send_new_game_board(self):
        """Send new game board to user"""
        if not self.current_player:
            log.info('Connect4 not yet started')
            return

        if self.initiator == self.opponent:
            self.slack_api.post_slack_message(
                channel='@' + self.players[self.initiator]['name'],
                text="Oops! You can't choose yourself as the opponent."
            )
            return

        initiator = '<@' + self.players[self.initiator]['name'] + '>'
        message = 'Starting game, ' + initiator + \
            ', your turn. Choose column between 1 to 7'

        legend = '\n'
        for player in [self.initiator, self.opponent]:
            legend += self.user_mapping[player] + ' ' + \
                self.players[player]['name']

        message += legend

        player = self.players[self.current_player]['name']
        self.slack_api.post_slack_message(
            channel='@' + player,
            text=message
        )

        for row in self.connect4.rows():
            self.slack_api.post_slack_message(
                channel='@' + player,
                text=''.join(row)
            )

    def send_game_board(self):
        """Send current game board to all players"""
        print(self.players)

        player_next_turn_id \
            = (set(self.players.keys()) - set([self.current_player])).pop()
        player_next_turn = self.players[player_next_turn_id]['name']

        legend = '\n'
        for player in [self.initiator, self.opponent]:
            legend += self.user_mapping[player] + ' ' + \
                self.players[player]['name']

        for user in self.players:
            # XXX Need to revisit, is it really required?
            if not self.players[user]:
                continue

            player = self.players[user]['name']
            self.slack_api.post_slack_message(
                channel='@' + player,
                text='Current game, @{}\'s turn. '.
                        format(player_next_turn) + legend
            )

            for row in self.connect4.rows():
                self.slack_api.post_slack_message(
                    channel='@' + player,
                    text=''.join(row)
                )

    def main_loop(self):
        """Connect4Bot main loop"""
        # Connect to slack RTM websocket
        if not self.rtm_handler.connect():
            return False

        while True:
            # Get real time messages from slack channel
            slack_messages = self.rtm_handler.read()

            # No messages to handle, sleep and read websocket again
            if not slack_messages:
                time.sleep(BOT_LOOP_SLEEP)
                continue

            slack_message = self.parse_slack_messages(slack_messages)

            # No 'interesting' message
            if not slack_message:
                continue

            # Call handler based on action attached to slack message
            if slack_message.action == 'play':
                self.handle_game_play(slack_message)
            elif slack_message.action == 'select_column':
                self.handle_game_select_column(slack_message)
            elif slack_message.action == 'help':
                self.handle_game_help(slack_message)
            else:
                assert False, 'Unknown game action'

            if self.game_over:
                self.init_game_connect4()
                self.game_over = False

            time.sleep(BOT_LOOP_SLEEP)


def main():
    connect4bot = Connect4Bot()

    if not connect4bot.init_slack_bot():
        sys.exit(-1)

    if not connect4bot.main_loop():
        sys.exit(-1)

if __name__ == '__main__':
    logging.info('Starting logger for Connect4Bot')
    main()
