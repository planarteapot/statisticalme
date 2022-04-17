#!/usr/bin/env python3
#
# This file is part of StatisticalMe discord bot.
#
# Copyright 2019 by Antony Suter
#
# StatisticalMe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# StatisticalMe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with StatisticalMe.  If not, see <https://www.gnu.org/licenses/>.

import sys

from dotenv import load_dotenv
from pathlib import Path
from .responder import MainCommand
import discord
import logging
import os
import re
import shlex
import time

load_dotenv(Path('var/env.sh'))

logger = logging.getLogger('StatisticalMe')
logger.setLevel(logging.DEBUG)

logpath = Path('var/log/statisticalme.log')
logpath.parent.mkdir(parents=True, exist_ok=True)
logfh = logging.FileHandler(logpath)
logfh.setLevel(logging.DEBUG)


class UTCFormatter(logging.Formatter):
    converter = time.gmtime


logformatter = UTCFormatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logfh.setFormatter(logformatter)
logger.addHandler(logfh)

logger.info('App starting; logger ready')

# pseudo global vars

dev_author_env = os.environ['STATISTICALME_DEV_AUTHORS']
ok_channels_env = os.environ['STATISTICALME_OK_CHANNELS']

dev_author_list = [int(aa) for aa in dev_author_env.split(',')]
mainc = MainCommand(dev_author_list, ok_channels_env)

devecho_match = re.compile(r'\s*!sme\s+dev\s+echo\b', re.IGNORECASE)
devping_match = re.compile(r'\s*!sme\s+dev\s+ping\b', re.IGNORECASE)

alias_matches = [
    (re.compile(r'\s*!sme\b', re.IGNORECASE), []),
    (re.compile(r'\s*!gt\b', re.IGNORECASE), ['tech', 'list']),
    (re.compile(r'\s*!away\b', re.IGNORECASE), ['time', 'away']),
    (re.compile(r'\s*!back\b', re.IGNORECASE), ['time', 'back']),
    (re.compile(r'\s*!checkin\b', re.IGNORECASE), ['time', 'checkin']),
    (re.compile(r'\s*!dead\b', re.IGNORECASE), ['ws', 'ship', 'dead']),
    (re.compile(r'\s*!ship\b', re.IGNORECASE), ['ws', 'ship']),
    (re.compile(r'\s*!st\b', re.IGNORECASE), ['tech', 'set']),
    (re.compile(r'\s*!tr\b', re.IGNORECASE), ['tech', 'report']),
    (re.compile(r'\s*!time\s+set\b', re.IGNORECASE), ['time']),  # keeps the 'set'
    (re.compile(r'\s*!time\b', re.IGNORECASE), ['time', 'list'])
]


class SmeClient(discord.Client):
    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author == self.user:
            return

        # logger.info('Client event on_message author={au} channel={ch} content={co}'.format(
        #     au=str(message.author), ch=str(message.channel), co=str(message.content)))

        return_message_list = []

        if devecho_match.match(message.clean_content):
            logger.info(f'Client event on_message author={str(message.author)} channel={str(message.channel)} content={str(message.content)}')

            if message.author.id in dev_author_list:
                msg_list = ['Content:', str(message.content),
                            '```\n' + str(message.content) + '\n```',
                            'Clean content:', str(message.clean_content),
                            '```\n' + str(message.clean_content) + '\n```']
                # print('ECHO msg_list "{}"'.format(msg_list))
                return_message_list = ['\n'.join(msg_list)]
        elif devping_match.match(message.clean_content):
            logger.info(f'Client event on_message author={str(message.author)} channel={str(message.channel)} content={str(message.content)}')

            if message.author.id in dev_author_list:
                return_message_list = ['Pong']
        else:
            pre_list = None

            for a_match, a_list in alias_matches:
                if a_match.match(message.clean_content):
                    pre_list = a_list
                    break

            if pre_list is not None:
                logger.info(f'Client event on_message author={str(message.author)} channel={str(message.channel)} content={str(message.content)}')

                params = shlex.split(message.content)
                msg_list = await mainc.on_message(pre_list + params[1:], message.author, message.channel)
                return_message_list = return_message_list + msg_list
            # else:
            #     await mainc.on_unused_message(message)

        if return_message_list is not None:
            if len(return_message_list) == 1:
                rarg = return_message_list[0]
                if rarg[:23] == 'dented-control-message:':
                    return_message_list.pop()
                    rarg_command = rarg[23:]

                    if rarg_command == 'no-reply':
                        pass
                    if rarg_command == 'delete-original-message':
                        await message.delete()
                    elif rarg_command == 'quit':
                        await self.close()
                        sys.exit(0)

            if len(return_message_list) > 0:
                for mm in return_message_list:
                    if len(mm) > 0:
                        await message.channel.send(mm)

    async def on_ready(self):
        logger.info('Client event on_ready')

        logger.info('Logged in as: {}'.format(self.user.name))
        mainc.set_bot_self(self.user)

        logger.info('In guilds: {}'.format(', '.join([str(g) for g in self.guilds])))
        if len(self.guilds) >= 1:
            mainc.set_guild(self.guilds[0])


def main_function():
    intents = discord.Intents.default()
    intents.typing = False
    intents.presences = False
    intents.reactions = False
    intents.members = True

    client = SmeClient(intents=intents)

    logger.info('Calling discord Client.run')
    client.run(os.environ['STATISTICALME_TOKEN'])


if __name__ == "__main__":
    main_function()
