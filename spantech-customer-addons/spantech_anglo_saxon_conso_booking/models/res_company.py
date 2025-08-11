# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    conso_booking_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="ITR Consolidation Entry Journal",
        check_company=True,
    )
    itr_account_id = fields.Many2one(
        comodel_name="account.account",
        string="ITR Account",
        check_company=True,
    )
    itr_ico_account_id = fields.Many2one(
        comodel_name="account.account",
        string="ITR ICO Account",
        check_company=True,
    )
    fg_var_account_id = fields.Many2one(
        comodel_name="account.account",
        string="FG Account",
        check_company=True,
    )
    fg_var_ico_account_id = fields.Many2one(
        comodel_name="account.account",
        string="FG ICO Account",
        check_company=True,
    )
