# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models

POC_BUDGET_LINE_KEYS = ["2. COGS", "3. ITL"]


class AccountBudgetPost(models.Model):
    _inherit = "account.budget.post"

    budget_grouping_key = fields.Char(string="Grouping Key")
    order_type = fields.Many2one(
        comodel_name="purchase.order.type",
        readonly=False,
        string="Purchase Type",
        domain="[('company_id', 'in', [False, company_id])]",
    )


class CrossoveredBudget(models.Model):
    _inherit = "crossovered.budget"

    name = fields.Char("Project Code", help="Unique identifier for the project")

    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
    )
    date_from = fields.Date(
        tracking=True, help="Date when the contract is signed with the client"
    )
    date_to = fields.Date(
        tracking=True,
        help="The date when the project handover is completed, and all payments "
        "have been made",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency", related="company_id.currency_id", readonly=True
    )
    initial_amount_total = fields.Monetary(
        string="Initial Budget Total",
        compute="_compute_total_amount",
        store=True,
        tracking=True,
    )
    planned_amount_total = fields.Monetary(
        string="Last Estimate Total",
        compute="_compute_total_amount",
        store=True,
        tracking=True,
    )
    to_engage_amount_total = fields.Monetary(
        string="Forecast Total",
        compute="_compute_total_amount",
        store=True,
        tracking=True,
    )
    engaged_amount_total = fields.Monetary(
        string="PO Total",
        compute="_compute_total_amount",
        store=True,
        tracking=True,
    )
    crossovered_budget_line_grouped_ids = fields.One2many(
        comodel_name="crossovered.budget.lines.grouped",
        inverse_name="crossovered_budget_id",
        string="Budget Lines Grouped",
        compute="_compute_crossovered_budget_line_grouped_ids",
    )
    purchase_order_line_ids = fields.Many2many(
        comodel_name="purchase.order.line",
        compute="_compute_purchase_order_line_ids",
        compute_sudo=True,
        store=True,
    )
    initial_date = fields.Date()
    margin_initial_amount = fields.Float(
        compute="_compute_margin_initial_amount", store=True, string="Margin (IB)"
    )
    margin_percentage_initial_amount = fields.Float(
        compute="_compute_margin_initial_amount",
        store=True,
        string="Bud. Marg.",
        help="Margin initially calculated in the budget (expressed in %)",
    )
    margin_planned_amount = fields.Float(
        compute="_compute_margin_planned_amount", store=True, string="Margin (LE)"
    )
    margin_percentage_planned_amount = fields.Float(
        compute="_compute_margin_planned_amount",
        store=True,
        string="LE Marg.",
        help="Last Estimate margin (expressed in %)",
    )

    poc = fields.Float(
        string="POC",
        compute="_compute_poc",
        help="POC: Percentage Of Completion, expressed as a percentage, "
        "reflecting the project's progress. "
        "It is calculated by dividing the total actual costs recorded "
        "in accounting by the total Last Estimate costs",
    )
    poc_le = fields.Float(
        compute="_compute_poc",
    )
    poc_actual = fields.Float(compute="_compute_poc")

    budget_version_ids = fields.One2many(
        comodel_name="crossovered.budget.version",
        inverse_name="crossovered_budget_id",
    )
    budget_version_count = fields.Integer(compute="_compute_budget_version_count")

    @api.depends(
        "crossovered_budget_line.initial_amount",
        "crossovered_budget_line.planned_amount",
        "crossovered_budget_line.to_engage_amount",
        "crossovered_budget_line.engaged_amount",
    )
    def _compute_total_amount(self):
        for budget in self:
            budget.initial_amount_total = sum(
                budget_line.initial_amount
                for budget_line in budget.crossovered_budget_line
            )
            budget.planned_amount_total = sum(
                budget_line.planned_amount
                for budget_line in budget.crossovered_budget_line
            )
            budget.to_engage_amount_total = sum(
                budget_line.to_engage_amount
                for budget_line in budget.crossovered_budget_line
            )
            budget.engaged_amount_total = sum(
                budget_line.engaged_amount
                for budget_line in budget.crossovered_budget_line
            )

    @api.depends("crossovered_budget_line")
    def _compute_crossovered_budget_line_grouped_ids(self):
        for budget in self:
            grouping_keys = sorted(
                set(budget.crossovered_budget_line.mapped("budget_grouping_key")),
                key=lambda gk: gk if gk else "Z",
            )
            budget_lines_grouped = self.env[
                budget.crossovered_budget_line_grouped_ids._name
            ]
            for grouping_key in grouping_keys:
                planned_amount = 0.0
                initial_amount = 0.0
                practical_amount = 0.0
                theoritical_amount = 0.0
                to_engage_amount = 0.0
                engaged_amount = 0.0
                for budget_line in budget.crossovered_budget_line.filtered(
                    lambda cbl, gk=grouping_key: cbl.budget_grouping_key == gk
                ):
                    planned_amount += budget_line.planned_amount
                    initial_amount += budget_line.initial_amount
                    practical_amount += budget_line.practical_amount
                    theoritical_amount += budget_line.theoritical_amount
                    to_engage_amount += budget_line.to_engage_amount
                    engaged_amount += budget_line.engaged_amount
                budget_lines_grouped |= self.env[
                    budget.crossovered_budget_line_grouped_ids._name
                ].create(
                    {
                        "planned_amount": planned_amount,
                        "initial_amount": initial_amount,
                        "practical_amount": practical_amount,
                        "theoritical_amount": theoritical_amount,
                        "to_engage_amount": to_engage_amount,
                        "engaged_amount": engaged_amount,
                        "budget_grouping_key": grouping_key,
                        "crossovered_budget_id": budget.id,
                    }
                )
            budget.crossovered_budget_line_grouped_ids = budget_lines_grouped

    @api.depends("analytic_account_id", "analytic_account_id.purchase_order_line_ids")
    def _compute_purchase_order_line_ids(self):
        for budget in self:
            if budget.analytic_account_id:
                budget.purchase_order_line_ids = (
                    budget.analytic_account_id.purchase_order_line_ids.filtered(
                        lambda pol, b=budget: not pol.company_id
                        or pol.company_id == b.company_id
                    )
                )
            else:
                budget.purchase_order_line_ids = False

    @api.depends("crossovered_budget_line.initial_amount")
    def _compute_margin_initial_amount(self):
        for budget in self:
            if budget.crossovered_budget_line:
                margin = sum(
                    line.initial_amount for line in budget.crossovered_budget_line
                )
                revenue = sum(
                    line.initial_amount
                    for line in budget.crossovered_budget_line.filtered(
                        lambda cbl: cbl.initial_amount > 0.0
                    )
                )
                if revenue != 0:
                    budget.margin_initial_amount = margin
                    budget.margin_percentage_initial_amount = (margin / revenue) * 100
                else:
                    budget.margin_initial_amount = margin
                    budget.margin_percentage_initial_amount = 0.0
            else:
                budget.margin_initial_amount = 0.0
                budget.margin_percentage_initial_amount = 0.0

    @api.depends("crossovered_budget_line.planned_amount")
    def _compute_margin_planned_amount(self):
        for budget in self:
            if budget.crossovered_budget_line:
                margin = sum(
                    line.planned_amount for line in budget.crossovered_budget_line
                )
                revenue = sum(
                    line.planned_amount
                    for line in budget.crossovered_budget_line.filtered(
                        lambda cbl: cbl.planned_amount > 0.0
                    )
                )
                if revenue != 0:
                    budget.margin_planned_amount = margin
                    budget.margin_percentage_planned_amount = (margin / revenue) * 100
                else:
                    budget.margin_planned_amount = margin
                    budget.margin_percentage_planned_amount = 0.0
            else:
                budget.margin_planned_amount = 0.0
                budget.margin_percentage_planned_amount = 0.0

    def _compute_budget_version_count(self):
        for budget in self:
            budget.budget_version_count = len(budget.budget_version_ids)

    def _compute_poc(self):
        for budget in self:
            sum_le = 0
            sum_actual = 0
            for blg in budget.crossovered_budget_line_grouped_ids:
                if blg.budget_grouping_key in POC_BUDGET_LINE_KEYS:
                    sum_le += blg.planned_amount
                    sum_actual += blg.practical_amount
            budget.poc_le = sum_le
            budget.poc_actual = sum_actual
            if sum_le:
                budget.poc = sum_actual / sum_le
            else:
                budget.poc = 0

    @api.onchange("analytic_account_id")
    def _onchange_analytic_account_id(self):
        self.crossovered_budget_line.analytic_account_id = self.analytic_account_id

    def action_open_budgets_analysis(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "account_budget.act_crossovered_budget_lines_view"
        )
        action.update(
            {
                "domain": [("id", "in", self.crossovered_budget_line.ids)],
                "context": {},
            }
        )
        return action

    def action_open_purchase_orders(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "purchase.purchase_form_action"
        )
        action.update(
            {
                "domain": [
                    ("analytic_account_ids", "in", self.analytic_account_id.ids)
                ],
                "context": {
                    "search_default_confirmed": True,
                    "search_default_order_type": True,
                },
            }
        )
        return action

    def action_open_analytic_lines(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "analytic.account_analytic_line_action"
        )
        action.update(
            {
                "domain": [("account_id", "=", self.analytic_account_id.id)],
            }
        )
        return action

    def action_open_account_move_lines(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "account_move_line_search_extension"
            + "."
            + "account_move_line_action_search_extension"
        )
        action.update(
            {
                "domain": [
                    ("analytic_account_ids", "in", self.analytic_account_id.ids)
                ],
            }
        )
        return action

    def action_open_crossovered_budget_versions(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "spantech_analytic.crossovered_budget_version_action"
        )
        action.update(
            {
                "domain": [("crossovered_budget_id", "=", self.id)],
            }
        )
        return action

    def action_recompute_values(self):
        self.ensure_one()
        self.crossovered_budget_line._compute_engaged_amount()

    def action_set_to_engage_to_zero(self):
        self.ensure_one()
        self.crossovered_budget_line.write({"to_engage_amount": 0})

    def action_generate_budget_version_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "generate.crossovered.budget.version.wiz",
            "view_mode": "form",
            "target": "new",
            "context": {"default_crossovered_budget_id": self.id},
        }


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"
    _order = "sequence, budget_grouping_key, id"

    sequence = fields.Integer()
    initial_amount = fields.Monetary(string="Budget")
    planned_amount = fields.Monetary(
        string="LE", compute="_compute_planned_amount", store=True
    )
    delta = fields.Monetary(compute="_compute_delta")
    delta_percentage = fields.Float(compute="_compute_delta", string="Delta %")
    practical_amount = fields.Monetary(string="Actuals")
    to_engage_amount = fields.Monetary(string="Forecast")
    engaged_amount = fields.Monetary(
        string="PO", compute="_compute_engaged_amount", store=True
    )
    budget_grouping_key = fields.Char(
        related="general_budget_id.budget_grouping_key", store=True
    )
    order_type = fields.Many2one(
        related="general_budget_id.order_type",
        store=True,
    )
    margin_percentage_initial_amount = fields.Float(
        related="crossovered_budget_id.margin_percentage_initial_amount",
        store=True,
        string="Margin % (IB)",
        group_operator="avg",
    )
    margin_percentage_planned_amount = fields.Float(
        related="crossovered_budget_id.margin_percentage_planned_amount",
        store=True,
        string="Margin % (LE)",
        group_operator="avg",
    )

    @api.depends("planned_amount", "initial_amount")
    def _compute_delta(self):
        for line in self:
            line.delta = line.planned_amount - line.initial_amount
            if line.initial_amount:
                line.delta_percentage = line.delta / line.initial_amount
            else:
                line.delta_percentage = 0.0

    @api.depends("date_from", "date_to")
    def _compute_theoritical_amount(self):
        today = fields.Date.today()
        for line in self:
            if line.paid_date:
                if today <= line.paid_date:
                    theo_amt = 0.00
                else:
                    theo_amt = line.planned_amount
            else:
                theo_amt = line.planned_amount - line.practical_amount
            line.theoritical_amount = theo_amt

    @api.depends(
        "order_type",
        "crossovered_budget_id.purchase_order_line_ids",
        "crossovered_budget_id.purchase_order_line_ids.price_unit",
        "crossovered_budget_id.purchase_order_line_ids.qty_invoiced",
        "crossovered_budget_id.purchase_order_line_ids.state",
        "crossovered_budget_id.purchase_order_line_ids.order_type",
    )
    def _compute_engaged_amount(self):
        for budget_line in self:
            if budget_line.order_type:
                budget_pol = (
                    budget_line.crossovered_budget_id.purchase_order_line_ids.filtered(
                        lambda pol, bl=budget_line: pol.order_type == bl.order_type
                        and pol.state not in ["draft", "cancel", "done"]
                    )
                )
                engaged_amount = 0.0
                for pol in budget_pol:
                    if pol.currency_id != budget_line.currency_id:
                        engaged_amount -= pol.currency_id._convert(
                            pol.price_uninvoiced,
                            budget_line.currency_id,
                            budget_line.company_id,
                            pol.date_order or fields.Date.today(),
                        )
                    else:
                        engaged_amount -= pol.price_uninvoiced
                budget_line.engaged_amount = engaged_amount
            else:
                budget_line.engaged_amount = 0.0

    @api.depends("practical_amount", "engaged_amount", "to_engage_amount")
    def _compute_planned_amount(self):
        for budget_line in self:
            budget_line.planned_amount = (
                budget_line.practical_amount
                + budget_line.engaged_amount
                + budget_line.to_engage_amount
            )


