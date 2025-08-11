# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    consolidation_account_id = fields.Many2one(
        comodel_name="consolidation.account",
        string="Consolidation Account",
        domain="[('chart_id', '=', consolidation_chart_id)]",
        compute="_compute_consolidation_account_id",
        store=True,
    )
    consolidation_chart_id = fields.Many2one(
        comodel_name="consolidation.chart",
        string="Consolidation Chart",
        related="company_id.consolidation_chart_id",
    )
    account_id_domain = fields.Binary(
        string="Account Domain", compute="_compute_account_id_domain"
    )
    account_id = fields.Many2one(domain="[('id', 'in', allowed_account_ids)]")

    @api.depends("account_id")
    def _compute_consolidation_account_id(self):
        for rec in self:
            rec.consolidation_account_id = rec.account_id.consolidation_account_id

    @api.depends("consolidation_account_id")
    def _compute_account_id_domain(self):
        if not self.env.user.has_group(
            "account_consolidation_mapping_base.group_consolidation_account_mapping"
        ):
            self.write({"account_id_domain": []})
            return
        for rec in self:
            if rec.consolidation_account_id:
                allowed_accounts = rec.consolidation_account_id.account_ids.filtered(
                    lambda r, rec=rec: r.company_id == rec.company_id
                    and not r.deprecated
                )
            else:
                allowed_accounts = self.env["account.account"].search(
                    [("company_id", "=", rec.company_id.id), ("deprecated", "=", False)]
                )
            # exclude AR/AP and off-balance accounts from invoice tab
            if "line_ids" not in rec.env.context:
                allowed_accounts = allowed_accounts.filtered(
                    lambda r: r.account_type
                    not in ("liability_payable", "asset_receivable")
                    and not r.is_off_balance
                )
            rec.account_id_domain = [("id", "in", allowed_accounts.ids)]
