# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_product_accounts(self):
        res = super()._get_product_accounts()
        company = self.env.company
        if company.country_id.code == "DE":
            if (
                not self.property_account_income_id
                and self.categ_id.property_account_income_categ_id
            ):
                res["income"] = self.categ_id.property_account_income_categ_id
            if (
                not self.property_account_expense_id
                and self.categ_id.property_account_expense_categ_id
            ):
                res["expense"] = self.categ_id.property_account_expense_categ_id
        return res