class CrossoveredBudgetLinesGrouped(models.TransientModel):
    _name = "crossovered.budget.lines.grouped"
    _description = "crossovered budget lines grouped"

    crossovered_budget_id = fields.Many2one(
        "crossovered.budget",
        "Budget",
    )
    budget_grouping_key = fields.Char(string="Grouping Keys")

    planned_amount = fields.Monetary(string="LE", compute="_compute_planned_amount")
    initial_amount = fields.Monetary(string="Budget")
    delta = fields.Monetary(compute="_compute_delta")
    delta_percentage = fields.Float(compute="_compute_delta", string="Delta %")
    practical_amount = fields.Monetary(
        string="Actuals",
    )
    theoritical_amount = fields.Monetary(
        string="Theoretical Amount",
    )
    to_engage_amount = fields.Monetary(string="Forecast")
    engaged_amount = fields.Monetary(string="PO")
    company_id = fields.Many2one(
        related="crossovered_budget_id.company_id",
        comodel_name="res.company",
        string="Company",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency", related="company_id.currency_id"
    )

    @api.depends("planned_amount", "initial_amount")
    def _compute_delta(self):
        for line in self:
            line.delta = line.planned_amount - line.initial_amount
            if line.initial_amount:
                line.delta_percentage = line.delta / line.initial_amount
            else:
                line.delta_percentage = 0.0

    @api.depends("practical_amount", "engaged_amount", "to_engage_amount")
    def _compute_planned_amount(self):
        for budget_line in self:
            budget_line.planned_amount = (
                budget_line.practical_amount
                + budget_line.engaged_amount
                + budget_line.to_engage_amount
            )
