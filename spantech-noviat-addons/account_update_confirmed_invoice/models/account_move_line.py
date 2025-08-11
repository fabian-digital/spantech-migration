# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def update_invoice_line(self):
        self.ensure_one()
        module = __name__.split("addons.")[1].split(".")[0]
        view = self.env.ref("%s.account_invoice_line_update_view_form" % module)
        self = self.with_context(
            default_inv_line_id=self.id,
            default_name=self.name,
            default_product_id=self.product_id.id,
            default_account_id=self.account_id.id,
            default_analytic_distribution=self.analytic_distribution,
            default_tax_ids=self.tax_ids.ids,
            default_type_tax_use=(
                self.move_id.move_type[:3] == "in_" and "purchase" or "sale"
            ),
        )
        return {
            "name": _("Update Invoice Line"),
            "view_mode": "form",
            "res_model": "account.invoice.line.update",
            "view_id": view.id,
            "target": "new",
            "type": "ir.actions.act_window",
            "context": self.env.context,
        }
