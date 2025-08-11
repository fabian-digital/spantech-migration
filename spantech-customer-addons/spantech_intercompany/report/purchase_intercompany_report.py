# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models
from odoo.osv.expression import AND


class PurchaseIntercompanyReport(models.Model):
    _name = "purchase.intercompany.report"
    _description = "Purchase Intercompany Report"
    _auto = False
    _order = "write_date desc, date_order desc, order_id desc"

    name = fields.Char()
    po_name = fields.Char(string="Purchase Order")
    date_order = fields.Datetime(string="Order Date", readonly=True)
    state = fields.Selection(
        selection=[
            ("draft", "Draft RFQ"),
            ("sent", "RFQ Sent"),
            ("to approve", "To Approve"),
            ("purchase", "Purchase Order"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        readonly=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.product", string="Product", readonly=True
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Vendor", readonly=True
    )
    date_approve = fields.Datetime(string="Confirmation Date", readonly=True)
    product_uom = fields.Many2one(
        comodel_name="uom.uom", string="Reference Unit of Measure", required=True
    )
    company_id = fields.Many2one(
        comodel_name="res.company", string="Company", readonly=True
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency", string="Currency", readonly=True
    )
    user_id = fields.Many2one(
        comodel_name="res.users", string="Purchase Representative", readonly=True
    )
    price_unit = fields.Float(readonly=True)
    price_subtotal = fields.Monetary(string="Subtotal", readonly=True)
    price_total = fields.Monetary(string="Total", readonly=True)
    price_tax = fields.Float(string="Tax", readonly=True)
    product_uom_qty = fields.Float(string="Quantity", store=True)
    qty_received = fields.Float(string="Received Qty", digits="Product Unit of Measure")
    qty_to_invoice = fields.Float(
        string="To Invoice Quantity", digits="Product Unit of Measure"
    )
    qty_invoiced = fields.Float(string="Billed Qty", digits="Product Unit of Measure")
    category_id = fields.Many2one(
        comodel_name="product.category", string="Product Category", readonly=True
    )
    product_tmpl_id = fields.Many2one(
        comodel_name="product.template", string="Product Template", readonly=True
    )
    analytic_distribution = fields.Json(
        string="Analytic Account",
        readonly=True,
    )
    commercial_partner_id = fields.Many2one(
        comodel_name="res.partner", string="Commercial Entity", readonly=True
    )
    is_interco_partner = fields.Boolean(string="Is a Spantech Entity", readonly=True)
    order_id = fields.Many2one(
        comodel_name="purchase.order", string="Order", readonly=True
    )
    create_date = fields.Datetime(string="Created On", readonly=True)
    write_date = fields.Datetime(string="Last Updated On", readonly=True)

    @property
    def _table_query(self):
        return f"{self._select()} {self._from()} {self._group_by()}"

    def _select(self):
        select_str = """
                SELECT
                    po.id as order_id,
                    l.id as id,
                    l.name,
                    po.name as po_name,
                    po.date_order as date_order,
                    po.state,
                    po.date_approve,
                    po.partner_id as partner_id,
                    po.user_id as user_id,
                    po.company_id as company_id,
                    l.product_id,
                    p.product_tmpl_id,
                    t.categ_id as category_id,
                    po.currency_id,
                    t.uom_id as product_uom,
                    partner.commercial_partner_id as commercial_partner_id,
                    po.analytic_distribution as analytic_distribution,
                    l.price_unit,
                    l.price_subtotal,
                    l.price_total,
                    l.price_tax,
                    l.qty_invoiced,
                    l.qty_received,
                    l.qty_to_invoice,
                    l.product_uom_qty,
                    po.is_interco_partner,
                    l.create_date,
                    l.write_date
        """
        return select_str

    def _from(self):
        from_str = """
            FROM
            purchase_order_line l
                join purchase_order po on (l.order_id=po.id)
                join res_partner partner on po.partner_id = partner.id
                    left join product_product p on (l.product_id=p.id)
                        left join product_template t on (p.product_tmpl_id=t.id)
                left join uom_uom line_uom on (line_uom.id=l.product_uom)
                left join uom_uom product_uom on (product_uom.id=t.uom_id)
                left join {currency_table} ON currency_table.company_id = po.company_id
        """.format(
            currency_table=self.env["res.currency"]._get_query_currency_table(
                {"multi_company": True, "date": {"date_to": fields.Date.today()}}
            ),
        )
        return from_str

    def _group_by(self):
        group_by_str = ""
        return group_by_str

    @api.model
    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        count=False,
        access_rights_uid=None,
    ):
        args = AND(
            [
                args,
                [
                    (
                        "company_id",
                        "in",
                        self.env.company.sudo().purchase_intercompany_report_company_ids.ids,
                    ),
                    ("commercial_partner_id", "=", self.env.company.partner_id.id),
                ],
            ]
        )
        return super()._search(
            args, offset, limit, order, count=count, access_rights_uid=access_rights_uid
        )

    @api.model
    def read_group(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):
        domain = AND(
            [
                domain,
                [
                    (
                        "company_id",
                        "in",
                        self.env.company.sudo().purchase_intercompany_report_company_ids.ids,
                    ),
                    ("commercial_partner_id", "=", self.env.company.partner_id.id),
                ],
            ]
        )
        return super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)
