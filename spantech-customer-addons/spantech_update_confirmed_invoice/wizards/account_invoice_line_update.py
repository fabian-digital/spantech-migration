# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models

from odoo.addons.account.models.account_move_line import AccountMoveLine as AML_OC

_logger = logging.getLogger(__name__)


class AccountInvoiceLineUpdate(models.TransientModel):
    _name = "account.invoice.line.update"
    _inherit = ["analytic.mixin"]
    _description = "Update Confirmed Invoice Line Wizard"

    name = fields.Text(
        string="Description", store=True, readonly=False, compute="_compute_fields"
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        compute="_compute_fields",
        store=True,
        readonly=False,
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        domain=[("deprecated", "=", False)],
        required=True,
        string="Account",
        compute="_compute_fields",
        store=True,
        readonly=False,
    )
    note = fields.Text(string="Notes", readonly=True, default="")
    inv_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Invoice Line",
    )

    @api.depends("inv_line_id")
    def _compute_fields(self):
        for rec in self:
            rec.name = rec.inv_line_id.name
            rec.product_id = rec.inv_line_id.product_id
            rec.account_id = rec.inv_line_id.account_id
            rec.analytic_distribution = rec.inv_line_id.analytic_distribution

    def update_invoice_line(self):
        self.ensure_one()
        inv_line = self.inv_line_id
        invoice = inv_line.move_id
        invoice._check_fiscalyear_lock_date()
        m2o_fields, basic_fields = self._get_fields()
        flds = m2o_fields + basic_fields

        updates = []
        for i, f in enumerate(flds):
            if getattr(self, f) != getattr(inv_line, f):
                updates.append(flds[i])
        if not updates:
            self.note = _("No lines have been updated.")
            return self._results_view()

        old_vals = ", ".join([f"\n{f}: {getattr(inv_line, f)}" for f in updates])
        vals = {}
        for field in updates:
            if field in m2o_fields:
                vals[field] = getattr(self, field).id
            elif field in basic_fields:
                vals[field] = getattr(self, field)
            else:
                raise NotImplementedError
        super(AML_OC, inv_line).write(vals)

        log_msg = ("update_invoice_line performed by '%s' ") % self.env.user.login
        log_msg += f"on {inv_line}."
        msg = _("Old Values: %s") % old_vals
        log_msg += "\n" + msg
        note = _("Updated invoice line: %s") % f"{inv_line.name} ({inv_line.id})"
        note += "\n\n" + msg
        new_vals = ", ".join([f"\n{f}: {getattr(self, f)}" for f in updates])
        msg = "\n\n" + _("New Values: %s") % new_vals
        log_msg += msg
        note += msg
        self.note = note
        return self._results_view()

    def action_close(self):
        return {"type": "ir.actions.client", "tag": "reload"}

    def _get_fields(self):
        m2o_fields = [
            "account_id",
            "product_id",
        ]
        basic_fields = ["name", "analytic_distribution"]
        return m2o_fields, basic_fields

    def _results_view(self):
        module = __name__.split("addons.")[1].split(".")[0]
        result_view = self.env.ref(f"{module}.{self._table}_view_form_result")
        return {
            "name": _("Update invoice line results"),
            "res_id": self.id,
            "view_mode": "form",
            "res_model": self._name,
            "view_id": result_view.id,
            "context": self._context,
            "target": "new",
            "type": "ir.actions.act_window",
        }
