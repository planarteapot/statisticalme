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

import copy
import json
import logging
import math
import re
import sys
import traceback

import aiohttp
import discord
from discord.ext import tasks

import statisticalme.statisticalme as smer

from . import sme_paramparse, sme_table, sme_tech

logger = logging.getLogger("StatisticalMe")
teh = sme_tech.TechHandler()

bs_support_count = [0, 0, 1, 2, 3, 4, 5]


def is_int(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


class MainCommand:
    def __init__(self, dev_author_list, ok_channels):
        logger.debug("MainCommand __init__")

        self.dev_author_list = dev_author_list
        self.ok_channels = ok_channels.split(",")

        self.time_now = smer.sme_time_now()
        self.time_up = self.time_now

        self.background_update_started = False

        self.aiohttp_session = aiohttp.ClientSession()

        self.current_guild = None

        self.timeparse_match1 = re.compile(r"(\d+)([dhm])")
        self.timeparse_match2 = re.compile(r"(\d+):(\d+):(\d+)")
        self.timeparse_match3 = re.compile(r"(\d+):(\d+)")
        self.timeparse_match4 = re.compile(r"(\d+)d(\d+)h(\d+)m")
        self.ws_name_match = re.compile(r"-([a-zA-Z]+\d*)$")

        # Load configuration/non-pilot data
        self.config_filepath = "var/config.json"
        self.flag_config_dirty = False
        self.groups = dict()
        self.ws = dict()
        self.config_load()

        # Load persistant/pilot data
        self.persdata_filepath = "var/persdata.json"
        self.flag_persdata_dirty = False
        self.players = dict()
        self.persdata_load()

        # Even if a dev group is saved and loaded, we do not use it and we overwrite it.
        self.groups_protected = ["dev"]
        self.groups_next_refresh_all = self.time_now
        self.group_set("dev", " ".join([f"<@!{mm}>" for mm in dev_author_list]))

        self.messages_out = list()

        logger.debug(f"{ok_channels=}")

        self.weights = dict()
        try:
            with open("var/weights.json", "r") as fh:
                loaded = json.load(fh)

                if "weights" in loaded:
                    self.weights = copy.copy(loaded["weights"])
        except Exception:
            logger.debug("Exception reading weights file")

        self.dev_parser = sme_paramparse.CommandParse(title="StatisticalMe Dev")
        self.dev_parser.add_command("info", False, self.dev_command_info)
        self.dev_parser.add_command("save", False, self.dev_command_save)
        self.dev_parser.add_command("roleprint", False, self.dev_command_roleprint)
        self.dev_parser.add_command("techlist", False, self.dev_command_techlist)
        self.dev_parser.add_command("purge1", False, self.dev_command_purge1)
        self.dev_parser.add_command("quit", False, self.dev_command_quit)

        self.subparser_group = sme_paramparse.CommandParse(title="StatisticalMe group")
        self.subparser_group.add_command("add", False, self.command_group_add)
        self.subparser_group.add_command("remove", False, self.command_group_remove)
        self.subparser_group.add_command("list", False, self.command_group_list)

        self.subparser_rolemem = sme_paramparse.CommandParse(
            title="StatisticalMe role members"
        )
        self.subparser_rolemem.add_command("add", False, self.command_rolemem_add)
        self.subparser_rolemem.add_command("remove", False, self.command_rolemem_remove)
        self.subparser_rolemem.add_command("list", False, self.command_rolemem_list)

        self.subparser_ws = sme_paramparse.CommandParse(title="StatisticalMe ws")
        self.subparser_ws.add_command(
            "add", False, self.command_ws_add, auth_fn=self.auth_chief
        )
        self.subparser_ws.add_command(
            "remove", False, self.command_ws_remove, auth_fn=self.auth_chief
        )
        self.subparser_ws.add_command(
            "list", False, self.command_ws_list, auth_fn=self.auth_chief
        )
        self.subparser_ws.add_command(
            "roles", False, self.command_ws_roles, auth_fn=self.auth_chief
        )
        self.subparser_ws.add_command(
            "ship", False, self.command_ws_ship, auth_fn=self.auth_watcher
        )

        self.subparser_tech = sme_paramparse.CommandParse(title="StatisticalMe tech")
        self.subparser_tech.add_command("set", False, self.command_tech_set)
        self.subparser_tech.add_command("report", False, self.command_tech_report)
        self.subparser_tech.add_command("list", False, self.command_tech_list)

        self.subparser_time = sme_paramparse.CommandParse(title="StatisticalMe time")
        self.subparser_time.add_command("set", False, self.command_time_set)
        self.subparser_time.add_command("get", False, self.command_time_get)
        self.subparser_time.add_command("list", False, self.command_time_list)
        self.subparser_time.add_command("away", False, self.command_time_away)
        self.subparser_time.add_command("back", False, self.command_time_back)
        self.subparser_time.add_command("checkin", False, self.command_time_checkin)

        self.subparser_pilot = sme_paramparse.CommandParse(title="StatisticalMe pilot")
        self.subparser_pilot.add_command("lastup", False, self.command_pilot_lastup)

        self.ord_parser = sme_paramparse.CommandParse(title="StatisticalMe")
        self.ord_parser.add_command("dev", True, self.dev_parser, auth_fn=self.auth_dev)
        self.ord_parser.add_command(
            "group", True, self.subparser_group, auth_fn=self.auth_chief
        )
        self.ord_parser.add_command(
            "rolemem", True, self.subparser_rolemem, auth_fn=self.auth_chief
        )
        self.ord_parser.add_command("ws", True, self.subparser_ws)
        self.ord_parser.add_command(
            "tech", True, self.subparser_tech, auth_fn=self.auth_watcher
        )
        self.ord_parser.add_command(
            "time", True, self.subparser_time, auth_fn=self.auth_watcher
        )
        self.ord_parser.add_command(
            "pilot", True, self.subparser_pilot, auth_fn=self.auth_chief
        )
        self.ord_parser.add_command(
            "score", False, self.command_score, auth_fn=self.auth_watcher
        )
        self.ord_parser.add_command(
            "msgme", False, self.command_msgme, auth_fn=self.auth_watcher
        )
        self.ord_parser.add_command(
            "clear", False, self.command_clear, auth_fn=self.auth_chief
        )

        self.current_author = None
        self.current_channel = None

        logger.info("object MainCommand built")

    def post_guild_init(self):
        self.time_now = smer.sme_time_now()
        self.group_refresh_all()
        self.opportunistic_save()
        self.opportunistic_background_update_start()

    def set_guild(self, p_guild):
        self.current_guild = p_guild
        self.post_guild_init()

    def config_load(self):
        try:
            with open(self.config_filepath, "r") as fh:
                loaded = json.load(fh)

                if "groups" in loaded:
                    self.groups = copy.copy(loaded["groups"])

                if "ws" in loaded:
                    self.ws = copy.copy(loaded["ws"])

                self.flag_config_dirty = False
        except Exception:
            logger.debug("Exception reading config file")

    def config_save(self):
        with open(self.config_filepath, "w") as fh:
            json.dump({"groups": self.groups, "ws": self.ws}, fh)

            self.flag_config_dirty = False

    def persdata_load(self):
        try:
            with open(self.persdata_filepath, "r") as fh:
                loaded = json.load(fh)

                ltk = loaded["tech_keys"]

                if ltk == teh.tech_keys:
                    self.players = copy.copy(loaded["players"])
                else:
                    logger.info("Massaging persistant data for new tech list")

                    self.players = dict()
                    unk_tech = set()

                    for loaded_pkey, loaded_p in loaded["players"].items():
                        self.players[loaded_pkey] = copy.copy(loaded_p)

                        loaded_tech = self.players[loaded_pkey]["tech"]
                        self.players[loaded_pkey]["tech"] = [0] * len(teh.tech_keys)

                        for index in range(len(loaded_tech)):
                            key = ltk[index]

                            if teh.get_tech_index(key) >= 0:
                                self.player_tech_set(
                                    loaded_pkey, key, loaded_tech[index]
                                )
                            else:
                                unk_tech.add(key)

                    if len(unk_tech) > 0:
                        logger.debug(f"Unknown techs {unk_tech} in persistant data")

                    self.persdata_save()

                self.flag_persdata_dirty = False
        except Exception:
            logger.debug("Exception reading persdata file")
            self.players = dict()

    def persdata_save(self):
        with open(self.persdata_filepath, "w") as fh:
            json.dump({"tech_keys": teh.tech_keys, "players": self.players}, fh)

            self.flag_persdata_dirty = False

    def opportunistic_save(self):
        if self.flag_config_dirty:
            self.config_save()

        if self.flag_persdata_dirty:
            self.persdata_save()

    def auth_dev(self):
        return self.group_contains_member("dev", self.current_author.id)

    def auth_chief(self):
        allowed = False

        if self.auth_dev():
            allowed = True
        elif self.group_contains_member("auth_chief", self.current_author.id):
            allowed = True

        return allowed

    def auth_watcher(self):
        allowed = False

        if self.auth_dev():
            allowed = True
        elif self.auth_chief():
            allowed = True
        elif self.group_contains_member("auth_watcher", self.current_author.id):
            allowed = True

        return allowed

    async def on_message(self, p_content, p_author, p_channel):
        return_list = []

        self.time_now = smer.sme_time_now()
        self.current_author = p_author
        self.current_channel = p_channel

        try:
            if self.groups_next_refresh_all < self.time_now:
                self.group_refresh_all()

            return_list = return_list + await self.ord_parser.do_command(p_content)

            if len(return_list) < 1:
                if self.group_contains_member("dev", self.current_author.id):
                    return_list = ["Pardon, my liege?"]
                elif self.group_contains_member("auth_chief", self.current_author.id):
                    return_list = ["Excuse me chief?"]
                else:
                    return_list = ["Say what?"]

        except SmeArgumentWarning as smewarn:
            if smewarn.message is not None:
                return_list.append(smewarn.message)

        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            tbe = traceback.TracebackException(exc_type, exc_value, exc_tb)
            logger.error("on_message exception\n" + "".join(tbe.format()))

            if self.group_contains_member("dev", self.current_author.id):
                return_list = ["The sky fell, my liege"]
            elif self.group_contains_member("auth_chief", self.current_author.id):
                return_list = ["Sorry about that chief"]
            else:
                return_list = ["Oh crap"]

        # Opportunistic send out messages queued
        if len(self.messages_out) > 0:
            await self.send_out_messages()

        self.current_author = None
        self.current_channel = None

        self.opportunistic_save()

        return return_list

    def queue_msg_for_send_out(self, who_ob, msg_str):
        self.messages_out.append((who_ob, msg_str))

    async def send_out_messages(self):
        while len(self.messages_out) > 0:
            who_ob, msg_str = self.messages_out.pop()
            if (who_ob is not None) and (msg_str is not None) and (len(msg_str) > 0):
                await who_ob.send(msg_str)

    async def dev_command_info(self, params):
        info_str = "StatisticalMe"
        info_str += "\nversion: 23.1.0"
        info_str += "\nnotes:"
        info_str += "\n  - discord.py 2.3"
        info_str += "\nuptime: {ut}".format(
            ut=self.timedelta_as_string(self.time_now - self.time_up)
        )

        return [info_str]

    async def dev_command_save(self, params):
        self.config_save()
        self.persdata_save()
        return ["App and pilot data saved"]

    async def dev_command_roleprint(self, params):
        return_list = []

        who_list = list()
        role_list = list()
        return_list = return_list + self.parse_who(
            params, who_list, role_list=role_list
        )

        if len(role_list) > 0:
            msg_list = []
            for role_id in role_list:
                msg_list.append("Role:")
                msg_list.append(f"  id: {role_id}")

                role = self.role_from_id(role_id)
                if role is not None:
                    msg_list.append(f"  name: {role.name}")
                    member_names = [
                        self.member_name_from_id(memb.id) for memb in role.members
                    ]
                    msg_list.append("  members: " + ", ".join(member_names))

            return_list.append("\n".join(msg_list))
        else:
            return_list.append("Pardon my liege? No config var name")

        return return_list

    async def dev_command_techlist(self, params):
        return ["Valid tech names: " + ", ".join(teh.tech_keys)]

    async def dev_command_purge1(self, params):
        delete_player_list = list()
        len_all = len(self.players)

        flag_yes = False
        flag_name = False

        if "-y" in params:
            flag_yes = True

        if "--name" in params:
            flag_name = True

        for pkey, pdata in self.players.items():
            flag_remove = True

            if pdata["tech"] != [0] * len(teh.tech_keys):
                flag_remove = False

            # ii = pdata["info"]
            # if "last_tech_update" in ii:
            #     flag_remove = False

            if flag_remove:
                delete_player_list.append(pkey)

        len_purge1 = len(delete_player_list)

        return_str = f"Purge1: current {len_all}, remove {len_purge1}"

        if len_purge1 > 0:
            if flag_name:
                name_list = [
                    self.member_name_from_id(pkey) for pkey in delete_player_list
                ]
                return_str += "\nThese players have NO tech:-\n  - " + "\n  - ".join(
                    name_list
                )

            if flag_yes:
                for pkey in delete_player_list:
                    del self.players[pkey]

        return [return_str]

    async def dev_command_quit(self, params):
        self.opportunistic_save()
        return ["dented-control-message:quit"]

    def member_from_id(self, p_id):
        memb = None

        # TODO loop thru all guilds, and do not accept someone from outside those

        if self.current_guild is not None:
            memb = self.current_guild.get_member(int(p_id))

        return memb

    def member_name_from_id(self, p_id):
        name = None

        memb = self.member_from_id(p_id)

        if memb is not None:
            try:
                name = memb.nick
            except AttributeError:
                pass

            if name is None:
                name = memb.name

        if name is None:
            name = ""

        return name

    def member_from_name(self, p_name):
        memb = None

        if self.current_guild is not None:
            memb = self.current_guild.get_member_named(str(p_name))

        return memb

    def role_from_id(self, p_id):
        role = None

        if self.current_guild is not None:
            role = self.current_guild.get_role(int(p_id))

        return role

    def role_from_name(self, p_name):
        role = None

        if self.current_guild is not None:
            role = next((r for r in self.current_guild.roles if r.name == p_name), None)

        return role

    def group_set(self, group_name, group_def):
        self.groups[group_name] = {"defn": str(group_def), "members": list()}

        self.group_refresh(group_name)

    def group_remove(self, group_name):
        if group_name in self.groups:
            del self.groups[group_name]

    def group_exists(self, group_name):
        found = False
        if group_name in self.groups:
            found = True

        return found

    def group_refresh(self, group_name):
        if group_name in self.groups:
            grp = self.groups[group_name]
            if group_name == "dev":
                grp["members"] = copy.copy(self.dev_author_list)
            else:
                grp["members"] = list()
                self.parse_who(grp["defn"].split(" "), grp["members"])

            self.flag_config_dirty = True

    def group_refresh_all(self):
        for group_name, grp in self.groups.items():
            if group_name == "dev":
                grp["members"] = copy.copy(self.dev_author_list)
            else:
                grp["members"] = list()
                self.parse_who(grp["defn"].split(" "), grp["members"])

        self.flag_config_dirty = True
        self.groups_next_refresh_all = self.time_now + 20

    def group_contains_member(self, group_name, memb_id):
        found = False
        if group_name in self.groups:
            grp = self.groups[group_name]
            if memb_id in grp["members"]:
                found = True

        return found

    def parse_who(
        self, param_list, who_list, memb_list=None, role_list=None, other=None
    ):
        return_list = []

        who_set = list()

        for value in param_list:
            if value[0:3] == "<@!" and value[3].isdigit() and value[-1] == ">":
                memb = self.member_from_id(int(value[3:-1]))
                if memb is not None:
                    if memb_list is not None:
                        if memb.id not in memb_list:
                            memb_list.append(memb.id)
                    else:
                        if memb.id not in who_set:
                            who_set.append(memb.id)
            elif value[0:2] == "<@" and value[2].isdigit() and value[-1] == ">":
                memb = self.member_from_id(int(value[2:-1]))
                if memb is not None:
                    if memb_list is not None:
                        if memb.id not in memb_list:
                            memb_list.append(memb.id)
                    else:
                        if memb.id not in who_set:
                            who_set.append(memb.id)
            elif value[0:3] == "<@&" and value[3].isdigit() and value[-1] == ">":
                role = self.role_from_id(int(value[3:-1]))
                if role is not None:
                    if role_list is not None:
                        if role.id not in role_list:
                            role_list.append(role.id)
                    else:
                        for memb in role.members:
                            if memb.id not in who_set:
                                who_set.append(memb.id)
            elif value[0:2] == "?!":
                memb = self.member_from_name(value[2:])
                if memb is not None:
                    if memb_list is not None:
                        if memb.id not in memb_list:
                            memb_list.append(memb.id)
                    else:
                        if memb.id not in who_set:
                            who_set.append(memb.id)
            elif value[0:2] == "?&":
                role = self.role_from_name(value[2:])
                if role is not None:
                    if role_list is not None:
                        if role.id not in role_list:
                            role_list.append(role.id)
                    else:
                        for memb in role.members:
                            if memb.id not in who_set:
                                who_set.append(memb.id)
            else:
                if other is not None:
                    other.append(value)

        # People
        for who in who_set:
            if str(who) not in self.players:
                self.ensure_player_created(who)

            who_list.append(who)

        # logger.debug(f"parse_who() return_list {return_list}")
        # logger.debug(f"parse_who() who_list {who_list}")
        # if memb_list is not None:
        #     logger.debug(f"parse_who() memb_list {memb_list}")
        # if role_list is not None:
        #     logger.debug(f"parse_who() role_list {role_list}")
        # if other is not None:
        #     logger.debug(f"parse_who() other {other}")

        return return_list

    def parse_who_what_int(self, param_list, who_list, what_list, int_list, other=None):
        return_list = []

        who_set = list()
        other_list = list()

        return_list = return_list + self.parse_who(
            param_list, who_set, other=other_list
        )

        what_set = list()

        for value in other_list:
            if is_int(value):
                int_list.append(int(value))
            elif value == "|":
                pass
            else:
                what = smer.sme_utils_normalize_caseless(value)
                what_rangelist = teh.tech_key_range_list(what)
                if what_rangelist:
                    for tt in what_rangelist:
                        if tt not in what_set:
                            what_set.append(tt)
                else:
                    if what[0:2] == "--" or what[0:1] == "+":
                        if other is not None:
                            other.append(what)
                    else:
                        if what not in what_set:
                            what_set.append(what)

        # People
        for who in who_set:
            if str(who) not in self.players:
                self.ensure_player_created(who)

            who_list.append(who)

        # Tech
        for what in what_set:
            if teh.get_tech_index(what) >= 0:
                what_list.append(what)
            else:
                return_list.append(f"Tech {what} not found")

        # logger.debug(f"parse_who_what_int() return_list {return_list}")
        # logger.debug(f"parse_who_what_int() who_list {who_list}")
        # logger.debug(f"parse_who_what_int() what_list {what_list}")
        # logger.debug(f"parse_who_what_int() int_list {int_list}")
        # if other is not None:
        #     logger.debug(f"parse_who_what_int() other {other}")

        return return_list

    def ensure_player_created(self, p_playerid):
        playerid = str(p_playerid)
        if playerid not in self.players:
            self.players[playerid] = {"tech": [0] * len(teh.tech_keys), "info": dict()}

    def player_tech_get(self, p_playerid, techname):
        playerid = str(p_playerid)
        r_value = 0

        if playerid in self.players:
            p = self.players[playerid]

            if "tech" in p:
                pt = p["tech"]

                if techname == "relics" or techname == "totalcargo":
                    ti_cbe = teh.get_tech_index("cargobayextension")
                    ti_ts = teh.get_tech_index("transport")

                    if ti_cbe >= 0 and ti_ts >= 0:
                        totalcargo = 0
                        val_cbe = pt[ti_cbe]
                        if val_cbe > 0 and val_cbe <= 12:
                            score_cbe = [1, 2, 3, 5, 7, 9, 12, 15, 19, 25, 31, 52]
                            totalcargo += score_cbe[val_cbe - 1]

                        val_ts = pt[ti_ts]
                        if val_ts > 0 and val_ts <= 6:
                            score_ts = [1, 2, 3, 4, 5, 8]
                            totalcargo += score_ts[val_ts - 1]

                        r_value = int(totalcargo)
                        if techname == "relics":
                            r_value = int(totalcargo / 4)
                else:
                    tech_index = teh.get_tech_index(techname)

                    if tech_index >= 0:
                        r_value = pt[tech_index]

        return r_value

    def player_tech_set(self, p_playerid, techname, techvalue):
        playerid = str(p_playerid)
        tech_index = teh.get_tech_index(techname)

        if tech_index >= 0 and tech_index < 9900:
            self.ensure_player_created(playerid)
            pt = self.players[playerid]["tech"]
            pt[tech_index] = int(techvalue)

            self.flag_persdata_dirty = True

    def player_info_get(self, p_playerid, infoname):
        playerid = str(p_playerid)
        r_value = None

        if playerid in self.players:
            p = self.players[playerid]

            if "info" in p:
                pi = p["info"]

                if infoname in pi:
                    r_value = pi[infoname]

        return r_value

    def player_info_set(self, p_playerid, infoname, infovalue):
        playerid = str(p_playerid)
        self.ensure_player_created(playerid)
        pi = self.players[playerid]["info"]
        pi[infoname] = infovalue

        self.flag_persdata_dirty = True

    async def command_group_add(self, params):
        return_list = []

        who_list_scratch = list()
        other_list = list()
        memb_list = list()
        role_list = list()
        self.parse_who(
            params,
            who_list_scratch,
            memb_list=memb_list,
            role_list=role_list,
            other=other_list,
        )

        if other_list and (memb_list or role_list):
            group_name = other_list[0]
            if group_name not in self.groups_protected:
                self.group_set(
                    group_name,
                    " ".join(
                        [f"<@!{mm}>" for mm in memb_list]
                        + [f"<@&{rr}>" for rr in role_list]
                    ),
                )

                return_list.append(f"Group {group_name} added")
                self.flag_config_dirty = True

        return return_list

    async def command_group_remove(self, params):
        return_list = []

        if params:
            group_name = params[0]
            if group_name in self.groups and group_name not in self.groups_protected:
                self.group_remove(group_name)

                return_list.append(f"Group {group_name} removed")
                self.flag_config_dirty = True

        return return_list

    async def command_group_list(self, params):
        return_list = []

        group_strs = list()

        for gname, grp in self.groups.items():
            who_list_scratch = list()
            memb_list = list()
            role_list = list()
            self.parse_who(
                grp["defn"].split(" "),
                who_list_scratch,
                memb_list=memb_list,
                role_list=role_list,
            )

            group_strs.append(
                gname
                + ": "
                + ", ".join(
                    [self.member_name_from_id(mm) for mm in memb_list]
                    + [str(self.role_from_id(rr)) for rr in role_list]
                )
            )

        if group_strs:
            return_list.append("\n".join(group_strs))

        return return_list

    async def command_rolemem_add(self, params):
        return_list = []

        who_list_scratch = list()
        memb_list = list()
        role_list = list()
        self.parse_who(
            params,
            who_list_scratch,
            memb_list=memb_list,
            role_list=role_list,
        )

        if len(role_list) > 0 and len(memb_list) > 0:
            flag_added = False

            for memb_id in memb_list:
                memb = self.member_from_id(memb_id)
                if memb is not None:
                    list_roles = list()
                    for role_id in role_list:
                        role = self.role_from_id(role_id)
                        if role is not None:
                            if role not in memb.roles:
                                list_roles.append(role)

                    if list_roles:
                        # print(f"MEGAFONE list_roles {list_roles}")
                        # print(f"MEGAFONE t list_roles {type(list_roles)}")
                        # print(f"MEGAFONE t0 list_roles {type(list_roles[0])}")
                        await memb.add_roles(
                            *list_roles,
                            reason="StatisticalMe member adding role(s)",
                            atomic=True,
                        )
                        flag_added = True

            if flag_added:
                return_list.append("Added")

                msg_list = []
                for role_id in role_list:
                    role = self.role_from_id(role_id)
                    if role is not None:
                        msg_list.append(f"Role: {role.name}")
                        msg_list.append(
                            "  members: "
                            + " ".join([f"<@!{memb.id}>" for memb in role.members])
                        )

                return_list.append("\n".join(msg_list))
            else:
                return_list.append("No adds")
        else:
            return_list.append("No members and/or roles")

        return return_list

    async def command_rolemem_remove(self, params):
        return_list = []

        who_list_scratch = list()
        memb_list = list()
        role_list = list()
        self.parse_who(
            params,
            who_list_scratch,
            memb_list=memb_list,
            role_list=role_list,
        )

        if len(role_list) > 0 and len(memb_list) > 0:
            flag_removed = False

            for memb_id in memb_list:
                memb = self.member_from_id(memb_id)
                if memb is not None:
                    list_roles = list()
                    for role_id in role_list:
                        role = self.role_from_id(role_id)
                        if role is not None:
                            if role in memb.roles:
                                list_roles.append(role)

                    if list_roles:
                        await memb.remove_roles(
                            *list_roles,
                            reason="StatisticalMe member removing role(s)",
                            atomic=True,
                        )
                        flag_removed = True

            if flag_removed:
                return_list.append("Removed")
            else:
                return_list.append("No removals")
        else:
            return_list.append("No members or roles")

        return return_list

    async def command_rolemem_list(self, params):
        return_list = []

        who_list_scratch = list()
        role_list = list()
        self.parse_who(
            params,
            who_list_scratch,
            role_list=role_list,
        )

        if len(role_list) > 0:
            msg_list = []
            for role_id in role_list:
                role = self.role_from_id(role_id)
                if role is not None:
                    msg_list.append(f"Role: {role.name}")
                    member_names = [
                        self.member_name_from_id(memb.id) for memb in role.members
                    ]
                    member_names.sort()
                    msg_list.append("  members: " + ", ".join(member_names))

            return_list.append("\n".join(msg_list))
        else:
            return_list.append("No roles")

        return return_list

    def timedelta_to_days_secs(self, timedelta_s):
        td_days = 0
        td_secs = 0

        if timedelta_s > 0:
            td = int(timedelta_s)

            td_days = int(td / int(86400))
            if td_days > 0:
                td -= td_days * int(86400)

            td_secs = td

        return (td_days, td_secs)

    def timedelta_as_string(self, timedelta_s, show_sec=False):
        (td_days, td_secs) = self.timedelta_to_days_secs(timedelta_s)
        outp = list()

        if td_days >= 1:
            outp.append(str(td_days) + "d")

        if td_secs >= 1:
            sec = int(td_secs)
            hr = int(int(sec) / int(3600))
            if hr >= 1:
                outp.append(str(hr) + "h")
                sec -= hr * 3600

            mn = int(int(sec) / int(60))

            if show_sec:
                if mn >= 1:
                    outp.append(str(mn) + "m")
                    sec -= mn * 60

                outp.append(str(sec) + "s")
            else:
                outp.append(str(mn) + "m")

        return " ".join(outp)

    def timedelta_as_string2(self, timedelta_s):
        (td_days, td_secs) = self.timedelta_to_days_secs(timedelta_s)
        part_d = 0
        part_h = 0
        part_m = 0

        if td_days >= 1:
            part_d = int(td_days)

        if td_secs >= 1:
            sec = int(td_secs)

            part_h = int(int(sec) / int(3600))
            if part_h >= 1:
                sec -= part_h * 3600

            part_m = int(int(sec) / int(60))
            if part_m >= 1:
                sec -= part_m * 60

        tstr = None
        if part_d > 0:
            tstr = "{:d}:{:02d}:{:02d}".format(part_d, part_h, part_m)
        else:
            tstr = "{:2d}:{:02d}".format(part_h, part_m)

        return tstr

    def timedelta_from_strings(self, other_list):
        timed = 0

        for other in other_list:
            try1_match = self.timeparse_match1.search(other)
            if try1_match:
                m_id = int(try1_match.group(1))
                m_control = try1_match.group(2)

                if m_control == "d":
                    timed += m_id * 24 * 3600
                elif m_control == "h":
                    timed += m_id * 3600
                elif m_control == "m":
                    timed += m_id * 60
                else:
                    break
            else:
                try4_match = self.timeparse_match4.search(other)
                if try4_match:
                    timed += int(try4_match.group(1)) * 24 * 3600
                    timed += int(try4_match.group(2)) * 3600
                    timed += int(try4_match.group(3)) * 60
                else:
                    try2_match = self.timeparse_match2.search(other)
                    if try2_match:
                        timed += int(try2_match.group(1)) * 24 * 3600
                        timed += int(try2_match.group(2)) * 3600
                        timed += int(try2_match.group(3)) * 60
                    else:
                        try3_match = self.timeparse_match3.search(other)
                        if try3_match:
                            timed += int(try3_match.group(1)) * 3600
                            timed += int(try3_match.group(2)) * 60
                        else:
                            break

        return timed

    def test_background_update_needed(self):
        needed = False

        if len(self.ws) > 0:
            needed = True

        return needed

    def opportunistic_background_update_start(self):
        if not self.background_update_started and self.test_background_update_needed():
            self.background_update_all.start()
            self.background_update_started = True

    def opportunistic_background_update_stop(self):
        if self.background_update_started and not self.test_background_update_needed():
            self.background_update_all.stop()
            self.background_update_started = False

    @tasks.loop(seconds=5.0)
    async def background_update_all(self):
        # logger.debug('MEGAFONE background_update_all, counts: ws {wc}'.format(wc=len(self.ws)))

        self.time_now = smer.sme_time_now()

        # Update WhiteStars
        ws_over = list()

        for ws_name, ws_struct in self.ws.items():
            try:
                if "done" not in ws_struct or not ws_struct["done"]:
                    nova_time = smer.sme_time_from_string(ws_struct["nova_time"])

                    ws_time_str = ""

                    if (nova_time + 30) < self.time_now:
                        ws_struct["done"] = True
                        self.flag_config_dirty = True
                        ws_time_str = "over"
                        ws_over.append(ws_name)
                    else:
                        # Resolves to a minute, so add 30s here to cause a round up.
                        ws_time = nova_time + 30 - self.time_now
                        ws_time_str = self.timedelta_as_string(ws_time)

                    new_content = f"```\nNova time {ws_time_str}\n"

                    control_role = ws_struct["control_role"]
                    all_role = ws_struct["all_role"]

                    if control_role > 0 or all_role > 0:
                        role_list = []

                        if control_role > 0:
                            control_role_ob = self.role_from_id(control_role)
                            role_list.append(
                                "Leaders: @{}".format(str(control_role_ob))
                            )

                        if all_role > 0:
                            all_role_ob = self.role_from_id(all_role)
                            role_list.append("pilots: @{}".format(str(all_role_ob)))

                        new_content += ", ".join(role_list) + "\n"

                    if all_role > 0:
                        all_role_str = f"<@&{all_role}>"

                        newcont2 = await self.command_time_list(
                            [all_role_str], ws_info=ws_struct
                        )
                        if newcont2 and newcont2[0][:3] == "```":
                            new_content += newcont2[0][3:-3]

                        newcont2 = self.nicommand_ws_shiplist(
                            [all_role_str], ws_info=ws_struct
                        )
                        if newcont2 and newcont2[0][:3] == "```":
                            new_content += newcont2[0][3:-3]

                    new_content += "```"

                    if (
                        "old_content" not in ws_struct
                        or new_content != ws_struct["old_content"]
                    ):
                        ws_struct["old_content"] = new_content
                        self.flag_config_dirty = True

                        chan_ob = self.current_guild.get_channel(ws_struct["channel"])
                        if chan_ob is not None:
                            msg_id = ws_struct["message"]

                            msg_ob = None
                            if msg_id > 0:
                                try:
                                    msg_ob = await chan_ob.fetch_message(msg_id)
                                except discord.NotFound:
                                    msg_ob = None

                            if msg_ob is None:
                                msg_ob = await chan_ob.send(new_content)
                                msg_id = msg_ob.id
                                ws_struct["message"] = msg_id
                                self.flag_config_dirty = True
                            else:
                                await msg_ob.edit(content=new_content)

                            if "dirty" in ws_struct:
                                del ws_struct["dirty"]
                                self.flag_config_dirty = True
                        else:
                            ws_struct["done"] = True
                            self.flag_config_dirty = True
                            ws_time_str = "over"
                            ws_over.append(ws_name)

            except Exception:
                exc_type, exc_value, exc_tb = sys.exc_info()
                tbe = traceback.TracebackException(exc_type, exc_value, exc_tb)
                logger.error(
                    "background_update_all Exception processing WhiteStar "
                    + ws_name
                    + "\n"
                    + "".join(tbe.format())
                )

        for ws_name in ws_over:
            try:
                self.nicommand_ws_remove_impl(ws_name)
            except Exception:
                exc_type, exc_value, exc_tb = sys.exc_info()
                tbe = traceback.TracebackException(exc_type, exc_value, exc_tb)
                logger.error(
                    "background_update_all Exception removing WhiteStar "
                    + ws_name
                    + "\n"
                    + "".join(tbe.format())
                )

        # Opportunistic send out messages queued
        if len(self.messages_out) > 0:
            await self.send_out_messages()

        self.opportunistic_save()

    async def command_ws_add(self, params):
        return_list = []

        who_list_scratch = list()
        other_list = list()
        role_list = list()
        self.parse_who(params, who_list_scratch, role_list=role_list, other=other_list)

        ws_name = None
        wsname_match = self.ws_name_match.search(str(self.current_channel))

        if other_list and wsname_match:
            ws_name = wsname_match.group(1)

            nova_timedelta = self.timedelta_from_strings(other_list)

            if nova_timedelta < (1 * 60) or nova_timedelta > (5 * 24 * 3600):
                return_list.append("Error: Nova time out of good range")
            else:
                control_role = 0
                assist_group = ""
                if len(role_list) >= 1:
                    control_role = role_list[0]
                    assist_group = f"ws_{ws_name}_assist"
                    self.group_set(
                        assist_group, " ".join(["<@&{rid}>".format(rid=control_role)])
                    )

                all_role = 0
                if len(role_list) >= 2:
                    all_role = role_list[1]

                nova_time = self.time_now + nova_timedelta

                self.ws[ws_name] = {
                    # inputs
                    "control_role": control_role,
                    "all_role": all_role,
                    "nova_time": smer.sme_time_as_string(int(nova_time)),
                    # other state
                    "old_content": "",
                    "assist_group": assist_group,
                    "channel": self.current_channel.id,
                    "message": 0,
                    "greens": {},
                    "reds": {},
                    "done": False,
                }

                return_list.append(f"WhiteStar {ws_name} added")
                self.flag_config_dirty = True

                self.opportunistic_background_update_start()

        return return_list

    async def command_ws_remove(self, params):
        return_list = []

        who_list_scratch = list()
        role_list = list()
        self.parse_who(params, who_list_scratch, role_list=role_list)

        ws_name = None
        wsname_match = self.ws_name_match.search(str(self.current_channel))

        if wsname_match:
            ws_name = wsname_match.group(1)
            return_list += self.nicommand_ws_remove_impl(ws_name)

        return return_list

    def nicommand_ws_remove_impl(self, ws_name):
        return_list = []

        if ws_name in self.ws:
            ws_struct = self.ws[ws_name]
            self.group_remove(ws_struct["assist_group"])

            del self.ws[ws_name]

            self.opportunistic_background_update_stop()

            return_list.append(f"WhiteStar {ws_name} removed")
            self.flag_config_dirty = True

        return return_list

    async def command_ws_list(self, params):
        ws_strlist = []

        for ws_name, ws_struct in self.ws.items():
            str_list = []

            nova_time = smer.sme_time_from_string(ws_struct["nova_time"])

            ws_time_str = ""

            if (nova_time + 30) < self.time_now:
                ws_time_str = "over"
            else:
                # Resolves to a minute, so add 30s here to cause a round up.
                ws_time = nova_time + 30 - self.time_now
                ws_time_str = self.timedelta_as_string(ws_time)

            str_list.append("\t{:3}, Nova time: {}".format(ws_name, ws_time_str))

            control_role = ws_struct["control_role"]
            if control_role > 0:
                control_role_ob = self.role_from_id(control_role)
                str_list.append(f"leaders: @{str(control_role_ob)}")

            all_role = ws_struct["all_role"]
            if all_role > 0:
                all_role_ob = self.role_from_id(all_role)
                str_list.append(f"pilots: @{str(all_role_ob)}")

            ws_strlist.append(
                ", ".join(str_list) + " in <#{cid}>".format(cid=ws_struct["channel"])
            )

        if not ws_strlist:
            ws_strlist = ["\tempty"]

        return ["WhiteStar list:\n" + "\n".join(ws_strlist)]

    async def command_ws_roles(self, params):
        return_list = []

        who_list_scratch = list()
        role_list = list()
        self.parse_who(params, who_list_scratch, role_list=role_list)

        ws_name = None
        wsname_match = self.ws_name_match.search(str(self.current_channel))

        if wsname_match and len(role_list) >= 2:
            ws_name = wsname_match.group(1)
            ws_struct = self.ws[ws_name]

            control_role = role_list[0]
            all_role = role_list[1]
            assist_group = f"ws_{ws_name}_assist"

            ws_struct["control_role"] = control_role
            ws_struct["all_role"] = all_role
            ws_struct["assist_group"] = assist_group
            self.group_set(
                assist_group, " ".join(["<@&{rid}>".format(rid=control_role)])
            )

            return_list.append(f"WhiteStar roles added to {ws_name}")
            self.flag_config_dirty = True

        return return_list

    async def command_ws_ship(self, params):
        return_list = []

        who_list_good = list()
        other_list = list()
        return_list = return_list + self.parse_who(
            params, who_list_good, other=other_list
        )

        ws_name = None
        wsname_match = self.ws_name_match.search(str(self.current_channel))

        if wsname_match:
            ws_name = wsname_match.group(1)
            if ws_name in self.ws:
                ws_struct = self.ws[ws_name]
                nova_time = smer.sme_time_from_string(ws_struct["nova_time"])

                # two dicts, one 'green' keyed by pilotid, one 'red' keyed by string
                # in each case storing a 4 string tuple:
                #   (bs ship type in, bs closed countdown, sup ship type in, sup closed countdown)
                if "greens" not in ws_struct:
                    ws_struct["greens"] = dict()

                ws_greens = ws_struct["greens"]

                if "reds" not in ws_struct:
                    ws_struct["reds"] = dict()

                ws_reds = ws_struct["reds"]

                # if not self.auth_chief():
                #     who_list_good = [self.current_author.id]

                time_list = list()
                s_cmd = None
                s_shiptype = None
                s_flagship = False
                s_timertype = None
                s_enemy = None

                for ostr_withcase in other_list:
                    ostr = smer.sme_utils_normalize_caseless(ostr_withcase)
                    if ostr in ["in", "out", "timer", "dead", "add", "remove"]:
                        s_cmd = ostr
                    elif ostr in ["bs", "bat", "battleship", "fs", "flagship"]:
                        s_shiptype = "bs"
                        if ostr in ["fs", "flagship"]:
                            s_flagship = True
                    elif ostr in ["ts", "tr", "tran", "trans", "transport"]:
                        s_shiptype = "ts"
                    elif ostr in ["ms", "mn", "mr", "min", "miner"]:
                        s_shiptype = "mn"
                    elif ostr in ["at", "nova", "ago", "hence"]:
                        s_timertype = ostr
                    elif ostr_withcase[0] == "!":
                        s_enemy = ostr_withcase
                    else:
                        time_list.append(ostr)

                s_friend = 0
                if len(who_list_good) > 0:
                    s_friend = who_list_good[0]
                elif s_enemy is None:
                    s_friend = self.current_author.id

                # logger.debug('MEGAFONE ship what {sc} {ss} {st}'.format(sc=s_cmd, ss=s_shiptype, st=s_timertype))
                # logger.debug('MEGAFONE ship who {sf} {se}'.format(sf=s_friend, se=s_enemy))

                if s_friend != 0 and s_enemy is not None:
                    return_list.append(
                        "Crap: Can not work on friend and enemy at same time"
                    )
                elif s_timertype is not None and s_timertype not in [
                    "at",
                    "nova",
                    "ago",
                    "hence",
                ]:
                    return_list.append(
                        "Crap: Need a time code like: at, nova, ago, hence"
                    )
                else:
                    if s_cmd is not None:
                        if s_cmd == "add":
                            if s_enemy is not None:
                                if s_enemy not in ws_reds:
                                    ws_reds[s_enemy] = {
                                        "bship": "",
                                        "bdelay": "",
                                        "sship": "",
                                        "sdelay": "",
                                    }
                                    self.flag_config_dirty = True
                            else:
                                return_list.append(
                                    "Crap: Need enemy name with !, like: !Ralph"
                                )
                        elif s_cmd == "remove":
                            if s_enemy is not None:
                                if s_enemy in ws_reds:
                                    del ws_reds[s_enemy]
                                    self.flag_config_dirty = True
                            else:
                                return_list.append(
                                    "Crap: Need enemy name with !, like: !Ralph"
                                )
                        else:
                            if s_shiptype is not None:
                                given_time = self.timedelta_from_strings(time_list)
                                if len(time_list) == 0:
                                    s_timertype = "hence"
                                    given_time = 0

                                open_time = None
                                pilot_data = {
                                    "bship": "",
                                    "bdelay": "",
                                    "sship": "",
                                    "sdelay": "",
                                }

                                if s_timertype is not None and s_timertype == "ago":
                                    open_time = self.time_now - given_time
                                else:
                                    if s_cmd == "timer":
                                        # Command timer has a different default timertype
                                        if s_timertype is not None and s_timertype in [
                                            "at",
                                            "nova",
                                        ]:
                                            open_time = nova_time - given_time
                                        else:
                                            # Default timertype: in
                                            open_time = self.time_now + given_time
                                    else:
                                        if (
                                            s_timertype is not None
                                            and s_timertype == "hence"
                                        ):
                                            open_time = self.time_now + given_time
                                        else:
                                            # Default timertype: at, nova
                                            open_time = nova_time - given_time

                                if s_cmd == "in":
                                    open_time += 2 * 3600
                                elif s_cmd == "dead":
                                    if s_flagship:
                                        open_time += 16 * 3600
                                    else:
                                        open_time += 18 * 3600

                                if open_time > nova_time:
                                    open_time = nova_time

                                open_time_str = smer.sme_time_as_string(int(open_time))

                                if s_enemy is not None:
                                    if s_enemy in ws_reds:
                                        pilot_data = ws_reds[s_enemy]
                                else:
                                    if s_friend in ws_greens:
                                        pilot_data = ws_greens[s_friend]

                                shipkey = "sship"
                                delaykey = "sdelay"
                                if s_shiptype == "bs":
                                    shipkey = "bship"
                                    delaykey = "bdelay"

                                if s_cmd == "in":
                                    pilot_data[shipkey] = s_shiptype
                                elif s_cmd != "timer":
                                    pilot_data[shipkey] = ""

                                pilot_data[delaykey] = open_time_str

                                if s_enemy is not None:
                                    ws_reds[s_enemy] = pilot_data
                                else:
                                    ws_greens[s_friend] = pilot_data

                                self.flag_config_dirty = True
                    else:
                        return_list.append(
                            "Crap: Need command, one of: {}".format(
                                ["in", "out", "dead", "timer", "add", "remove"]
                            )
                        )

        if len(return_list) < 1:
            return_list.append("dented-control-message:delete-original-message")

        return return_list

    def nicommand_ws_shiplist(self, params, ws_info=None):
        return_list = []

        # who_list_good = list()
        # return_list = return_list + self.parse_who(params, who_list_good)

        # if ws_info is None:
        #     if len(who_list_good) == 0:
        #         who_list_good = [self.current_author.id]

        #     if not str(self.current_channel) in self.ok_channels and not self.auth_chief():
        #         who_list_good = [self.current_author.id]

        if ws_info is not None and "pilot_order" in ws_info:
            # Friends, greens
            green_list = []
            if "greens" in ws_info:
                ws_greens = ws_info["greens"]
                for pkey in ws_info["pilot_order"]:
                    if pkey not in ws_greens:
                        ws_greens[pkey] = {
                            "bship": "",
                            "bdelay": "",
                            "sship": "",
                            "sdelay": "",
                        }
                        self.flag_config_dirty = True

                    pilot_name = self.member_name_from_id(pkey)
                    user_info = self.list_one_pilot(pilot_name, ws_greens[pkey])
                    green_list.append(user_info)

            # Enemies, reds
            red_list = []
            if "reds" in ws_info:
                ws_reds = ws_info["reds"]

                red_pilots = list(ws_reds.keys())
                red_pilots.sort()
                for pilot_name in red_pilots:
                    user_info = self.list_one_pilot(pilot_name, ws_reds[pilot_name])
                    red_list.append(user_info)

            if green_list or red_list:
                t_header = ["Ships", "BS", "Supp"]
                t_align = ["l", "l", "l"]

                return_list += sme_table.draw(t_header, t_align, green_list + red_list)

        return return_list

    def list_one_pilot(self, pilot_name, pilot_data):
        b_delay = ""
        b_until_str = pilot_data["bdelay"]
        if b_until_str is not None and len(b_until_str) > 2:
            away_until = smer.sme_time_from_string(b_until_str)
            if self.time_now < away_until:
                td = away_until - self.time_now
                b_delay = self.timedelta_as_string2(td + 15)
            else:
                pilot_data["bdelay"] = ""
                self.flag_config_dirty = True

        b_ship = pilot_data["bship"]
        if len(b_ship) == 0 and len(b_delay) == 0:
            b_ship = "!"

        s_delay = ""
        s_until_str = pilot_data["sdelay"]
        if s_until_str is not None and len(s_until_str) > 2:
            away_until = smer.sme_time_from_string(s_until_str)
            if self.time_now < away_until:
                td = away_until - self.time_now
                s_delay = self.timedelta_as_string2(td + 15)
            else:
                pilot_data["sdelay"] = ""
                self.flag_config_dirty = True

        s_ship = pilot_data["sship"]
        if len(s_ship) == 0 and len(s_delay) == 0:
            s_ship = "!"

        # p_name = copy.copy(pilot_name)
        # if len(p_name) > 11:
        #     p_name = p_name[:11]

        return [
            "{:.11}".format(pilot_name),
            "{:1.1} {:>5}".format(b_ship, b_delay),
            "{:1.1} {:>5}".format(s_ship, s_delay),
        ]

    async def command_tech_set(self, params):
        return_list = []

        who_list_good = list()
        what_list_good = list()
        value_list = list()
        return_list = return_list + self.parse_who_what_int(
            params, who_list_good, what_list_good, value_list
        )

        if len(who_list_good) == 0:
            who_list_good = [self.current_author.id]

        if str(self.current_channel) not in self.ok_channels and not self.auth_chief():
            who_list_good = [self.current_author.id]

        if len(who_list_good) > 0 and len(what_list_good) > 0:
            if len(value_list) == len(what_list_good):
                old_value_list = list()

                for who in who_list_good:
                    self.player_info_set(
                        who, "last_name", self.member_name_from_id(who)
                    )

                    from_str = smer.sme_time_as_string(self.time_now)
                    self.player_info_set(who, "last_tech_update", from_str)

                    for what, val in zip(what_list_good, value_list):
                        old_value_list.append(self.player_tech_get(who, what))
                        self.player_tech_set(who, what, val)

                if len(value_list) == 1:
                    return_list.append(
                        "Value set to {nv} (was {ov})".format(
                            nv=value_list[0], ov=old_value_list[0]
                        )
                    )
                else:
                    return_list.append(
                        "Values set to {nl} (was {ol})".format(
                            nl=value_list, ol=old_value_list
                        )
                    )

                self.persdata_save()
            else:
                return_list.append(
                    "Got {go} value(s) when I expected {ex}".format(
                        go=len(value_list), ex=len(what_list_good)
                    )
                )

        return return_list

    async def command_tech_report(self, params):
        return_list = []

        who_list_good = list()
        what_list_good = list()
        value_list = list()
        other_list = list()
        return_list = return_list + self.parse_who_what_int(
            params, who_list_good, what_list_good, value_list, other=other_list
        )

        if len(who_list_good) == 0:
            who_list_good = [self.current_author.id]

        if str(self.current_channel) not in self.ok_channels and not self.auth_chief():
            who_list_good = [self.current_author.id]

        flag_csv = False
        if "--csv" in other_list or "+csv" in other_list:
            flag_csv = True

        if len(who_list_good) > 0 and len(what_list_good) > 0:
            user_list = []

            for who in who_list_good:
                user_list.append(
                    [self.member_name_from_id(who)]
                    + [self.player_tech_get(who, what) for what in what_list_good]
                )

            if not flag_csv:
                user_list.sort(key=lambda x: x[1], reverse=True)

            what_names = [teh.get_tech_name(what) for what in what_list_good]
            return_list += sme_table.draw(
                ["User"] + what_names,
                ["l"] + ["r"] * len(what_list_good),
                user_list,
                flag_csv=flag_csv,
            )

        return return_list

    async def command_tech_list(self, params):
        # sometimes known as !gt or tech get
        return_list = []

        who_list_good = list()
        what_list_good = list()
        value_list = list()
        other_list = list()
        return_list = return_list + self.parse_who_what_int(
            params, who_list_good, what_list_good, value_list, other=other_list
        )

        if len(who_list_good) == 0:
            who_list_good = [self.current_author.id]

        if str(self.current_channel) not in self.ok_channels and not self.auth_chief():
            who_list_good = [self.current_author.id]

        flag_csv = False
        if "--csv" in other_list or "+csv" in other_list:
            flag_csv = True

        if "--all" in other_list or "+all" in other_list or len(what_list_good) == 0:
            what_list_good = teh.tech_keys

        # if len(what_list_good) == 0:
        #     return_list.append('Did you mean: !gt +all')

        if len(who_list_good) > 0 and len(what_list_good) > 0:
            user_list = []

            last_tech_key = ""
            for what in what_list_good:
                row_data = [self.player_tech_get(who, what) for who in who_list_good]
                if row_data != ([0] * len(row_data)) or flag_csv:
                    if flag_csv:
                        prefix = ""
                    else:
                        prefix = "  "
                        if teh.is_range_change2(last_tech_key, what):
                            prefix = "- "

                    user_list.append([prefix + teh.get_tech_name(what)] + row_data)
                    last_tech_key = what

            who_names = [self.member_name_from_id(wh) for wh in who_list_good]
            return_list += sme_table.draw(
                ["Tech"] + who_names,
                ["l"] + ["r"] * len(who_list_good),
                user_list,
                flag_csv=flag_csv,
            )

        return return_list

    async def command_time_set(self, params):
        return_list = []

        who_list_good = list()
        other_list = list()
        return_list = return_list + self.parse_who(
            params, who_list_good, other=other_list
        )

        if len(who_list_good) == 0:
            who_list_good = [self.current_author.id]

        if str(self.current_channel) not in self.ok_channels and not self.auth_chief():
            who_list_good = [self.current_author.id]

        if len(who_list_good) > 0:
            if len(other_list) > 0:
                tzstr = str(other_list[0])
                prefix = smer.sme_utils_normalize_caseless(tzstr[:3])
                if prefix in ["utc", "gmt", "fof"] and len(other_list) > 1:
                    tzstr = tzstr + other_list[1]
                    other_list = other_list[2:]
                else:
                    other_list = other_list[1:]

                if bool(smer.sme_time_is_valid_timezone(tzstr)):
                    self.player_info_set(who_list_good[0], "timezone", tzstr)
                    return_list.append("OK")

        return return_list

    async def command_time_get(self, params):
        return_list = []

        who_list_good = list()
        return_list = return_list + self.parse_who(params, who_list_good)

        if len(who_list_good) == 0:
            who_list_good = [self.current_author.id]

        if str(self.current_channel) not in self.ok_channels and not self.auth_chief():
            who_list_good = [self.current_author.id]

        if len(who_list_good) > 0:
            user_list = []

            for pkey in who_list_good:
                user_list.append(
                    [
                        self.member_name_from_id(pkey),
                        self.player_info_get(pkey, "timezone"),
                    ]
                )

            return_list += sme_table.draw(["User", "timezone"], ["l", "l"], user_list)

        return return_list

    async def command_time_list(self, params, ws_info=None):
        return_list = []

        who_list_good = list()
        return_list = return_list + self.parse_who(params, who_list_good)

        if ws_info is None:
            if len(who_list_good) == 0:
                who_list_good = [self.current_author.id]

            if (
                str(self.current_channel) not in self.ok_channels
                and not self.auth_chief()
            ):
                who_list_good = [self.current_author.id]

        if len(who_list_good) > 0:
            user_list = []

            for pkey in who_list_good:
                timestr = "timeless"
                t_sorting = int(0)
                tz_str = self.player_info_get(pkey, "timezone")
                if tz_str is not None:
                    try:
                        converted0, converted1 = str(
                            smer.sme_time_convert_to_timezone(self.time_now, tz_str)
                        ).split(",")
                        if len(converted0) > 0 and len(converted1) > 0:
                            timestr = str(converted0)
                            t_sorting = int(converted1)
                    except ValueError:
                        pass

                away_result = ""
                away_msg_str = ""
                away_until_str = self.player_info_get(pkey, "away_until")
                if away_until_str is not None and len(away_until_str) > 2:
                    away_until = smer.sme_time_from_string(away_until_str)
                    if self.time_now < away_until:
                        (td_days, td_secs) = self.timedelta_to_days_secs(
                            away_until - self.time_now
                        )
                        if td_days >= 1:
                            away_result = away_result + f"{td_days}d "

                        sec = td_secs
                        if sec >= 3600:
                            hrs = int(sec / 3600)
                            away_result = away_result + f"{hrs}h "
                            sec = sec - hrs * 3600

                        mins = int(sec / 60)
                        away_result = away_result + f"{mins}m"

                        away_msg_str = self.player_info_get(pkey, "away_msg")
                        if away_msg_str is None:
                            away_msg_str = ""

                # Use '\U0001F451' for a unicode emoji of Crown.
                pilot_name = self.member_name_from_id(pkey)
                if ws_info is not None:
                    if self.group_contains_member(ws_info["assist_group"], pkey):
                        pilot_name = "+ " + pilot_name
                    else:
                        pilot_name = "  " + pilot_name

                user_info = [
                    pilot_name,
                    timestr,
                    away_result,
                    t_sorting,
                    pkey,
                    away_msg_str,
                ]
                user_list.append(user_info)

            user_list.sort(key=lambda x: x[3], reverse=True)

            t_header = ["User", "time"]
            t_align = ["l", "l"]
            t_user_list = list()

            sumlen = 2
            for ee in user_list:
                if sumlen < 3 and len(ee[2]) > 0:
                    sumlen = 3

                if sumlen < 4 and len(ee[5]) > 0:
                    sumlen = 4

            if sumlen <= 2:
                t_user_list = [[ee[0], ee[1]] for ee in user_list]
            elif sumlen <= 3:
                t_header = ["User", "time", "away"]
                t_align = ["l", "l", "r"]
                t_user_list = [[ee[0], ee[1], ee[2]] for ee in user_list]
            else:
                t_header = ["User", "time", "away", "reason"]
                t_align = ["l", "l", "r", "l"]
                t_user_list = [[ee[0], ee[1], ee[2], ee[5]] for ee in user_list]

            return_list += sme_table.draw(t_header, t_align, t_user_list)

            if ws_info is not None and "pilot_order" not in ws_info:
                ws_info["pilot_order"] = [pi[4] for pi in user_list]
                ws_info["dirty"] = True

        return return_list

    async def command_time_away(self, params):
        return_list = []

        who_list_good = list()
        other_list = list()
        return_list = return_list + self.parse_who(
            params, who_list_good, other=other_list
        )

        away_player_id = 0
        if self.auth_chief():
            if len(who_list_good) == 0:
                away_player_id = self.current_author.id
            elif len(who_list_good) == 1:
                away_player_id = who_list_good[0]
            else:
                return_list.append("Sorry about that chief. Can only do one.")
        else:
            if len(who_list_good) == 0:
                away_player_id = self.current_author.id
            else:
                return_list.append("Oh crap. Will only work on self.")

        if away_player_id > 0 and len(other_list) >= 1 and is_float(other_list[0]):
            delay = float(other_list[0])

            if delay <= 36.0:
                from_str = smer.sme_time_as_string(self.time_now)
                self.player_info_set(away_player_id, "away_from", from_str)

                until_time = self.time_now + (delay * 3600)
                until_str = smer.sme_time_as_string(int(until_time))
                self.player_info_set(away_player_id, "away_until", until_str)

                if len(other_list) >= 2:
                    self.player_info_set(
                        away_player_id, "away_msg", " ".join(other_list[1:])
                    )
                else:
                    self.player_info_set(away_player_id, "away_msg", "")

                return_list.append("OK")
            else:
                return_list.append("Away denied. Engage leaders for therapy.")

        return return_list

    async def command_time_back(self, params):
        return_list = []

        who_list_good = list()
        other_list = list()
        return_list = return_list + self.parse_who(
            params, who_list_good, other=other_list
        )

        if len(who_list_good) > 0:
            return_list.append("Oh crap. Will only work on self.")
        else:
            self.player_info_set(self.current_author.id, "away_from", "")
            self.player_info_set(self.current_author.id, "away_until", "")
            self.player_info_set(self.current_author.id, "away_msg", "")

            return_list.append("OK")

        return return_list

    async def command_time_checkin(self, params):
        return_list = []
        return_ok = False

        who_list_good = list()
        other_list = list()
        return_list = return_list + self.parse_who(
            params, who_list_good, other=other_list
        )

        if not self.auth_chief():
            who_list_good = list()
            return_list.append("Only for chiefs")

        if len(who_list_good) > 0:
            delay = 1
            from_str = smer.sme_time_as_string(self.time_now)
            until_str = smer.sme_time_as_string(int(self.time_now + (delay * 3600)))
            instigator_name = self.member_name_from_id(self.current_author.id)
            who_list_away = list()

            for pkey in who_list_good:
                flag_away = False
                away_until_str = self.player_info_get(pkey, "away_until")
                if away_until_str is not None and len(away_until_str) > 2:
                    away_until = smer.sme_time_from_string(away_until_str)
                    if self.time_now < away_until:
                        flag_away = True

                if flag_away:
                    who_list_away.append(pkey)
                else:
                    return_ok = True
                    self.player_info_set(pkey, "checkin_from", from_str)
                    self.player_info_set(pkey, "checkin_by", until_str)

                    memb = self.member_from_id(pkey)
                    if memb is not None:
                        msg_out = f"{instigator_name} wants you to check in during the next hour"
                        if len(other_list) >= 1:
                            msg_out += "\n" + " ".join(other_list)

                        self.queue_msg_for_send_out(
                            memb,
                            msg_out,
                        )

            if who_list_away:
                name_list = [self.member_name_from_id(pkey) for pkey in who_list_away]
                if len(name_list) > 1:
                    return_list.append(", ".join(name_list) + " are all away")
                else:
                    return_list.append(name_list[0] + " is away")

            if return_ok and not return_list:
                return_list.append("OK")

        return return_list

    async def command_pilot_lastup(self, params):
        return_list = []

        who_list_good = list()
        other_list = list()
        return_list = return_list + self.parse_who(
            params, who_list_good, other=other_list
        )

        if len(who_list_good) == 0:
            who_list_good = [self.current_author.id]

        if "--not" in other_list or "+not" in other_list:
            all_who = set()
            for pkey in self.players:
                all_who.add(int(pkey))

            who_set = set(who_list_good)
            who_list_good = list(all_who - who_set)

        if str(self.current_channel) not in self.ok_channels and not self.auth_chief():
            who_list_good = [self.current_author.id]

        if len(who_list_good) > 0:
            user_list = []

            for pkey in who_list_good:
                lup_result = float(0.0)
                lup_was_str = self.player_info_get(pkey, "last_tech_update")
                if lup_was_str is not None and len(lup_was_str) > 2:
                    lup_was = smer.sme_time_from_string(lup_was_str)
                    if self.time_now > lup_was:
                        (td_days, td_secs) = self.timedelta_to_days_secs(
                            self.time_now - lup_was
                        )
                        if td_days >= 1:
                            lup_result = lup_result + float(td_days)

                        lup_result = lup_result + float(td_secs) / float(86400.0)

                user_list.append([self.member_name_from_id(pkey), lup_result])

            user_list.sort(key=lambda x: x[1], reverse=True)

            return_list += sme_table.draw(
                ["User", "days since update"], ["l", "l"], user_list
            )

        return return_list

    async def command_score(self, params):
        return_list = []

        who_list_good = list()
        other_list = list()
        return_list = return_list + self.parse_who(
            params, who_list_good, other=other_list
        )

        if len(who_list_good) == 0:
            who_list_good = [self.current_author.id]

        if str(self.current_channel) not in self.ok_channels and not self.auth_chief():
            who_list_good = [self.current_author.id]

        score_key = "210918"
        flag_detail = False
        flagged_whotruncated = False
        if len(other_list) > 0:
            new_key = other_list[0]
            if new_key in self.weights:
                score_key = new_key

            if "--detail" in other_list or "+detail" in other_list:
                flag_detail = True

                if len(who_list_good) > 4:
                    flagged_whotruncated = True
                    del who_list_good[4:]

        flag_wspoints210918 = False
        if score_key == "210918":
            flag_wspoints210918 = True

        flag_wspoints201206 = False
        if score_key == "201206":
            flag_wspoints201206 = True

        ww = self.weights[score_key]

        user_list = []

        t_header = ["User", score_key]

        for pkey in who_list_good:
            pp = self.players[str(pkey)]
            ppt = pp["tech"]
            accum = 0

            try:
                if flag_wspoints201206:
                    faccum = list()
                    detail_aa = []
                    detail_mi = []
                    detail_s1 = []
                    detail_s2 = []
                    detail_we = []
                    detail_sh = []

                    # relics, entrust, dispatch, data, relicdrone
                    for tkey in ["relics", "entrust", "dispatch", "dart", "relicdrone"]:
                        if tkey in ww:
                            tweights = ww[tkey]
                            tval = self.player_tech_get(pkey, tkey)
                            if tval > 0:
                                score = tweights[tval - 1]
                                faccum.append(float(score))
                                if flag_detail:
                                    detail_aa.append(f"{tkey} {score}")

                    # mining
                    otherminingtech = list()
                    ml1 = teh.tech_key_range_list("mining")
                    for mtkey in ml1:
                        score = 0
                        if mtkey in ww:
                            tweights = ww[mtkey]
                            tval = self.player_tech_get(pkey, mtkey)
                            if tval > 0:
                                score = tweights[tval - 1]

                        if score > 0:
                            otherminingtech.append([mtkey, score])

                    if len(otherminingtech) > 0:
                        otherminingtech.sort(key=lambda x: x[1], reverse=True)
                        minerlvl = self.player_tech_get(pkey, "miner")
                        mcount = 0
                        if minerlvl >= 2 and minerlvl <= 6:
                            mcount = minerlvl - 1

                        fscore = float(0.0)

                        mmax = len(otherminingtech)
                        mhi = mcount
                        if mhi > mmax:
                            mhi = mmax

                        for zz in range(0, mhi):
                            iscore = float(otherminingtech[zz][1])
                            fscore += iscore
                            if flag_detail:
                                detail_mi.append(
                                    "{tn} {ts}".format(
                                        tn=otherminingtech[zz][0], ts=iscore
                                    )
                                )

                        if mcount < mmax:
                            mhi = mcount * 2 - 2
                            if mhi > mmax:
                                mhi = mmax

                            for zz in range(mcount, mhi):
                                iscore = float(otherminingtech[zz][1]) * 0.5
                                fscore += iscore
                                if flag_detail:
                                    detail_mi.append(
                                        "{tn} {ts}".format(
                                            tn=otherminingtech[zz][0], ts=iscore
                                        )
                                    )

                        faccum.append(fscore)

                    # support
                    bslvl = self.player_tech_get(pkey, "bs")
                    if bslvl >= 2 and bslvl <= 6:
                        scount = bslvl - 1

                        techlist = teh.tech_key_range_list("support")

                        supporttech = list()
                        for tkey in techlist:
                            score = 0
                            if tkey in ww:
                                tweights = ww[tkey]
                                tval = self.player_tech_get(pkey, tkey)
                                if tval > 0:
                                    score = tweights[tval - 1]

                            if score > 0:
                                supporttech.append([tkey, score])

                        if len(supporttech) > 0:
                            supporttech.sort(key=lambda x: x[1], reverse=True)

                            fscore = float(0.0)

                            smax = len(supporttech)
                            shi = scount
                            if shi > smax:
                                shi = smax

                            for zz in range(0, shi):
                                iscore = float(supporttech[zz][1])
                                fscore += iscore
                                if flag_detail:
                                    detail_s1.append(
                                        "{tn} {ts}".format(
                                            tn=supporttech[zz][0], ts=iscore
                                        )
                                    )

                            if scount < smax:
                                shi = scount * 2
                                if shi > smax:
                                    shi = smax

                                for zz in range(scount, shi):
                                    iscore = float(supporttech[zz][1]) * 0.75
                                    fscore += iscore
                                    if flag_detail:
                                        detail_s1.append(
                                            "{tn} {ts}".format(
                                                tn=supporttech[zz][0], ts=iscore
                                            )
                                        )

                                if (scount * 2) < smax:
                                    for zz in range(scount * 2, smax):
                                        iscore = float(supporttech[zz][1]) * 0.25
                                        fscore += iscore
                                        if flag_detail:
                                            detail_s2.append(
                                                "{tn} {ts}".format(
                                                    tn=supporttech[zz][0], ts=iscore
                                                )
                                            )

                            faccum.append(fscore)

                    # weapons
                    wl1 = teh.tech_key_range_list("weapon")
                    techlist = [t for t in wl1 if t not in ["dart"]]
                    weapontech = list()
                    for tkey in techlist:
                        score = 0
                        if tkey in ww:
                            tweights = ww[tkey]
                            tval = self.player_tech_get(pkey, tkey)
                            if tval > 0:
                                score = tweights[tval - 1]

                        if score > 0:
                            weapontech.append([tkey, score])

                    if len(weapontech) > 0:
                        weapontech.sort(key=lambda x: x[1], reverse=True)
                        got_first = False
                        wt2 = list()

                        for weapon_tuple in weapontech:
                            skey = weapon_tuple[0]

                            if skey in ["battery", "laser"]:
                                if not got_first:
                                    wt2.append(weapon_tuple)
                                    got_first = True

                            else:
                                wt2.append(weapon_tuple)

                        whi = 3
                        if whi > len(wt2):
                            whi = len(wt2)

                        if 0 < whi:
                            iscore = float(wt2[0][1])
                            fscore = iscore
                            if flag_detail:
                                detail_we.append(
                                    "{tn} {ts}".format(tn=wt2[0][0], ts=iscore)
                                )

                            if 1 < whi:
                                iscore = float(wt2[1][1]) * 0.75
                                fscore += iscore
                                if flag_detail:
                                    detail_we.append(
                                        "{tn} {ts}".format(tn=wt2[1][0], ts=iscore)
                                    )

                                if 2 < whi:
                                    iscore = float(wt2[2][1]) * 0.5
                                    fscore += iscore
                                    if flag_detail:
                                        detail_we.append(
                                            "{tn} {ts}".format(tn=wt2[2][0], ts=iscore)
                                        )

                            faccum.append(fscore)

                    # shields
                    techlist = teh.tech_key_range_list("shield")
                    shieldtech = list()
                    for tkey in techlist:
                        score = 0
                        if tkey in ww:
                            tweights = ww[tkey]
                            tval = self.player_tech_get(pkey, tkey)
                            if tval > 0:
                                score = tweights[tval - 1]

                        if score > 0:
                            shieldtech.append([tkey, score])

                    if len(shieldtech) > 0:
                        shieldtech.sort(key=lambda x: x[1], reverse=True)
                        gotmain = False
                        gotareadelta = False
                        st2 = list()

                        for ss in shieldtech:
                            skey = ss[0]

                            if skey in ["passiveshield", "omegashield", "mirrorshield"]:
                                if not gotmain:
                                    st2.append(ss)
                                    gotmain = True

                            elif skey in ["areashield", "deltashield"]:
                                if not gotareadelta:
                                    st2.append(ss)
                                    gotareadelta = True
                                else:
                                    st2.append([skey, ss[1] * 0.5])

                            elif skey in ["blastshield"]:
                                st2.append(ss)

                        fscore = float(0.0)

                        for ss in st2:
                            iscore = float(ss[1])
                            fscore += iscore
                            if flag_detail:
                                detail_sh.append(
                                    "{tn} {ts}".format(tn=ss[0], ts=iscore)
                                )

                        faccum.append(fscore)

                    #
                    faccum.append(0.5)
                    accum = int(math.floor(math.fsum(faccum)))
                elif flag_wspoints210918:
                    faccum = list()
                    detail_aa = []
                    detail_mi = []
                    detail_s1 = []
                    detail_s2 = []
                    detail_we = []
                    detail_sh = []

                    # relics, entrust, dispatch, data, relicdrone
                    for tkey in ["relics", "entrust", "dispatch", "dart", "relicdrone"]:
                        if tkey in ww:
                            tweights = ww[tkey]
                            tval = self.player_tech_get(pkey, tkey)
                            if tval > 0:
                                score = tweights[tval - 1]
                                if tkey == "dart":
                                    # Special bonus for dart
                                    score = 50

                                faccum.append(float(score))
                                if flag_detail:
                                    detail_aa.append(
                                        "{tk} {sc}".format(tk=tkey, sc=score)
                                    )

                    # mining
                    otherminingtech = list()
                    ml1 = teh.tech_key_range_list("mining")
                    for mtkey in ml1:
                        score = 0
                        if mtkey in ww:
                            tweights = ww[mtkey]
                            tval = self.player_tech_get(pkey, mtkey)
                            if tval > 0:
                                score = tweights[tval - 1]

                        if score > 0:
                            otherminingtech.append([mtkey, score])

                    if len(otherminingtech) > 0:
                        otherminingtech.sort(key=lambda x: x[1], reverse=True)
                        minerlvl = self.player_tech_get(pkey, "miner")
                        mcount = 0
                        if minerlvl >= 2 and minerlvl <= 6:
                            mcount = minerlvl - 1

                        fscore = float(0.0)

                        mmax = len(otherminingtech)
                        mhi = mcount
                        if mhi > mmax:
                            mhi = mmax

                        for zz in range(0, mhi):
                            iscore = float(otherminingtech[zz][1])
                            fscore += iscore
                            if flag_detail:
                                detail_mi.append(
                                    "{tn} {ts}".format(
                                        tn=otherminingtech[zz][0], ts=iscore
                                    )
                                )

                        if mcount < mmax:
                            mhi = mcount * 2 - 2
                            if mhi > mmax:
                                mhi = mmax

                            for zz in range(mcount, mhi):
                                iscore = float(otherminingtech[zz][1]) * 0.5
                                fscore += iscore
                                if flag_detail:
                                    detail_mi.append(
                                        "{tn} {ts}".format(
                                            tn=otherminingtech[zz][0], ts=iscore
                                        )
                                    )

                        faccum.append(fscore)

                    # support
                    bslvl = self.player_tech_get(pkey, "bs")
                    if bslvl >= 2 and bslvl <= 6:
                        scount = bslvl - 1

                        techlist = teh.tech_key_range_list("support")

                        supporttech = list()
                        for tkey in techlist:
                            score = 0
                            if tkey in ww:
                                tweights = ww[tkey]
                                tval = self.player_tech_get(pkey, tkey)
                                if tval > 0:
                                    score = tweights[tval - 1]

                            if score > 0:
                                supporttech.append([tkey, score])

                        if len(supporttech) > 0:
                            supporttech.sort(key=lambda x: x[1], reverse=True)

                            fscore = float(0.0)

                            smax = len(supporttech)
                            shi = scount
                            if shi > smax:
                                shi = smax

                            for zz in range(0, shi):
                                iscore = float(supporttech[zz][1])
                                fscore += iscore
                                if flag_detail:
                                    detail_s1.append(
                                        "{tn} {ts}".format(
                                            tn=supporttech[zz][0], ts=iscore
                                        )
                                    )

                            if scount < smax:
                                shi = scount * 2
                                if shi > smax:
                                    shi = smax

                                for zz in range(scount, shi):
                                    iscore = float(supporttech[zz][1]) * 0.75
                                    fscore += iscore
                                    if flag_detail:
                                        detail_s1.append(
                                            "{tn} {ts}".format(
                                                tn=supporttech[zz][0], ts=iscore
                                            )
                                        )

                                if (scount * 2) < smax:
                                    for zz in range(scount * 2, smax):
                                        iscore = float(supporttech[zz][1]) * 0.25
                                        fscore += iscore
                                        if flag_detail:
                                            detail_s2.append(
                                                "{tn} {ts}".format(
                                                    tn=supporttech[zz][0], ts=iscore
                                                )
                                            )

                            faccum.append(fscore)

                    # weapons
                    wl1 = teh.tech_key_range_list("weapon")
                    weapontech = list()
                    for tkey in wl1:
                        score = 0
                        if tkey in ww:
                            tweights = ww[tkey]
                            tval = self.player_tech_get(pkey, tkey)
                            if tval > 0:
                                score = tweights[tval - 1]

                        if score > 0:
                            weapontech.append([tkey, score])

                    if len(weapontech) > 0:
                        weapontech.sort(key=lambda x: x[1], reverse=True)
                        got_first = False
                        wt2 = list()

                        for weapon_tuple in weapontech:
                            skey = weapon_tuple[0]

                            if skey in ["battery", "laser"]:
                                if not got_first:
                                    wt2.append(weapon_tuple)
                                    got_first = True

                            else:
                                wt2.append(weapon_tuple)

                        whi = 3
                        if whi > len(wt2):
                            whi = len(wt2)

                        if 0 < whi:
                            iscore = float(wt2[0][1])
                            fscore = iscore
                            if flag_detail:
                                detail_we.append(
                                    "{tn} {ts}".format(tn=wt2[0][0], ts=iscore)
                                )

                            if 1 < whi:
                                iscore = float(wt2[1][1]) * 0.75
                                fscore += iscore
                                if flag_detail:
                                    detail_we.append(
                                        "{tn} {ts}".format(tn=wt2[1][0], ts=iscore)
                                    )

                                if 2 < whi:
                                    iscore = float(wt2[2][1]) * 0.5
                                    fscore += iscore
                                    if flag_detail:
                                        detail_we.append(
                                            "{tn} {ts}".format(tn=wt2[2][0], ts=iscore)
                                        )

                            faccum.append(fscore)

                    # shields
                    techlist = teh.tech_key_range_list("shield")
                    shieldtech = list()
                    for tkey in techlist:
                        score = 0
                        if tkey in ww:
                            tweights = ww[tkey]
                            tval = self.player_tech_get(pkey, tkey)
                            if tval > 0:
                                score = tweights[tval - 1]

                        if score > 0:
                            shieldtech.append([tkey, score])

                    if len(shieldtech) > 0:
                        shieldtech.sort(key=lambda x: x[1], reverse=True)
                        gotmain = False
                        gotareadelta = False
                        st2 = list()

                        for ss in shieldtech:
                            skey = ss[0]

                            if skey in ["passiveshield", "omegashield", "mirrorshield"]:
                                if not gotmain:
                                    st2.append(ss)
                                    gotmain = True

                            elif skey in ["areashield", "deltashield"]:
                                if not gotareadelta:
                                    st2.append(ss)
                                    gotareadelta = True
                                else:
                                    st2.append([skey, ss[1] * 0.5])

                            elif skey in ["blastshield"]:
                                st2.append(ss)

                        fscore = float(0.0)

                        for ss in st2:
                            iscore = float(ss[1])
                            fscore += iscore
                            if flag_detail:
                                detail_sh.append(
                                    "{tn} {ts}".format(tn=ss[0], ts=iscore)
                                )

                        faccum.append(fscore)

                    #
                    faccum.append(0.5)
                    accum = int(math.floor(math.fsum(faccum)))
                else:
                    for tindex in range(len(ppt)):
                        tval = ppt[tindex]

                        if tval > 0:
                            tkey = teh.tech_keys[tindex]

                            if tkey in ww:
                                tweights = ww[tkey]
                                accum += tweights[tval - 1]
            except IndexError:
                accum = 0

            if flag_detail and accum > 0:
                olist = list()
                olist.append(
                    "`| {nm}` {ac}".format(nm=self.member_name_from_id(pkey), ac=accum)
                )
                olist.append("`|     :` " + ", ".join(detail_aa))
                olist.append("`|   mi:` " + ", ".join(detail_mi))
                olist.append("`|   su:` " + ", ".join(detail_s1))
                olist.append("`|   su:` " + ", ".join(detail_s2))
                olist.append("`|   we:` " + ", ".join(detail_we))
                olist.append("`|   sh:` " + ", ".join(detail_sh))
                return_list.append("\n".join(olist))
            else:
                user_list.append([self.member_name_from_id(pkey), accum])

        if not flag_detail:
            user_list.sort(key=lambda x: x[1], reverse=True)

            if len(t_header) == 2:
                t_header[1] = "Score"

            return_list += sme_table.draw(t_header, ["l", "r"], user_list)

        if flagged_whotruncated:
            return_list.append("Only showing 4 pilots")

        return return_list

    async def command_msgme(self, params):
        return_list = []

        self.queue_msg_for_send_out(self.current_author, "You rang?")

        return_list.append("OK")

        return return_list

    async def command_clear(self, params):
        return_list = []

        who_list_good = list()
        other_list = list()
        return_list = return_list + self.parse_who(
            params, who_list_good, other=other_list
        )

        count_clear = 1
        flag_all = False
        count_after = 2

        other_count = 0
        while other_count < len(other_list):
            oo = other_list[other_count]

            if oo == "+all":
                pass
                # flag_all = True
            elif oo == "+keep":
                count_after = 1
                if (other_count + 1) < len(other_list) and is_int(
                    other_list[other_count + 1]
                ):
                    count_after = int(other_list[other_count + 1])
                    other_count += 1

                    if count_after > 10:
                        return_list.append(f"Error: wont keep more than {count_after}")
                        count_clear = 0
                        flag_all = False
                        count_after = 0

                    if count_after < 0:
                        count_after = 0
            elif is_int(oo):
                count_clear = int(oo)

            other_count += 1

        # logger.debug(f'MEGAFONE {count_clear=}')
        # logger.debug(f'MEGAFONE {flag_all=}')
        # logger.debug(f'MEGAFONE {count_after=}')

        found_after = None
        if count_after > 0:
            old_msgs = await self.current_channel.history(
                limit=int(count_after + 1), oldest_first=True
            ).flatten()

            if count_after >= len(old_msgs):
                count_clear = 0
                flag_all = False
                count_after = 0
            else:
                found_after = old_msgs[count_after - 1]

        if flag_all:
            pass
            # logger.debug('MEGAFONE mark .5')
            # chunk_size = 96
            # keep_going = True
            # while keep_going:
            #     old_msgs = await self.current_channel.purge(limit=chunk_size, after=found_after)
            #     if len(old_msgs) < chunk_size:
            #         keep_going = False
        if count_clear > 0:
            await self.current_channel.purge(limit=count_clear + 1, after=found_after)

        if len(return_list) < 1:
            return_list.append("dented-control-message:no-reply")

        return return_list


class SmeArgumentWarning(Exception):
    def __init__(self, message):
        self.message = message
