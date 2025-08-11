from odoo import api, fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    stock_move_ids = fields.Many2many(
        comodel_name="stock.move",
        relation="account_analytic_account_stock_move_rel",
        column1="analytic_account_id",
        column2="move_id",
        string="Stock Moves",
    )
    picking_ids = fields.Many2many(
        comodel_name="stock.picking",
        compute="_compute_picking_ids",
        store=True,
        compute_sudo=True,
    )
    picking_ids_count = fields.Integer(
        compute="_compute_picking_ids_count",
    )

    @api.depends("stock_move_ids")
    def _compute_picking_ids(self):
        for analytic_account in self:
            if analytic_account.stock_move_ids:
                pickings = analytic_account.stock_move_ids.mapped("picking_id")
                analytic_account.picking_ids = pickings
            else:
                analytic_account.picking_ids = False

    @api.depends("picking_ids")
    def _compute_picking_ids_count(self):
        for analytic_account in self:
            if analytic_account.picking_ids:
                analytic_account.picking_ids_count = len(analytic_account.picking_ids)
            else:
                analytic_account.picking_ids_count = 0

    def _compute_attachment_ids(self):
        res = super()._compute_attachment_ids()
        for analytic_account in self:
            attachment_ids_count = analytic_account.attachment_ids_count
            if analytic_account.picking_ids:
                stock_attachments = self.env["ir.attachment"].search(
                    [
                        ("res_model", "=", "stock.picking"),
                        ("res_id", "in", analytic_account.picking_ids.ids),
                    ]
                )
                attachment_ids_count += len(stock_attachments)
            analytic_account.attachment_ids_count = attachment_ids_count
        return res

    def action_open_stock_pickings(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock.action_picking_tree_all"
        )
        action.update({"domain": [("id", "in", self.picking_ids.ids)], "context": {}})
        return action
