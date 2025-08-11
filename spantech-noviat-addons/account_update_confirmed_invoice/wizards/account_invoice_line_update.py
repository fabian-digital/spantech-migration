# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.account.models.account_move_line import AccountMoveLine as AML_OC


class AccountInvoiceLineUpdate(models.TransientModel):

    _name = "account.invoice.line.update"
    _inherit = ["analytic.mixin"]
    _description = "Update Confirmed Invoice Line Wizard"

    name = fields.Char(
        string="Label", store=True, readonly=False, compute="_compute_fields"
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        store=True,
        readonly=False,
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        domain=[("deprecated", "=", False)],
        required=True,
        string="Account",
        store=True,
        readonly=False,
    )
    tax_ids = fields.Many2many(
        comodel_name="account.tax",
        string="Taxes",
        store=True,
        readonly=False,
    )
    note = fields.Text(string="Notes", readonly=True, default="")
    inv_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Invoice Line",
    )
    company_id = fields.Many2one(
        string="Company",
        related="inv_line_id.company_id",
    )
    type_tax_use = fields.Char()

    def update_invoice_line(self):
        self.ensure_one()
        inv_line = self.inv_line_id
        inv = inv_line.move_id
        inv._check_fiscalyear_lock_date()
        amount_total = inv.amount_total
        m2o_fields, m2m_fields, basic_fields = self._get_fields()
        flds = m2o_fields + m2m_fields + basic_fields

        updates = []
        for i, f in enumerate(flds):
            if getattr(self, f) != getattr(inv_line, f):
                updates.append(flds[i])
        if not updates:
            self.note = _("No lines have been updated.")
            return self._results_view()
        old_vals = "\n".join(
            self._get_vals_to_display(inv_line, updates, m2o_fields, m2m_fields)
        )
        vals = {}
        for field in updates:
            if field in m2o_fields:
                vals[field] = getattr(self, field).id
            elif field in m2m_fields:
                vals[field] = [(6, 0, getattr(self, field).ids)]
            elif field in basic_fields:
                vals[field] = getattr(self, field)
            else:
                raise NotImplementedError
        old_tax_lines = inv.line_ids.filtered(
            lambda r: r.tax_line_id in inv_line.tax_ids
        )
        super(AML_OC, inv_line).write(vals)
        if "analytic_distribution" in vals:
            inv_line._inverse_analytic_distribution()
        if "tax_ids" in updates:
            self._recalc_taxes(old_tax_lines)
        if inv.amount_total != amount_total:
            raise UserError(
                _(
                    "Updates impacting the invoice amount are not allowed.\n"
                    "You should correct this invoice via refund and new invoice."
                )
            )

        log_msg = ("update_invoice_line performed by '%s' ") % self.env.user.login
        log_msg += "on {}.".format(inv_line)
        msg = _("Old Values:\n%s") % old_vals
        log_msg += "\n" + msg
        note = _("Updated invoice line: %(name)s (ID: %(id)s)") % {
            "name": self._get_truncated_name(inv_line.name),
            "id": inv_line.id,
        }
        note += "\n\n" + msg
        new_vals = "\n".join(
            self._get_vals_to_display(inv_line, updates, m2o_fields, m2m_fields)
        )
        msg = "\n\n" + _("New Values:\n%s") % new_vals
        log_msg += msg
        note += msg
        self.note = note
        return self._results_view()

    def action_close(self):
        return {"type": "ir.actions.act_window_close"}

    def _get_fields(self):
        m2o_fields = [
            "account_id",
            # Todo: Fix the update of product_id.
            # Change the product_id by sql otherwise invoice amount is broken
            # "product_id","product_id",
        ]
        m2m_fields = ["tax_ids"]
        basic_fields = ["name", "analytic_distribution"]
        return m2o_fields, m2m_fields, basic_fields

    def _recalc_taxes(self, old_tax_lines):  # noqa: C901
        inv_line = self.inv_line_id
        inv = inv_line.move_id
        sign = inv.move_type in ("in_refund", "out_invoice") and -1 or 1
        is_zero = inv.currency_id.is_zero
        line_dict = self.env["account.tax"]._convert_to_tax_base_line_dict(
            inv_line,
            partner=inv.partner_id,
            currency=inv.currency_id,
            product=inv_line.product_id,
            taxes=inv_line.tax_ids,
            price_unit=inv_line.price_unit,
            quantity=inv_line.quantity,
            discount=inv_line.discount,
            account=inv_line.account_id,
            analytic_distribution=inv_line.analytic_distribution,
            price_subtotal=inv_line.price_subtotal,
            is_refund=inv.move_type in ("out_refund", "in_refund"),
            rate=inv_line.currency_rate,
            handle_price_include=True,
        )
        to_update_vals, tax_vals_list = self.env[
            "account.tax"
        ]._compute_taxes_for_single_line(line_dict)
        if len(old_tax_lines) != len(tax_vals_list):
            raise UserError(
                _(
                    "Change of tax object resulting in more or less "
                    "tax lines is not supported.\n"
                    "You should correct this invoice via refund and new invoice."
                )
            )
        if not is_zero(
            sign * sum(old_tax_lines.mapped("amount_currency"))
            - sum([x["tax_amount_currency"] for x in tax_vals_list])
        ):
            raise UserError(
                _(
                    "Change of tax object resulting in change of tax amount "
                    "is not supported.\n"
                    "You should correct this invoice via refund and new invoice."
                )
            )

        new_tag_ids = to_update_vals.get("tax_tag_ids")
        if new_tag_ids:
            super(AML_OC, inv_line).write({"tax_tag_ids": new_tag_ids})

        for entry in tax_vals_list:
            lines = old_tax_lines.filtered(
                lambda r: is_zero(
                    sign * r.amount_currency - entry["tax_amount_currency"]
                )
            )
            if not lines:
                raise NotImplementedError
            if len(lines) == 1:
                line = lines
            elif len(lines) > 1:
                # e.g. non-deductible taxes on base account
                if not entry["account_id"]:
                    line = lines.filtered(lambda r: r.account_id == inv_line.account_id)
                else:
                    line = lines.filtered(lambda r: r.account_id != inv_line.account_id)
            if len(line) != 1:
                raise NotImplementedError
            vals = {}
            for key, key_type, fld, fld_type in self._tax_sync_fields():
                # complex logic since no consistency in Odoo account module
                # between tax_vals_list and line fields
                # TODO: add unit test since this code will fail once Odoo cleans up
                # the account module tax engine

                entry_value = entry[key]
                if key_type == "m2o":
                    entry_value = entry_value and entry_value.id
                elif key_type == "m2m":
                    entry_value = entry_value and entry_value.ids or []
                # use inv_line account when no account defined on tax repartition line
                if not entry_value and fld == "account_id":
                    entry_value = inv_line.account_id.id
                if isinstance(entry_value, list):
                    entry_value = set(entry_value)

                line_value = line[fld]
                if fld_type == "m2o":
                    line_value = line_value.id
                elif fld_type == "m2m":
                    line_value = line_value.ids
                if isinstance(line_value, list):
                    line_value = set(line_value)

                if fld_type == "monetary":
                    diff = not is_zero(sign * line_value - entry_value)
                else:
                    diff = line_value != entry_value
                if diff:
                    if fld_type == "basic":
                        vals[fld] = entry[key]
                    elif fld_type == "m2o":
                        vals[fld] = key_type == "basic" and entry[key] or entry[key].id
                    elif fld_type == "m2m":
                        vals[fld] = [(6, 0, entry[key])]
                    else:
                        raise NotImplementedError
            if vals:
                super(AML_OC, line).write(vals)
        return

    def _tax_sync_fields(self):
        """
        returns list of tuples:
          tuple[0]: key in tax_vals_list entry
          tuple[1]: key field type 'm2o', m2m', 'regular'
          tuple[2]: aml field name
          tuple[3]: aml field type 'm2o', m2m', 'regular'
        TODO: add analytics
        """
        return [
            ("account_id", "basic", "account_id", "m2o"),
            ("name", "basic", "name", "basic"),
            ("tax_amount_currency", "monetary", "amount_currency", "monetary"),
            ("tag_ids", "basic", "tax_tag_ids", "m2m"),
            ("tax_repartition_line", "m2o", "tax_repartition_line_id", "m2o"),
        ]

    def _results_view(self):
        module = __name__.split("addons.")[1].split(".")[0]
        result_view = self.env.ref("{}.{}_view_form_result".format(module, self._table))
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

    def _get_vals_to_display(self, inv_line, updates, m2o_fields, m2m_fields):
        vals = []
        for f in updates:
            if f in m2o_fields:
                vals.append(
                    "%(field_name)s: %(name)s (ID: %(id)s)"
                    % {
                        "name": self._get_field_value_to_display(getattr(inv_line, f)),
                        "id": getattr(inv_line, f).id,
                        "field_name": f,
                    }
                )
            elif f in m2m_fields:
                names = []
                for record in getattr(inv_line, f):
                    names.append(
                        "%(field_name)s: %(name)s (ID: %(id)s)\n"
                        % {
                            "name": self._get_field_value_to_display(record),
                            "id": record.id,
                            "field_name": f,
                        }
                    )
                vals.append(
                    "%(field_name)s: %(name)s"
                    % {"field_name": f, "name": " - ".join(names)}
                )
            else:
                vals.append(
                    "%(field_name)s: %(name)s"
                    % {
                        "field_name": f,
                        "name": self._get_truncated_name(str(getattr(inv_line, f))),
                    }
                )
        return vals

    def _get_field_value_to_display(self, record):
        name = record
        if hasattr(record, "display_name"):
            name = record.display_name
        elif hasattr(record, "name"):
            name = record.name
        return self._get_truncated_name(name)

    def _get_truncated_name(self, name):
        if not name:
            return ""
        return (name[:110] + "..") if len(name) > 110 else name
