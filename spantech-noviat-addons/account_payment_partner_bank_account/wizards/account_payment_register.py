# Copyright 2009-2023 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _compute_partner_bank_id(self):
        for rec in self:
            batches = rec._get_batches()
            ams = [x["lines"].mapped("move_id") for x in batches]
            partner_banks = []
            for entry in ams:
                for am in entry:
                    if am.partner_bank_id:
                        partner_banks.append(am.partner_bank_id)
                    else:
                        partner_banks = []
            if len(partner_banks) == 1:
                rec.partner_bank_id = partner_banks[0]
            else:
                return super(AccountPaymentRegister, rec)._compute_partner_bank_id()
