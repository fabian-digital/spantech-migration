# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.osv import expression


class Partner(models.Model):
    _inherit = "res.partner"

    property_out_journal_id = fields.Many2one(
        comodel_name="account.journal",
        company_dependent=True,
        string="Sales Journal",
        domain=[("type", "=", "sale")],
    )
    property_in_journal_id = fields.Many2one(
        comodel_name="account.journal",
        company_dependent=True,
        string="Purchases Journal",
        domain=[("type", "=", "purchase")],
    )

    approver_id = fields.Many2one(
        comodel_name="res.users", string="Approver for vendor payments"
    )
    partner_followup_cc_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="partner_followup_cc_ids_rel",
        column1="customer_partner_id",
        column2="partner_cc_id",
        string="Partner to add in CC for followups",
    )

    duplicated_bank_account_partners_count = fields.Integer(
        compute="_compute_duplicated_bank_account_partners_count",
    )

    @api.depends("bank_ids")
    def _compute_duplicated_bank_account_partners_count(self):
        for partner in self:
            partner.duplicated_bank_account_partners_count = len(
                partner._get_duplicated_bank_accounts()
            )

    def action_view_partner_with_same_bank(self):
        self.ensure_one()
        bank_partners = self._get_duplicated_bank_accounts()
        # Open a list view or form view of the partner(s) with the same bank accounts
        if self.duplicated_bank_account_partners_count == 1:
            action_vals = {
                "type": "ir.actions.act_window",
                "res_model": "res.partner",
                "view_mode": "form",
                "res_id": bank_partners.partner_id.id,
                "views": [(False, "form")],
            }
        else:
            action_vals = {
                "name": _("Partners"),
                "type": "ir.actions.act_window",
                "res_model": "res.partner",
                "view_mode": "tree,form",
                "views": [(False, "list"), (False, "form")],
                "domain": [("id", "in", bank_partners.partner_id.ids)],
            }

        return action_vals

    def _get_duplicated_bank_accounts(self):
        self.ensure_one()
        if not self.bank_ids:
            return self.env["res.partner.bank"]
        domains = []
        for bank in self.bank_ids:
            domains.append(
                [
                    ("acc_number", "=", bank.acc_number),
                    ("bank_id", "=", bank.bank_id.id),
                ]
            )
        domain = expression.OR(domains)
        if self.company_id:
            domain = expression.AND(
                [domain, [("company_id", "in", (False, self.company_id.id))]]
            )
        domain = expression.AND([domain, [("partner_id", "!=", self._origin.id)]])
        return self.env["res.partner.bank"].search(domain)

    @api.model
    def _commercial_fields(self):
        return super()._commercial_fields() + [
            "property_out_journal_id",
            "property_in_journal_id",
        ]


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    company_id = fields.Many2one(default=False)
