# Copyright 2025 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CrossoveredBudgetVersion(models.Model):
    _name = "crossovered.budget.version"
    _inherit = "crossovered.budget"

    crossovered_budget_id = fields.Many2one(
        comodel_name="crossovered.budget",
        string="Budget",
    )
    crossovered_budget_line = fields.One2many(
        comodel_name="crossovered.budget.version.lines",
        inverse_name="crossovered_budget_id",
        string="Budget Lines",
        states={"done": [("readonly", True)]},
        copy=True,
    )
    crossovered_budget_line_grouped_ids = fields.One2many(
        comodel_name="crossovered.budget.version.lines.grouped",
        inverse_name="crossovered_budget_id",
        string="Budget Lines Grouped",
        compute="_compute_crossovered_budget_line_grouped_ids",
    )
    version = fields.Char()

    def _compute_purchase_order_line_ids(self):
        for budget in self:
            budget.purchase_order_line_ids = False


class CrossoveredBudgetVersionLines(models.Model):
    _name = "crossovered.budget.version.lines"
    _inherit = "crossovered.budget.lines"

    crossovered_budget_id = fields.Many2one(
        comodel_name="crossovered.budget.version",
        string="PBR Version",
        ondelete="cascade",
        index=True,
        required=True,
    )

    practical_amount = fields.Monetary(store=True)
    theoritical_amount = fields.Monetary(store=True)


class CrossoveredBudgetVersionLinesGrouped(models.TransientModel):
    _name = "crossovered.budget.version.lines.grouped"
    _inherit = "crossovered.budget.lines.grouped"

    crossovered_budget_id = fields.Many2one(
        comodel_name="crossovered.budget.version",
        string="PBR Version",
    )
