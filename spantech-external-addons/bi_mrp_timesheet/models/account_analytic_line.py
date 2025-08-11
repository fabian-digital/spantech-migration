# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _description = 'Analytic Line'

    production_id = fields.Many2one("mrp.production", string="Manufacturing Order")
    work_order_id = fields.Many2one("mrp.workorder", "Mrp Work order")

    @api.model
    def create(self, vals):
        res = super(AccountAnalyticLine, self).create(vals)
        workorder_id = self.env['mrp.workorder'].browse(self.env.context.get('active_id', False))
        if workorder_id.production_id.manage_timesheet_bool:
            workorder_id.production_id.write({'timesheet_ids': [(4, res.id)]})
        return res
