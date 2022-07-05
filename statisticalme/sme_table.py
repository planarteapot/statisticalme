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

import statisticalme.statisticalme as smer


def draw(header, data_align, data, flag_csv=False):
    return_list = []
    msg_lines = list()

    if flag_csv:
        # csv style
        csv_line = str(header[0])
        for hh in header[1:]:
            csv_line += "," + str(hh)

        msg_lines.append(csv_line)

        for ditem in data:
            csv_line = str(ditem[0])
            for dd in ditem[1:]:
                csv_line += "," + str(dd)

            msg_lines.append(csv_line)
    else:
        # pretty text table
        data2 = list()
        for drow in data:
            data2.append([str(dcell) for dcell in drow])

        msg_lines = smer.sme_table_render(
            [str(hcell) for hcell in header],
            [str(acell) for acell in data_align],
            data2,
        )

    flag_truncated = False
    next_out = list()
    noout_len = 7
    for ll in msg_lines:
        strill = ll.rstrip()

        if (len(strill) + 1 + 7) > 2000:
            # line by itself too long
            if len(next_out) > 0:
                return_list.append("```\n" + "\n".join(next_out) + "\n```")

            next_out = list()
            noout_len = 7

            return_list.append("```\n" + strill[0:1992] + "\n```")
            flag_truncated = True
        elif (len(strill) + 1 + noout_len) > 2000:
            # adding line would make current set too long
            if len(next_out) > 0:
                return_list.append("```\n" + "\n".join(next_out) + "\n```")

            next_out = [strill]
            noout_len = 7 + len(strill) + 1
        else:
            # add line
            next_out.append(strill)
            noout_len += len(strill) + 1

    if len(next_out) > 0:
        return_list.append("```\n" + "\n".join(next_out) + "\n```")

    if flag_truncated:
        return_list.append("Some lines truncated")

    return return_list
