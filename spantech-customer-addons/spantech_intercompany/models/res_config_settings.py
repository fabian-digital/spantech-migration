# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    interco_po_notif_user_ids = fields.Many2many(
        comodel_name="res.users",
        related="company_id.interco_po_notif_user_ids",
        readonly=False,
    )
    interco_so_notif_user_ids = fields.Many2many(
        comodel_name="res.users",
        related="company_id.interco_so_notif_user_ids",
        readonly=False,
    )
    interco_am_notif_user_ids = fields.Many2many(
        comodel_name="res.users",
        related="company_id.interco_am_notif_user_ids",
        readonly=False,
    )
    purchase_intercompany_report_company_ids = fields.Many2many(
        comodel_name="res.company",
        related="company_id.purchase_intercompany_report_company_ids",
        readonly=False,
    )
