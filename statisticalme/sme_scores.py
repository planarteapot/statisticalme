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


def import_weights(p_keypart):
    weights = dict()

    lines = None
    with open('data/values-{}.txt'.format(p_keypart), 'r') as ff:
        lines = ff.read().splitlines()

    iterlines = iter(lines)
    for techs in iterlines:
        weightline = next(iterlines).split(',')
        weightline = [int(x) for x in weightline]

        for tt in techs.split(','):
            weights[tt] = weightline

    return weights
