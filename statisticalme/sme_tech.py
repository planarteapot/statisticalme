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

import logging


logger = logging.getLogger('StatisticalMe')


class TechHandler:
    def __init__(self):
        self.tech_keys = [
            # 0
            'redstarscanner', 'creditcapacity',

            # 2 ships
            'transport', 'miner', 'battleship',

            # 5 trade
            'cargobayextension', 'shipmentcomputer', 'tradeboost', 'rush',
            'tradeburst', 'shipmentdrone', 'offload', 'shipmentbeam',
            'entrust', 'dispatch', 'recall', 'relicdrone',

            # 17 mining
            'miningboost', 'hydrogenbayextension', 'enrich', 'remotemining',
            'hydrogenupload', 'miningunity', 'crunch', 'genesis',
            'hydrogenrocket', 'miningdrone',

            # 27 weapon
            'battery', 'laser', 'massbattery',
            'duallaser', 'barrage', 'dart',

            # 33 shield
            'deltashield', 'passiveshield', 'omegashield',
            'mirrorshield', 'blastshield', 'areashield',

            # 39 support
            'emp', 'teleport', 'redstarlifeextender', 'remoterepair',
            'timewarp', 'unity', 'sanctuary', 'stealth',
            'fortify', 'impulse', 'alpharocket', 'salvage',
            'suppress', 'destiny', 'barrier', 'vengeance',
            'deltarocket', 'leap', 'bond', 'alphadrone',
            'suspend', 'omegarocket', 'remotebomb'
            ]

        self.tech_key_aliases = {
            'redstarscanner': ['rs', 'rss', 'rscanner', 'rsscanner', 'scanner', 'redstar'],
            'creditcapacity': ['cc', 'credcap', 'creditcap'],

            # ships
            'transport': ['ts', 'transp'],
            'battleship': ['bs'],

            # trade
            'cargobayextension': ['cbe', 'cargo', 'cargobay'],
            'shipmentcomputer': ['computer', 'comp', 'shipcomp', 'shipcomputer'],
            'tradeboost': ['tboost'],
            'tradeburst': ['burst', 'tburst'],
            'shipmentdrone': ['sdrone', 'shipdrone'],
            'shipmentbeam': ['beam', 'sbeam'],
            'relicdrone': ['rd', 'rdrone', 'reldrone'],

            # mining
            'miningboost': ['mboost'],
            'hydrogenbayextension': ['hbe', 'hydrobay', 'hydrogenbay'],
            'remotemining': ['remote'],
            'hydrogenupload': ['upload', 'hupload', 'hydroupload'],
            'miningunity': ['munity'],
            'genesis': ['gen'],
            'hydrogenrocket': ['hrocket', 'hydrorocket'],
            'miningdrone': ['mdrone', 'minedrone'],

            # weapon
            'battery': ['batt'],
            'massbattery': ['mb', 'mass', 'massbatt'],
            'duallaser': ['dl', 'dual'],

            # shield
            'deltashield': ['delta'],
            'passiveshield': ['passive'],
            'omegashield': ['omega'],
            'mirrorshield': ['mirror'],
            'blastshield': ['blast'],
            'areashield': ['area'],

            # support
            'teleport': ['tele', 'tp'],
            'redstarlifeextender': ['rse', 'rsle', 'rsextender'],
            'remoterepair': ['rr', 'repair'],
            'timewarp': ['tw', 'warp'],
            'sanctuary': ['sanc'],
            'alpharocket': ['ar', 'arocket', 'rocket'],
            'suppress': ['sup', 'suppres'],
            'destiny': ['dest'],
            'barrier': ['bar'],
            'vengeance': ['veng'],
            'deltarocket': ['dr', 'drocket'],
            'alphadrone': ['ad', 'drone'],
            'suspend': ['sus', 'susp'],
            'omegarocket': ['or'],
            'remotebomb': ['bomb', 'rbomb']
            }

        self.tech_names = [
            # 0
            'RedStar Scanner', 'Credit Capacity',

            # 2 ships
            'Transport', 'Miner', 'Battleship',

            # 5 trade
            'Cargo Bay Extension', 'Shipment Computer', 'Trade Boost', 'Rush',
            'Trade Burst', 'Shipment Drone', 'Offload', 'Shipment Beam',
            'Entrust', 'Dispatch', 'Recall', 'Relic Drone',

            # 17 mining
            'Mining Boost', 'Hydrogen Bay Extension', 'Enrich', 'Remote Mining',
            'Hydrogen Upload', 'Mining Unity', 'Crunch', 'Genesis',
            'Hydrogen Rocket', 'Mining Drone',

            # 27 weapon
            'Battery', 'Laser', 'Mass Battery',
            'Dual Laser', 'Barrage', 'Dart',

            # 33 shield
            'Delta Shield', 'Passive Shield', 'Omega Shield',
            'Mirror Shield', 'Blast Shield', 'Area Shield',

            # 39 support
            'EMP', 'Teleport', 'Red Star Life Extender', 'Remote Repair',
            'Time Warp', 'Unity', 'Sanctuary', 'Stealth',
            'Fortify', 'Impulse', 'Alpha Rocket', 'Salvage',
            'Suppress', 'Destiny', 'Barrier', 'Vengeance',
            'Delta Rocket', 'Leap', 'Bond', 'Alpha Drone',
            'Suspend', 'Omega Rocket', 'Remote Bomb'
            ]

        self.other_range = (0, 2)
        self.ships_range = (2, 5)
        self.trade_range = (5, 17)
        self.mining_range = (17, 27)
        self.weapon_range = (27, 33)
        self.shield_range = (33, 39)
        self.support_range = (39, 63)

        # tech key or tech alias to tech index
        self.tech_key_index = dict()

        for li in range(len(self.tech_keys)):
            self.tech_key_index[self.tech_keys[li]] = int(li)

        for la_key, la_val in self.tech_key_aliases.items():
            li = self.tech_key_index[la_key]

            for la in la_val:
                self.tech_key_index[la] = int(li)

        logger.info('object TechHandler built')

    # @staticmethod
    # def index_dict_from_list(p_list):
    #     r_index = dict()

    #     for li in range(len(p_list)):
    #         r_index[p_list[li]] = li

    #     return r_index

    def get_tech_index(self, tech):
        li = -1

        if tech in self.tech_key_index:
            li = self.tech_key_index[tech]
        elif tech == 'relics':
            li = 9900
        elif tech == 'totalcargo':
            li = 9901

        return li

    def get_tech_name(self, tech):
        tname = ''

        tindex = self.get_tech_index(tech)
        if tindex >= 0 and tindex < 9900:
            tname = self.tech_names[tindex]
        elif tindex == 9900:
            tname = 'Relics'
        elif tindex == 9901:
            tname = 'Total Cargo'

        return tname

    def tech_keys_range_other(self):
        return self.tech_keys[self.other_range[0]:self.other_range[1]]

    def tech_keys_range_ships(self):
        return self.tech_keys[self.ships_range[0]:self.ships_range[1]]

    def tech_keys_range_trade(self):
        return self.tech_keys[self.trade_range[0]:self.trade_range[1]]

    def tech_keys_range_mining(self):
        return self.tech_keys[self.mining_range[0]:self.mining_range[1]]

    def tech_keys_range_weapon(self):
        return self.tech_keys[self.weapon_range[0]:self.weapon_range[1]]

    def tech_keys_range_shield(self):
        return self.tech_keys[self.shield_range[0]:self.shield_range[1]]

    def tech_keys_range_support(self):
        return self.tech_keys[self.support_range[0]:self.support_range[1]]

    def range_name(self, tech_id):
        name = 'unknown'

        if tech_id >= self.other_range[0] and tech_id < self.other_range[1]:
            name = 'other'
        elif tech_id >= self.ships_range[0] and tech_id < self.ships_range[1]:
            name = 'ships'
        elif tech_id >= self.trade_range[0] and tech_id < self.trade_range[1]:
            name = 'trade'
        elif tech_id >= self.mining_range[0] and tech_id < self.mining_range[1]:
            name = 'mining'
        elif tech_id >= self.weapon_range[0] and tech_id < self.weapon_range[1]:
            name = 'weapon'
        elif tech_id >= self.shield_range[0] and tech_id < self.shield_range[1]:
            name = 'shield'
        elif tech_id >= self.support_range[0] and tech_id < self.support_range[1]:
            name = 'support'

        return name

    def is_range_change(self, id1, id2):
        result = False

        if self.range_name(id1) != self.range_name(id2):
            result = True

        return result
