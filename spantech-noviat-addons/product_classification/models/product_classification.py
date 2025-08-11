# Copyright 2009-2022 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductClassification(models.Model):
    _name = "product.classification"
    _description = "Product Classification"
    _parent_store = True
    _parent_name = "parent_id"
    _rec_name = "complete_name"
    _order = "complete_name"
    _check_company_auto = True

    _sql_constraints = [
        (
            "code_parent_uniq",
            "unique(code, parent_id)",
            "Duplicate Product Classification code !",
        )
    ]

    name = fields.Char(string="Classification", required=True)
    code = fields.Char()
    level = fields.Integer(compute="_compute_level", store=True)
    note = fields.Text(string="Description")
    complete_name = fields.Char(
        compute="_compute_complete_name",
        recursive=True,
        store=True,
        unaccent=False,
    )
    parent_path = fields.Char(index=True)
    parent_id = fields.Many2one(
        comodel_name="product.classification",
        string="Parent Classification",
        index=True,
        ondelete="cascade",
    )
    child_ids = fields.One2many(
        comodel_name="product.classification",
        inverse_name="parent_id",
        string="Child Classifications",
    )
    product_tmpl_ids = fields.Many2many(
        comodel_name="product.template",
        relation="product_classification_product_template_rel",
        column1="classification_id",
        column2="product_tmpl_id",
        string="Products",
    )
    product_count = fields.Integer(compute="_compute_product_count")
    recursive_product_count = fields.Integer(compute="_compute_recursive_product_count")
    active = fields.Boolean(
        default=True,
        help="The active field allows you to hide "
        "the classification without removing it.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        index=True,
        help="Let this field empty if this location is shared between companies",
    )

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for rec in self:
            if rec.parent_id:
                res = "%s / %s" % (rec.parent_id.complete_name, rec.name)
            else:
                res = rec.name
            rec.complete_name = res

    @api.depends("parent_path")
    def _compute_level(self):
        for rec in self:
            rec.level = len(rec.parent_path.split("/")) - 1

    def _get_complete_name(self, cl):
        if cl.parent_id:
            parent_path = self._get_complete_name(cl.parent_id) + "/"
        else:
            parent_path = ""
        return parent_path + cl.name

    def get_product_tmpls_recursively(self):
        """
        Returns all product.template records belonging to this
        classification or its children.
        """
        self.ensure_one()
        res = self.product_tmpl_ids
        for classif in self.child_ids:
            res |= classif.get_product_tmpls_recursively()
        return res

    def _compute_product_count(self):
        for rec in self:
            rec.product_count = len(rec.product_tmpl_ids)

    def _compute_recursive_product_count(self):
        for rec in self:
            rec.recursive_product_count = len(self.get_product_tmpls_recursively())

    def action_open_all_products(self):
        product_ids = self.get_product_tmpls_recursively()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "product.product_template_action_all"
        )
        action["domain"] = [("id", "in", product_ids.ids)]
        return action
