# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

columns_renames = {
    "helpdesk_ticket": [
        ("solution_of_incident", "solution_to_incident"),
        ("provisional_cost", "estimated_cost"),
    ],
}


def migrate(cr, version):
    openupgrade.rename_columns(cr, columns_renames)
