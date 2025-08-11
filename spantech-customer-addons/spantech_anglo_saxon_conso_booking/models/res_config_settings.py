# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    conso_booking_journal_id = fields.Many2one(
        comodel_name="account.journal",
        related="company_id.conso_booking_journal_id",
        readonly=False,
        string="ITR Consolidation Entry Journal",
        domain="[('company_id', '=', company_id), ('type', '=', 'general')]",
        help="Financial Journal where the ITR Consolidation entry will be booked",
    )
    itr_account_id = fields.Many2one(
        comodel_name="account.account",
        string="ITR Account",
        domain="""[
            ('deprecated', '=', False),
            ('account_type', 'not in', (
                'asset_receivable',
                'liability_payable',
                'asset_cash',
                'liability_credit_card'
            )),
            ('company_id', '=', company_id)]""",
        related="company_id.itr_account_id",
        readonly=False,
        help="Invoice To Receive Account",
    )
    itr_ico_account_id = fields.Many2one(
        comodel_name="account.account",
        string="ITR ICO Account",
        domain="""[
            ('deprecated', '=', False),
            ('account_type', 'not in', (
                'asset_receivable',
                'liability_payable',
                'asset_cash',
                'liability_credit_card'
            )), ('company_id', '=', company_id)]""",
        related="company_id.itr_ico_account_id",
        readonly=False,
        help="Invoice To Receive ICO Account",
    )
    fg_var_account_id = fields.Many2one(
        comodel_name="account.account",
        string="FG Account",
        domain="""[
            ('deprecated', '=', False),
            ('account_type', 'not in', (
                'asset_receivable',
                'liability_payable',
                'asset_cash',
                'liability_credit_card'
            )), ('company_id', '=', company_id)]""",
        related="company_id.fg_var_account_id",
        readonly=False,
        help="Finished Goods Stock Variation Account",
    )
    fg_var_ico_account_id = fields.Many2one(
        comodel_name="account.account",
        string="FG ICO Account",
        domain="""[
            ('deprecated', '=', False),
            ('account_type', 'not in', (
                'asset_receivable',
                'liability_payable',
                'asset_cash',
                'liability_credit_card'
            )), ('company_id', '=', company_id)]""",
        related="company_id.fg_var_ico_account_id",
        readonly=False,
        help="Finished Goods ICO Stock Variation Account",
    )
