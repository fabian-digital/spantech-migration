# Copyright 2009-2023 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api


def pre_init_hook(cr):
    if openupgrade.is_module_installed(cr, "account_move_misc_entry_fix"):
        env = api.Environment(cr, SUPERUSER_ID, {})
        modules = [
            ("account_move_misc_entry_fix", "account_move_misc_entry_no_automatic_tax")
        ]
        openupgrade.update_module_names(env.cr, modules, merge_modules=True)
