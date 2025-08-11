# Copyright 2009-2022 Noviat.
# License LGPL-3 or later (http://www.gnu.org/licenses/lpgl).

from odoo import fields, models


class AccountTaxGroup(models.Model):
    _inherit = "account.tax.group"

    country_id = fields.Many2one(comodel_name="res.country", string="Country")
