# Copyright 2009-2024 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _compute_partner_bank_id(self):
        for rec in self:
            if rec.payment_type == "outbound" and not rec.partner_bank_id:
                return super()._compute_partner_bank_id
