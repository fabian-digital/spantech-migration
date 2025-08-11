# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import io
from datetime import datetime, time, timedelta

from pytz import UTC

from odoo import _, fields, models

try:
    import xlwt
except ImportError:
    xlwt = None


class SpantechStockFifoValuationReportWizard(models.TransientModel):
    _name = "spantech.stock.fifo.valuation.report.wizard"

    start_date = fields.Date(string="Start Period", required=True)
    end_date = fields.Date(string="End Period", required=True)
    warehouse_ids = fields.Many2many(comodel_name="stock.warehouse", string="Warehouse")
    category_id = fields.Many2many(
        comodel_name="product.category",
        relation="category_fifo_valuation_report_wizard_rel",
    )
    location_id = fields.Many2one(comodel_name="stock.location", string="Location")
    company_id = fields.Many2one(comodel_name="res.company", string="Company")
    display_sum = fields.Boolean(string="Summary")
    product_ids = fields.Many2many(
        comodel_name="product.product",
        relation="product_fifo_valuation_report_wizard_rel",
        string="Product",
    )
    filter_by = fields.Selection(
        selection=[("product", "Product"), ("categ", "Category")],
        default="product",
    )

    def _get_warehouse_name(self):
        warehouse_names = ""
        if self.warehouse_ids:
            warehouses = []
            for warehouse in self.warehouse_ids:
                warehouses.append(warehouse.name)
                warehouse_names = ",".join(warehouses)
        return warehouse_names

    def get_lines(self, data):  # noqa: C901
        operation_types = dict(
            self.env["stock.valuation.layer"]._fields["operation_type"].selection
        )
        svl_res = self.env["stock.valuation.layer"]
        product_res = self.env["product.product"]
        if data["product_ids"] and data["filter_by"] == "product":
            product_res = data["product_ids"]
        elif data["category"] and data["filter_by"] == "categ":
            category_lst = []
            for cate in data["category"]:
                if cate.id not in category_lst:
                    category_lst.append(cate.id)

                for child in cate.child_id:
                    if child.id not in category_lst:
                        category_lst.append(child.id)
                if len(category_lst) > 0:
                    product_res = svl_res.search(
                        [
                            ("categ_id", "in", category_lst),
                            ("product_id.type", "=", "product"),
                        ]
                    ).mapped("product_id")
        if not product_res:
            product_res = svl_res.search(
                [
                    ("product_id.type", "=", "product"),
                ]
            ).mapped("product_id")

        lines = {}
        for product in product_res:
            if product.default_code:
                product_full_name = product.name + " [" + product.default_code + "]"
            else:
                product_full_name = product.name
            if product.categ_id.property_cost_method == "fifo":
                custom_domain = []
                move_domain = []
                if data["company_id"]:
                    obj = self.env["res.company"].search(
                        [("name", "=", data["company_id"])]
                    )

                    custom_domain.append(("company_id", "=", obj.id))
                    move_domain.append(("company_id", "=", obj.id))

                if data["warehouse"]:
                    warehouse_lst = [a.id for a in data["warehouse"]]
                    custom_domain.append(
                        ("stock_move_id.warehouse_id", "in", warehouse_lst)
                    )
                    move_domain.append(("warehouse_id", "in", warehouse_lst))

                if data["location_id"]:
                    custom_domain.append("|")
                    custom_domain.append(
                        ("stock_move_id.location_dest_id", "=", data["location_id"].id)
                    )
                    custom_domain.append(
                        ("stock_move_id.location_id", "=", data["location_id"].id)
                    )
                    move_domain.append("|")
                    move_domain.append(
                        ("location_dest_id", "=", data["location_id"].id)
                    )
                    move_domain.append(("location_id", "=", data["location_id"].id))

                fifo_vals = {}

                start_date = (
                    datetime.combine(
                        data["start_date"],
                        time(hour=00, minute=0, second=0),
                    )
                    .astimezone(UTC)
                    .strftime("%Y-%m-%d %H:%M")
                )
                end_date = (
                    datetime.combine(
                        data["end_date"],
                        time(hour=23, minute=59, second=59),
                    )
                    .astimezone(UTC)
                    .strftime("%Y-%m-%d %H:%M")
                )
                to_date = (
                    datetime.combine(
                        data["start_date"] - timedelta(days=1),
                        time(hour=23, minute=59, second=59),
                    )
                    .astimezone(UTC)
                    .strftime("%Y-%m-%d %H:%M")
                )
                to_date_context = {
                    "to_date": to_date,
                    "at_date": to_date,
                }
                product_to_date = product.with_context(**to_date_context)
                qty_date = product_to_date.qty_at_date
                stock_val_layer = self.env["stock.valuation.layer"].search(
                    [
                        ("product_id", "=", product.id),
                        ("date", ">=", start_date),
                        ("date", "<=", end_date),
                    ]
                    + custom_domain
                )
                if product_to_date.stock_valuation_layer_ids or stock_val_layer:
                    vals = {
                        "sku": product.default_code or "",
                        "name": product.name or "",
                        "category": product.categ_id.name or "",
                        "cost_price": 0,
                        "opening": qty_date,
                        "opening_value": product_to_date.stock_value,
                        "available": 0,
                        "virtual": 0,
                        "incoming": 0,
                        "incoming_value": 0,
                        "outgoing": 0,
                        "outgoing_value": 0,
                        "manufacture": 0,
                        "manufacture_value": 0,
                        "adjust": 0,
                        "adjust_value": 0,
                        "total_value": product_to_date.stock_value,
                        "purchase_value": 0,
                        "type": "Opening",
                        "internal": 0,
                        "internal_value": 0,
                        "price_unit": 0,
                        "qty_date": qty_date,
                        "date": to_date,
                        "is_opening": True,
                        "reference": "Opening - " + product.default_code,
                    }
                    fifo_vals.update({"Opening - " + product.default_code: vals})
                    for layer in stock_val_layer:
                        if layer.id not in fifo_vals:
                            vals = {
                                "sku": product.default_code or "",
                                "name": product.name or "",
                                "category": product.categ_id.name or "",
                                "cost_price": layer.currency_id.round(layer.unit_cost)
                                or 0,
                                "opening": 0,
                                "opening_value": 0,
                                "available": 0,
                                "virtual": 0,
                                "incoming": 0,
                                "incoming_value": 0,
                                "outgoing": 0,
                                "outgoing_value": 0,
                                "manufacture": 0,
                                "manufacture_value": 0,
                                "adjust": 0,
                                "adjust_value": 0,
                                "net_on_hand": layer.quantity,
                                "total_value": layer.currency_id.round(layer.value)
                                or 0,
                                "purchase_value": 0,
                                "type": operation_types.get(layer.operation_type),
                                "internal": 0,
                                "internal_value": 0,
                                "price_unit": layer.unit_cost,
                                "qty_date": 0,
                                "date": fields.Datetime.context_timestamp(
                                    self.env.user, layer.date
                                ).strftime("%Y-%m-%d %H:%M"),
                            }
                            if layer.operation_type == "opening":
                                qty_date = qty_date + layer.quantity
                                vals["qty_date"] = qty_date
                                vals["opening"] = layer.quantity
                                vals["opening_value"] = layer.currency_id.round(
                                    layer.value
                                )
                            elif layer.operation_type == "inventory":
                                qty_date = qty_date + layer.quantity
                                vals["qty_date"] = qty_date
                                vals["adjust"] = layer.quantity
                                vals["adjust_value"] = layer.currency_id.round(
                                    layer.value
                                )
                            elif layer.operation_type == "manufacture":
                                qty_date = qty_date + layer.quantity
                                vals["qty_date"] = qty_date
                                vals["manufacture"] = layer.quantity
                                vals["manufacture_value"] = layer.currency_id.round(
                                    layer.value
                                )
                            elif layer.stock_move_id.picking_code == "outgoing":
                                qty_date = qty_date + layer.quantity
                                vals["qty_date"] = qty_date
                                vals["outgoing"] = layer.quantity
                                vals["outgoing_value"] = layer.currency_id.round(
                                    layer.value
                                )
                            elif layer.stock_move_id.picking_code == "incoming":
                                qty_date = qty_date + layer.quantity
                                vals["qty_date"] = qty_date
                                vals["incoming"] = layer.quantity
                                vals["incoming_value"] = layer.currency_id.round(
                                    layer.value
                                )
                            else:
                                qty_date = qty_date + layer.quantity
                                vals["qty_date"] = qty_date
                                vals["internal"] = layer.quantity
                                vals["internal_value"] = layer.currency_id.round(
                                    layer.value
                                )
                            if layer.stock_move_id.reference:
                                vals["reference"] = layer.stock_move_id.reference
                            else:
                                vals["reference"] = layer.description
                            fifo_vals.update({layer.id: vals})
                    if fifo_vals:
                        lines.update({product_full_name: fifo_vals})
        return lines

    def get_data(self, data):  # noqa: C901
        product_res = self.env["product.product"]
        if data["product_ids"]:
            product_res = data["product_ids"]
        elif data["category"]:
            category_lst = []
            for cate in data["category"]:
                if cate.id not in category_lst:
                    category_lst.append(cate.id)

                for child in cate.child_id:
                    if child.id not in category_lst:
                        category_lst.append(child.id)
                if len(category_lst) > 0:
                    product_res = self.env["product.product"].search(
                        [
                            ("categ_id", "in", category_lst),
                            ("stock_move_ids", "!=", False),
                            ("type", "=", "product"),
                        ]
                    )
        if not product_res:
            product_res = self.env["product.product"].search(
                [
                    ("stock_move_ids", "!=", False),
                    ("type", "=", "product"),
                ]
            )
        fifo_vals = {}
        for product in product_res:
            if product.categ_id.property_cost_method == "fifo":
                custom_domain = []
                move_domain = []
                if data["company_id"]:
                    obj = self.env["res.company"].search(
                        [("name", "=", data["company_id"])]
                    )

                    custom_domain.append(("company_id", "=", obj.id))
                    move_domain.append(("company_id", "=", obj.id))

                if data["warehouse"]:
                    warehouse_lst = [a.id for a in data["warehouse"]]
                    custom_domain.append(
                        ("stock_move_id.warehouse_id", "in", warehouse_lst)
                    )
                    move_domain.append(("warehouse_id", "in", warehouse_lst))

                if data["location_id"]:
                    custom_domain.append("|")
                    custom_domain.append(
                        ("stock_move_id.location_dest_id", "=", data["location_id"].id)
                    )
                    custom_domain.append(
                        ("stock_move_id.location_id", "=", data["location_id"].id)
                    )
                    move_domain.append("|")
                    move_domain.append(
                        ("location_dest_id", "=", data["location_id"].id)
                    )
                    move_domain.append(("location_id", "=", data["location_id"].id))

                to_date = datetime.combine(
                    data["start_date"] - timedelta(days=1),
                    time(hour=23, minute=59, second=59),
                )
                to_date_context = {
                    "to_date": to_date,
                    "at_date": to_date,
                }
                product_to_date = product.with_context(**to_date_context)
                qty_date = product_to_date.qty_at_date
                stock_val_layer = self.env["stock.valuation.layer"].search(
                    [
                        ("product_id", "=", product.id),
                        ("date", ">=", data["start_date"]),
                        ("date", "<=", data["end_date"]),
                    ]
                    + custom_domain
                )
                if product_to_date.stock_valuation_layer_ids or stock_val_layer:
                    if product.categ_id.name not in fifo_vals:
                        vals = {
                            "incoming": 0,
                            "incoming_value": 0,
                            "outgoing": 0,
                            "outgoing_value": 0,
                            "adjust": 0,
                            "adjust_value": 0,
                            "opening": 0,
                            "opening_value": 0,
                            "manufacture": 0,
                            "manufacture_value": 0,
                            "internal": 0,
                            "internal_value": 0,
                            "net_on_hand": 0,
                            "total_value": 0,
                            "purchase_value": 0,
                        }
                        fifo_vals.update({product.categ_id.name: vals})
                    fifo_vals.get(product.categ_id.name).update(
                        {
                            "opening_value": fifo_vals.get(product.categ_id.name).get(
                                "opening_value"
                            )
                            + product_to_date.stock_value,
                            "opening": fifo_vals.get(product.categ_id.name).get(
                                "opening"
                            )
                            + qty_date,
                        }
                    )
                    for layer in stock_val_layer:
                        fifo_vals.get(product.categ_id.name).update(
                            {
                                "total_value": fifo_vals.get(product.categ_id.name).get(
                                    "total_value"
                                )
                                + layer.value,
                            }
                        )
                        if layer.operation_type == "inventory":
                            fifo_vals.get(product.categ_id.name).update(
                                {
                                    "adjust": fifo_vals.get(product.categ_id.name).get(
                                        "adjust"
                                    )
                                    + layer.quantity,
                                    "adjust_value": fifo_vals.get(
                                        product.categ_id.name
                                    ).get("adjust_value")
                                    + layer.value,
                                }
                            )
                        elif layer.operation_type == "manufacture":
                            fifo_vals.get(product.categ_id.name).update(
                                {
                                    "manufacture": fifo_vals.get(
                                        product.categ_id.name
                                    ).get("manufacture")
                                    + layer.quantity,
                                    "manufacture_value": fifo_vals.get(
                                        product.categ_id.name
                                    ).get("manufacture_value")
                                    + layer.value,
                                }
                            )
                        elif layer.stock_move_id.picking_code == "outgoing":
                            fifo_vals.get(product.categ_id.name).update(
                                {
                                    "outgoing": fifo_vals.get(
                                        product.categ_id.name
                                    ).get("outgoing")
                                    + layer.quantity,
                                    "outgoing_value": fifo_vals.get(
                                        product.categ_id.name
                                    ).get("outgoing_value")
                                    + layer.value,
                                }
                            )
                        elif layer.stock_move_id.picking_code == "incoming":
                            fifo_vals.get(product.categ_id.name).update(
                                {
                                    "incoming": fifo_vals.get(
                                        product.categ_id.name
                                    ).get("incoming")
                                    + layer.quantity,
                                    "incoming_value": fifo_vals.get(
                                        product.categ_id.name
                                    ).get("incoming_value")
                                    + layer.value,
                                }
                            )
                        else:
                            fifo_vals.get(product.categ_id.name).update(
                                {
                                    "internal": fifo_vals.get(
                                        product.categ_id.name
                                    ).get("internal")
                                    + layer.quantity,
                                    "internal_value": fifo_vals.get(
                                        product.categ_id.name
                                    ).get("internal_value")
                                    + layer.value,
                                }
                            )
        return fifo_vals

    def print_xls_report(self):
        if self.filter_by == "product" and not self.display_sum:
            for product in self.product_ids:
                if product.categ_id.property_cost_method != "fifo":
                    raise Warning(
                        _("Costing Method For %s Product  Should Be FIFO")
                        % product.name
                    )

        if self.filter_by == "categ" and not self.display_sum:
            for cate in self.category_id:
                if cate.property_cost_method != "fifo":
                    raise Warning(
                        _("Costing Method For %s  Product Category  Should Be FIFO")
                        % cate.display_name
                    )

        data = {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "warehouse": self.warehouse_ids,
            "category": self.category_id,
            "location_id": self.location_id,
            "company_id": self.company_id.name,
            "display_sum": self.display_sum,
            "currency": self.company_id.currency_id.name,
            "product_ids": self.product_ids,
            "filter_by": self.filter_by,
        }
        filename = "Stock Valuation Report.xls"
        get_warehouse_name = self._get_warehouse_name()
        workbook = xlwt.Workbook()
        stylePC = xlwt.XFStyle()
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        fontP = xlwt.Font()
        fontP.bold = True
        fontP.height = 200
        stylePC.font = fontP
        stylePC.num_format_str = "@"
        stylePC.alignment = alignment
        style_title = xlwt.easyxf(
            "font:height 300; font: name Liberation Sans, "
            "bold on,color blue; align: horiz center"
        )
        style_table_header = xlwt.easyxf(
            "font:height 200; font: name Liberation Sans, "
            "bold on,color black; align: horiz center"
        )
        style_table_product = xlwt.easyxf(
            "font:height 200;pattern: pattern solid, pattern_fore_colour gray25;font: "
            "name Liberation Sans, bold on,color black; align: horiz center"
        )
        style = xlwt.easyxf("font:height 200; font: name Liberation Sans,color black;")
        worksheet = workbook.add_sheet("Sheet 1")
        currency_id = self.company_id.currency_id or self.env.company.currency_id
        if self.display_sum:
            worksheet.write(6, 4, "Start Date:", style_table_product)
            worksheet.write(7, 4, str(self.start_date))
            worksheet.write(6, 5, "End Date", style_table_product)
            worksheet.write(7, 5, str(self.end_date))
            worksheet.write(6, 6, "Company", style_table_product)
            worksheet.write(
                7,
                6,
                self.company_id.name or self.env.company.name or "",
            )
            worksheet.write(6, 7, "Warehouse(s)", style_table_product)
            worksheet.write(6, 8, "Currency", style_table_product)
            worksheet.write(
                7,
                8,
                self.company_id.currency_id.name
                or self.env.company.currency_id.name
                or "",
            )
            if get_warehouse_name:
                worksheet.write(7, 7, get_warehouse_name, stylePC)
            total_inv_val = 0
            worksheet.write_merge(
                1, 2, 2, 14, "Inventory Valuation Summary Report", style=style_title
            )
            worksheet.write(9, 2, "Category", style_table_product)
            worksheet.write(9, 3, "Opening (Val)", style_table_product)
            worksheet.write(9, 4, "Opening (Qty)", style_table_product)
            worksheet.write(9, 5, "Received (Val)", style_table_product)
            worksheet.write(9, 6, "Received (Qty)", style_table_product)
            worksheet.write(9, 7, "Sales (Val)", style_table_product)
            worksheet.write(9, 8, "Sales (Qty)", style_table_product)
            worksheet.write(9, 9, "Manufacturing (Val)", style_table_product)
            worksheet.write(9, 10, "Manufacturing (Qty)", style_table_product)
            worksheet.write(9, 11, "Internal (Val)", style_table_product)
            worksheet.write(9, 12, "Internal (Qty)", style_table_product)
            worksheet.write(9, 13, "Adjustment (Val)", style_table_product)
            worksheet.write(9, 14, "Adjustment (Qty)", style_table_product)
            worksheet.write(9, 15, "Valuation", style_table_product)
            prod_row = 10
            prod_col = 2

            get_line = self.get_data(data)
            for each in get_line:
                worksheet.write(prod_row, prod_col, each, style)
                worksheet.write(
                    prod_row,
                    prod_col + 1,
                    currency_id.round(get_line.get(each).get("opening_value")),
                    style,
                )
                worksheet.write(
                    prod_row,
                    prod_col + 2,
                    currency_id.round(get_line.get(each).get("opening")),
                    style,
                )
                worksheet.write(
                    prod_row,
                    prod_col + 3,
                    currency_id.round(get_line.get(each).get("incoming_value")),
                    style,
                )
                worksheet.write(
                    prod_row,
                    prod_col + 4,
                    currency_id.round(get_line.get(each).get("incoming")),
                    style,
                )
                worksheet.write(
                    prod_row,
                    prod_col + 5,
                    currency_id.round(get_line.get(each).get("outgoing_value")),
                    style,
                )
                worksheet.write(
                    prod_row,
                    prod_col + 6,
                    currency_id.round(get_line.get(each).get("outgoing")),
                    style,
                )
                worksheet.write(
                    prod_row,
                    prod_col + 7,
                    currency_id.round(get_line.get(each).get("manufacture_value")),
                    style,
                )
                worksheet.write(
                    prod_row,
                    prod_col + 8,
                    currency_id.round(get_line.get(each).get("manufacture")),
                    style,
                )
                worksheet.write(
                    prod_row,
                    prod_col + 9,
                    currency_id.round(get_line.get(each).get("internal_value")),
                    style,
                )
                worksheet.write(
                    prod_row,
                    prod_col + 10,
                    currency_id.round(get_line.get(each).get("internal")),
                    style,
                )
                worksheet.write(
                    prod_row,
                    prod_col + 11,
                    currency_id.round(get_line.get(each).get("adjust_value")),
                    style,
                )
                worksheet.write(
                    prod_row,
                    prod_col + 12,
                    currency_id.round(get_line.get(each).get("adjust")),
                    style,
                )
                worksheet.write(
                    prod_row,
                    prod_col + 13,
                    currency_id.round(get_line.get(each).get("total_value")),
                    style,
                )
                total_inv_val = total_inv_val + get_line.get(each).get("total_value")
                prod_row = prod_row + 1

            worksheet.write(prod_row + 2, 12, "Total Valuation", style_table_header)
            worksheet.write(prod_row + 2, 13, currency_id.round(total_inv_val), style)

        else:
            worksheet.write(6, 5, "Start Date:", style_table_product)
            worksheet.write(7, 5, str(self.start_date))
            worksheet.write(6, 6, "End Date", style_table_product)
            worksheet.write(7, 6, str(self.end_date))
            worksheet.write(6, 7, "Company", style_table_product)
            worksheet.write(
                7,
                7,
                self.company_id.name or self.env.company.name or "",
            )
            worksheet.write(6, 8, "Warehouse(s)", style_table_product)
            worksheet.write(6, 9, "Currency", style_table_product)
            worksheet.write(
                7,
                9,
                self.company_id.currency_id.name
                or self.env.company.currency_id.name
                or "",
            )
            if get_warehouse_name:
                worksheet.write(7, 8, get_warehouse_name, stylePC)
            worksheet.write_merge(
                1, 2, 1, 17, "Inventory Valuation Report", style=style_title
            )

            prod_row = 10
            prod_col = 0
            total_inv_val = 0
            total_opening_val = 0
            get_line = self.get_lines(data)
            for each in get_line:
                worksheet.write_merge(
                    prod_row, prod_row, 0, 18, each, style=style_table_product
                )
                prod_row = prod_row + 1
                worksheet.write(prod_row, 0, "Default Code", style_table_header)
                worksheet.write(prod_row, 1, "Date", style_table_header)
                worksheet.write(prod_row, 2, "Reference", style_table_header)
                worksheet.write(prod_row, 3, "Type", style_table_header)
                worksheet.write(prod_row, 4, "Category", style_table_header)
                worksheet.write(prod_row, 5, "Cost Price", style_table_header)
                worksheet.write(prod_row, 6, "Opening (Val)", style_table_header)
                worksheet.write(prod_row, 7, "Opening (Qty)", style_table_header)
                worksheet.write(prod_row, 8, "Received (Val)", style_table_header)
                worksheet.write(prod_row, 9, "Received (Qty)", style_table_header)
                worksheet.write(prod_row, 10, "Sales (Val)", style_table_header)
                worksheet.write(prod_row, 11, "Sales (Qty)", style_table_header)
                worksheet.write(prod_row, 12, "Manufacture (Val)", style_table_header)
                worksheet.write(prod_row, 13, "Manufacture (Qty)", style_table_header)
                worksheet.write(prod_row, 14, "Internal (Val)", style_table_header)
                worksheet.write(prod_row, 15, "Internal (Qty)", style_table_header)
                worksheet.write(prod_row, 16, "Adjustment (Val)", style_table_header)
                worksheet.write(prod_row, 17, "Adjustment (Qty)", style_table_header)
                worksheet.write(prod_row, 18, "Available", style_table_header)
                worksheet.write(prod_row, 19, "Value", style_table_header)
                total_val = 0
                prod_row = prod_row + 1
                for line in get_line.get(each):
                    worksheet.write(
                        prod_row, 0, get_line.get(each).get(line).get("sku"), style
                    )
                    worksheet.write(
                        prod_row,
                        1,
                        str(get_line.get(each).get(line).get("date")),
                        style,
                    )
                    worksheet.write(
                        prod_row,
                        2,
                        get_line.get(each).get(line).get("reference"),
                        style,
                    )
                    worksheet.write(
                        prod_row, 3, get_line.get(each).get(line).get("type"), style
                    )
                    worksheet.write(
                        prod_row, 4, get_line.get(each).get(line).get("category"), style
                    )
                    worksheet.write(
                        prod_row,
                        5,
                        get_line.get(each).get(line).get("cost_price"),
                        style,
                    )
                    worksheet.write(
                        prod_row,
                        6,
                        get_line.get(each).get(line).get("opening_value"),
                        style,
                    )
                    worksheet.write(
                        prod_row, 7, get_line.get(each).get(line).get("opening"), style
                    )
                    worksheet.write(
                        prod_row,
                        8,
                        get_line.get(each).get(line).get("incoming_value"),
                        style,
                    )
                    worksheet.write(
                        prod_row, 9, get_line.get(each).get(line).get("incoming"), style
                    )
                    worksheet.write(
                        prod_row,
                        10,
                        get_line.get(each).get(line).get("outgoing_value"),
                        style,
                    )
                    worksheet.write(
                        prod_row,
                        11,
                        get_line.get(each).get(line).get("outgoing"),
                        style,
                    )
                    worksheet.write(
                        prod_row,
                        12,
                        get_line.get(each).get(line).get("manufacture_value"),
                        style,
                    )
                    worksheet.write(
                        prod_row,
                        13,
                        get_line.get(each).get(line).get("manufacture"),
                        style,
                    )
                    worksheet.write(
                        prod_row,
                        15,
                        get_line.get(each).get(line).get("internal_value"),
                        style,
                    )
                    worksheet.write(
                        prod_row,
                        16,
                        get_line.get(each).get(line).get("internal"),
                        style,
                    )
                    worksheet.write(
                        prod_row,
                        17,
                        get_line.get(each).get(line).get("adjust_value"),
                        style,
                    )
                    worksheet.write(
                        prod_row, 18, get_line.get(each).get(line).get("adjust"), style
                    )
                    worksheet.write(
                        prod_row,
                        19,
                        get_line.get(each).get(line).get("qty_date"),
                        style,
                    )
                    worksheet.write(
                        prod_row,
                        20,
                        get_line.get(each).get(line).get("total_value"),
                        style,
                    )
                    total_val = total_val + get_line.get(each).get(line).get(
                        "total_value"
                    )
                    if get_line.get(each).get(line).get("is_opening", False):
                        total_opening_val = total_opening_val + get_line.get(each).get(
                            line
                        ).get("total_value")
                    prod_row = prod_row + 1
                worksheet.write(prod_row, 19, "Valuation", style_table_header)
                worksheet.write(prod_row, 20, currency_id.round(total_val), style)
                total_inv_val = total_inv_val + total_val
                prod_row = prod_row + 1

            worksheet.write(
                prod_row + 2, 17, "Total Opening Valuation", style_table_header
            )
            worksheet.write(
                prod_row + 2, 18, currency_id.round(total_opening_val), style
            )
            worksheet.write(prod_row + 2, 19, "Total Valuation", style_table_header)
            worksheet.write(prod_row + 2, 20, currency_id.round(total_inv_val), style)

        fp = io.BytesIO()
        workbook.save(fp)
        export_id = self.env[
            "spantech.stock.fifo.valuation.report.excel.wizard"
        ].create(
            [{"excel_file": base64.encodebytes(fp.getvalue()), "file_name": filename}]
        )
        res = {
            "view_mode": "form",
            "res_id": export_id.id,
            "res_model": "spantech.stock.fifo.valuation.report.excel.wizard",
            "view_type": "form",
            "type": "ir.actions.act_window",
            "target": "new",
        }
        return res


class SpantechStockFifoValuationReportExcelWizard(models.TransientModel):
    _name = "spantech.stock.fifo.valuation.report.excel.wizard"

    excel_file = fields.Binary()
    file_name = fields.Char("Excel File", size=64)
