# Copyright 2009-2022 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMoveLineImport(models.TransientModel):
    _inherit = "aml.import"

    def _handle_partner(self, wiz_dict, field, line, move, aml_vals):
        if not aml_vals.get("partner_id"):
            dom = ["|", ("parent_id", "=", False), ("is_company", "=", True)]
            dom_ref = dom + [
                "|",
                ("property_old_erp_customer_ref", "=", line[field]),
                ("property_old_erp_supplier_ref", "=", line[field]),
            ]
            partners = self.env["res.partner"].search(dom_ref)
            if len(partners) == 1:
                partner = partners.commercial_partner_id
                aml_vals["partner_id"] = partner.id
        if not aml_vals.get("partner_id"):
            super()._handle_partner(wiz_dict, field, line, move, aml_vals)
        return
