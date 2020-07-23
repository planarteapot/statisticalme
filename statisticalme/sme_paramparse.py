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


from .sme_utils import normalize_caseless
import logging


logger = logging.getLogger('StatisticalMe')


class CommandParse():
    def __init__(self, title):
        self.title = title

        self.params = dict()

    def add_command(self, key, object_flag, value, auth_fn=None):
        self.params[normalize_caseless(key)] = [object_flag, value, auth_fn]

    async def do_command(self, param_list):
        return_list = []

        if len(param_list) >= 1:
            pcommand = normalize_caseless(param_list[0])

            pparams = []
            if len(param_list) > 1:
                pparams = param_list[1:]

            if pcommand in self.params:
                object_flag, value, auth_fn = self.params[pcommand]
                if auth_fn is None or auth_fn():
                    if object_flag:
                        return_list = return_list + await value.do_command(pparams)
                    else:
                        return_list = return_list + await value(pparams)
                else:
                    logger.warning('Command denied')
            else:
                return_list = return_list + ['Unknown command {go}. Expected one of {ex}'.format(
                    go=pcommand, ex=[e for e in self.params])]

        return return_list
