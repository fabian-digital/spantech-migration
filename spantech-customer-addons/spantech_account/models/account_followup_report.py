# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountFollowupReport(models.AbstractModel):
    _inherit = "account.followup.report"

    @api.model
    def send_email(self, options):
        partner = self.env["res.partner"].browse(options.get("partner_id"))
        if partner.partner_followup_cc_ids:
            self = self.with_context(
                add_additionnal_partner_message=partner.partner_followup_cc_ids.ids
            )
            return super().send_email(options)
        return super().send_email(options)
