# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context


class ProductReplenish(models.TransientModel):
    _inherit = "product.replenish"
    _description = "Product Replenish"

    line_ids = fields.One2many(
        comodel_name="product.replenish.line", inverse_name="replenish_id"
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if res.get("warehouse_id", False):
            Forecast = self.env["report.stock.report_product_product_replenishment"]
            ForecastWH = Forecast.with_context(warehouse=res["warehouse_id"])
            product = res["product_id"]
            data = ForecastWH._get_report_data(product_variant_ids=[product])
            line_ids_vals = []
            total_quantity = 0.0
            for line in data["lines"]:
                if not line["document_in"] and line["document_out"]:
                    line_ids_vals.append(
                        (
                            0,
                            0,
                            {
                                "res_id": line["document_out"].id,
                                "res_name": line["document_out"].name,
                                "res_model": line["document_out"]._name,
                                "res_line_id": line["move_out"].sale_line_id.id,
                                "commitment_date": line[
                                    "move_out"
                                ].sale_line_id.commitment_date,
                                "quantity": line["quantity"],
                                "unit_id": line["uom_id"].id,
                            },
                        )
                    )
                    total_quantity += float(line["quantity"])
            res.update({"line_ids": line_ids_vals, "quantity": total_quantity})
        return res

    def launch_replenishment(self):
        if self.line_ids:
            uom_reference = self.product_id.uom_id
            for line in self.line_ids:
                quantity = line.unit_id._compute_quantity(line.quantity, uom_reference)
                order_id = self.env[line.res_model].browse(line.res_id)
                context = self.env.context.copy()
                context.update({"sale_line_id": line.res_line_id})
                try:
                    self.env["procurement.group"].with_context(
                        **clean_context(context)
                    ).run(
                        [
                            self.env["procurement.group"].Procurement(
                                self.product_id,
                                quantity,
                                uom_reference,
                                self.warehouse_id.lot_stock_id,  # Location
                                self.product_id.display_name,  # Name
                                order_id.name,  # Origin
                                self.warehouse_id.company_id,
                                self._prepare_run_values(),  # Values
                            )
                        ]
                    )
                except UserError as error:
                    raise UserError(error) from error
        else:
            super().launch_replenishment()
        return

    @api.onchange("line_ids", "line_ids.quantity")
    def _onchange_line_ids_quantity(self):
        self.quantity = sum(self.line_ids.mapped("quantity"))


class ProductReplenishLine(models.TransientModel):
    _name = "product.replenish.line"
    _description = "Product Replenish Line"

    replenish_id = fields.Many2one(comodel_name="product.replenish")
    res_model = fields.Char()
    res_id = fields.Integer()
    res_name = fields.Char()
    res_line_id = fields.Integer()
    commitment_date = fields.Datetime(string="Delivery Date")
    quantity = fields.Float(digits="Product Unit of Measure")
    unit_id = fields.Many2one(comodel_name="uom.uom")
