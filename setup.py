# This file is part of StatisticalMe discord bot.
#
# Copyright 2019-2020 by Antony Suter.
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


from setuptools import setup

setup(
    name='statisticalme',
    version='20.3.5',
    entry_points={"console_scripts": ["statisticalme = statisticalme.main:main_function"]},
    packages=['statisticalme'],
    zip_safe=False,
    platforms='any',
)
