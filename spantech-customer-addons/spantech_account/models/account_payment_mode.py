# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentMode(models.Model):
    _inherit = "account.payment.mode"

    default_invoice_approved = fields.Boolean(string="Default only approved invoices")
