# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class MRPProductionInherit(models.Model):
    _inherit = "mrp.production"

    timesheet_ids = fields.One2many("account.analytic.line", "production_id", string="Timesheet")
    manage_timesheet_bool = fields.Boolean(string="Manage Timesheet", default=False)


class MRPWorkOrderInherit(models.Model):
    _inherit = "mrp.workorder"

    timesheet_ids = fields.One2many("account.analytic.line", "work_order_id", string="Timesheet")
    work_order_id = fields.Many2one("mrp.workorder", "Mrp Work order")

