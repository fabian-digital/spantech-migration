# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression


class ProductSequence(models.Model):
    _name = "product.sequence"
    _order = "code"
    _description = "Sequence for products"

    _sql_constraints = [
        ("code_unique", "unique(code)", "`code` must be unique."),
    ]
    code = fields.Char()
    name = fields.Char()
    sequence_id = fields.Many2one(
        comodel_name="ir.sequence", domain=[("product_sequence_ids", "!=", False)]
    )
    number_next_actual = fields.Integer(related="sequence_id.number_next_actual")

    def name_get(self):
        return [(i.id, "[" + i.code + "] " + i.name) for i in self]

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("code", operator, name), ("name", operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ["&", "!"] + domain[1:]
        assets = self.search(domain + args, limit=limit)
        return assets.name_get()

    def copy(self, default=None):
        if self.code:
            code = "%s (Copy)" % (self.code or "")
        else:
            code = self.code

        default = dict(default or {}, code=code)
        return super().copy(default=default)

    @api.model
    def create(self, values):
        values["code"] = values.get("code").strip().rstrip("-") + "-"
        rec = super().create(values)
        seq_id = rec._get_sequence_id()
        rec.write({"sequence_id": seq_id.id})
        return rec

    def write(self, vals):
        if vals.get("code", False):
            vals["code"] = vals.get("code").strip().rstrip("-") + "-"
        seq_vals = {k: v for k, v in vals.items() if k in ["code", "name"]}
        if seq_vals:
            self.sequence_id.write(seq_vals)
        return super().write(vals)

    def next_by_id(self, sequence_date=None):
        for rec in self:
            if rec.sequence_id.number_next_actual > 999:
                raise UserError(
                    _(
                        "This Product sequence has reached its limit, "
                        "please use another."
                    )
                )
            return rec.sequence_id.next_by_id(sequence_date)

    def _get_sequence_id(self):
        seq_id = (
            self.env["ir.sequence"]
            .with_context(active_test=False)
            .sudo()
            .search([("code", "=", self.code)])
        )
        if not seq_id:
            seq_id = (
                self.env["ir.sequence"]
                .sudo()
                .create(
                    {
                        "code": self.code,
                        "name": self.name,
                        "implementation": "standard",
                        "prefix": self.code,
                        "padding": 3,
                        "number_increment": 1,
                        "company_id": False,
                    }
                )
            )
        return seq_id

    # To be executed in shell
    # Drop duplicate product sequences
    def action_check_product_sequence_name(self):
        existings = {}
        for rec in self:
            name = rec.name.strip().rstrip("-") + "-"
            cpt = existings.get(name, 0)
            existings[name] = cpt + 1

        duplicates = [x for x, v in existings.items() if v > 1]
        if duplicates:
            for elt in duplicates:
                ps = self.search([("name", "=", elt)])
                ps[0].sudo().unlink()

    # To be executed in shell`
    # Drop duplicate ir.sequence linked to product.sequence
    # unify code and prefix of ir.sequence and product.sequence
    # reassign correct ir.sequence to product.sequence
    def action_check_sequence(self):
        for rec in self:
            rec.code = rec.code.strip().rstrip("-") + "-"
            seq_id = (
                self.env["ir.sequence"]
                .sudo()
                .search(
                    ["|", ("code", "=", rec.code), ("code", "=", rec.code.rstrip("-"))]
                )
            )
            if seq_id and len(seq_id) > 1:
                seq_id.code = rec.code
                seq_id.prefix = rec.code
                seq_id = seq_id.sorted(lambda x: x.number_next_actual)
                rec.sequence_id = seq_id[1]
                seq_id[0].sudo().unlink()
                continue
            if seq_id:
                seq_id.code = rec.code
                seq_id.prefix = rec.code
                rec.sequence_id = seq_id
            else:
                rec.sequence_id = rec._get_sequence_id()


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    product_sequence_ids = fields.One2many(
        comodel_name="product.sequence",
        inverse_name="sequence_id",
        string="Product Sequences",
    )
