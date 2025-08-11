# Copyright 2009-2022 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import io
import logging

from xlsxwriter.exceptions import UnsupportedImageFormat

from odoo import models

_logger = logging.getLogger(__name__)


class BomStructureXlsx(models.AbstractModel):
    _name = "report.spantech_mrp.bom_structure_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "XLSX Reporting for MRP BOM"

    def generate_xlsx_report(self, workbook, data, bom_ids):
        for obj in bom_ids:
            vals_list = []
            self.get_bom_lines_vals(obj.bom_line_ids, 1, vals_list)

            structured_sheet = self.get_worksheet(workbook, "Bom Structure")
            self.write_bom_lines(vals_list, structured_sheet, workbook)

            consolidated_vals_list = self.get_consolidated_vals_list(vals_list)
            consolidated_sheet = self.get_worksheet(workbook, "BOM Consolidated")
            self.write_bom_lines(consolidated_vals_list, consolidated_sheet, workbook)

            consolidated_by_level_vals_list = self.get_consolidated_by_level_vals_list(
                vals_list
            )
            consolidated_level_sheet = self.get_worksheet(
                workbook, "BOM Consolidated By Level"
            )
            self.write_bom_lines(
                consolidated_by_level_vals_list, consolidated_level_sheet, workbook
            )

    def get_worksheet(self, workbook, name):
        sheet = workbook.add_worksheet(name)
        header_style = workbook.add_format({"bold": True, "align": "center"})
        sheet.set_column("A:A", 80)
        sheet.set_column("B:D", 20)
        sheet.set_column("E:E", 15)
        sheet.set_column("F:F", 10)
        sheet.set_default_row(70)
        sheet.set_row(0, 15)

        sheet.write(0, 0, "Product Name", header_style)
        sheet.write(0, 1, "Product Code", header_style)
        sheet.write(0, 2, "Product Quantity", header_style)
        sheet.write(0, 3, "Product UOM", header_style)
        sheet.write(0, 4, "Product Image", header_style)
        sheet.write(0, 5, "BOM Level", header_style)
        return sheet

    def get_bom_lines_vals(self, bom_lines, level, vals_list, parent_qty=1):
        for line in bom_lines:
            vals = {}
            vals["product_id"] = line.product_id.id
            vals["product_name"] = line.product_id.name
            vals["product_code"] = line.product_id.default_code
            vals["product_qty"] = line.product_qty * parent_qty
            vals["product_uom"] = line.product_uom_id.name
            vals["product_image"] = line.product_id.image_1920
            vals["product_level"] = level
            vals_list.append(vals)
            if line.child_line_ids:
                self.get_bom_lines_vals(
                    line.child_line_ids, level + 1, vals_list, vals["product_qty"]
                )

    def get_consolidated_vals_list(self, vals_list):
        datas = {}
        for vals in vals_list:
            if vals["product_id"] in datas.keys():
                tmp = datas[vals["product_id"]]
                tmp["product_qty"] += vals["product_qty"]
                datas[vals["product_id"]] = tmp
            else:
                datas[vals["product_id"]] = vals
        ret = sorted(list(datas.values()), key=lambda x: x["product_level"])
        return ret

    def get_consolidated_by_level_vals_list(self, vals_list):
        datas = {}
        for vals in vals_list:
            key = f"{vals['product_id']}:{vals['product_level']}"
            if key in datas.keys():
                tmp = datas[key]
                tmp["product_qty"] += vals["product_qty"]
                datas[key] = tmp
            else:
                datas[key] = vals
        ret = sorted(list(datas.values()), key=lambda x: x["product_level"])
        return ret

    def write_bom_lines(self, vals_list, sheet, workbook):
        row = 1
        for vals in vals_list:
            sheet.write(row, 0, vals["product_name"])
            sheet.write(row, 1, vals["product_code"] or "")
            sheet.write(row, 2, vals["product_qty"])
            sheet.write(row, 3, vals["product_uom"])
            if vals.get("product_image", False) and vals.get("product_code", False):
                product_image = io.BytesIO(base64.b64decode(vals["product_image"]))
                try:
                    workbook._get_image_properties(
                        vals["product_code"] + ".jpg", product_image
                    )
                    sheet.insert_image(
                        row,
                        4,
                        vals["product_code"] + ".jpg",
                        {
                            "image_data": product_image,
                            "x_scale": 0.3,
                            "y_scale": 0.3,
                            "positioning": 1,
                        },
                    )
                except UnsupportedImageFormat:
                    _logger.exception(
                        "UnsupportedImageFormat while printing "
                        "report_bom_structure_xlsx"
                    )

            sheet.write(row, 5, vals["product_level"])
            row += 1
