# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, models
from odoo.tools import float_compare


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _compute_inventory_value(self):
        self.env["account.move.line"].check_access_rights("read")
        to_date = self.env.context.get("at_date", False)
        accounting_values = {}
        layer_values = {}
        # pylint: disable=E8103
        query = """
            SELECT aml.product_id, aml.account_id,
            sum(aml.balance), sum(quantity),
            array_agg(aml.id)
            FROM account_move_line AS aml
            INNER JOIN account_move AS am ON am.id = aml.move_id
            WHERE aml.product_id IN %%s
            AND am.state = 'posted'
            AND aml.company_id=%%s %s
            GROUP BY aml.product_id, aml.account_id"""
        params = (
            tuple(
                self._ids,
            ),
            self.env.company.id,
        )
        if to_date:
            # pylint: disable=sql-injection
            query = query % ("AND aml.date <= %s",)
            params = params + (to_date,)
        else:
            query = query % ("",)
        # pylint: disable=E8103
        self.env.cr.execute(query, params=params)
        res = self.env.cr.fetchall()
        for row in res:
            accounting_values[(row[0], row[1])] = (row[2], row[3], list(row[4]))
        # pylint: disable=E8103
        query = """
            SELECT DISTINCT ON ("product_id") product_id, sum(quantity),
            sum(value), array_agg(svl.id)
            FROM   "stock_valuation_layer" AS svl
            WHERE svl.product_id IN %%s
            AND svl.company_id=%%s %s
            GROUP BY product_id
            ORDER BY "product_id" DESC NULLS LAST
            """
        params = (
            tuple(
                self._ids,
            ),
            self.env.company.id,
        )
        if to_date:
            # pylint: disable=sql-injection
            query = query % ("AND svl.date <= %s",)
            params = params + (to_date,)
        else:
            query = query % ("",)
        # pylint: disable=E8103
        self.env.cr.execute(query, params=params)
        res = self.env.cr.fetchall()
        aml_ids = self.env["account.move.line"]
        for row in res:
            layer_values[row[0]] = (row[1], row[2], list(row[3]))
        for product in self:
            # Retrieve the values from accounting
            # We cannot provide location-specific accounting valuation,
            # so better, leave the data empty in that case:
            if product.valuation == "real_time":
                valuation_account_id = (
                    product.categ_id.property_stock_valuation_account_id.id
                )
                value, quantity, aml_ids = accounting_values.get(
                    (product.id, valuation_account_id)
                ) or (0, 0, [])
                product.account_value = value
                product.account_qty_at_date = quantity
                product.stock_fifo_real_time_aml_ids = self.env[
                    "account.move.line"
                ].browse(aml_ids)
            else:
                product.account_value = 0.0
                product.account_qty_at_date = 0.0
                product.stock_fifo_real_time_aml_ids = []
            # Retrieve the values from inventory
            quantity, value, svl_ids = layer_values.get(product.id) or (0, 0, [])
            product.stock_value = value
            product.qty_at_date = quantity
            product.stock_valuation_layer_ids = self.env[
                "stock.valuation.layer"
            ].browse(svl_ids)
            if product.valuation == "real_time":
                product.valuation_discrepancy = (
                    product.stock_value - product.account_value
                )
                product.qty_discrepancy = (
                    product.qty_at_date - product.account_qty_at_date
                )
            else:
                product.valuation_discrepancy = 0.0
                product.qty_discrepancy = 0.0

    @api.model
    def _search_qty_discrepancy(self, operator, value):
        precision = self.env["decimal.precision"].precision_get("Product Price")
        products = self.env["product.product"].search([("type", "=", "product")])
        pp_list = []
        for pp in products:
            if (
                float_compare(
                    pp.qty_at_date, pp.account_qty_at_date, precision_digits=precision
                )
                != 0
            ):
                pp_list.append(pp.id)
        return [("id", "in", pp_list)]

    @api.model
    def _search_valuation_discrepancy(self, operator, value):
        precision = self.env["decimal.precision"].precision_get("Product Price")
        products = self.env["product.product"].search([("type", "=", "product")])
        pp_list = []
        for pp in products:
            if (
                float_compare(
                    pp.stock_value, pp.account_value, precision_digits=precision
                )
                != 0
            ):
                pp_list.append(pp.id)
        return [("id", "in", pp_list)]
