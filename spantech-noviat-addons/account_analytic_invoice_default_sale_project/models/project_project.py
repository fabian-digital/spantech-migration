# Copyright 2009-2023 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, models


class Project(models.Model):
    _inherit = "project.project"

    # This method is a copy/passed from the module sale_project.
    # The issue is: "psycopg2.errors.AmbiguousColumn: column reference
    # "analytic_distribution" is ambiguous" because 'analytic_distribution' is defined
    # in the account.move.line and the account.move models. This overryde simply add
    # 'account_move_line.' before the name field 'analytic_distribution'
    # Todo: always check if this module is still necessary
    def _compute_invoice_count(self):
        query = self.env["account.move.line"]._search(
            [("move_id.move_type", "in", ["out_invoice", "out_refund"])]
        )
        # line that cause the issue:
        # query.add_where('analytic_distribution ?| %s',
        # [[str(project.analytic_account_id.id) for project in self]])
        # line that sole the issue:
        query.add_where(
            "account_move_line.analytic_distribution ?| %s",
            [[str(project.analytic_account_id.id) for project in self]],
        )
        query.order = None
        query_string, query_param = query.select(
            "jsonb_object_keys(account_move_line.analytic_distribution) as account_id",
            "COUNT(DISTINCT move_id) as move_count",
        )
        query_string = (
            f"{query_string} "
            f"GROUP BY jsonb_object_keys(account_move_line.analytic_distribution)"
        )
        self._cr.execute(query_string, query_param)
        data = {
            int(row.get("account_id")): row.get("move_count")
            for row in self._cr.dictfetchall()
        }
        for project in self:
            project.invoice_count = data.get(project.analytic_account_id.id, 0)

    # Same issue that above
    def action_open_project_vendor_bills(self):
        query = self.env["account.move.line"]._search(
            [("move_id.move_type", "in", ["in_invoice", "in_refund"])]
        )
        # line that cause the issue:
        # query.add_where('analytic_distribution ? %s', [str(self.analytic_account_id.id)])
        # line that sole the issue:
        query.add_where(
            "account_move_line.analytic_distribution ? %s",
            [str(self.analytic_account_id.id)],
        )
        query.order = None
        query_string, query_param = query.select("DISTINCT move_id")
        self._cr.execute(query_string, query_param)
        result = self._cr.dictfetchall()
        vendor_bill_ids = [line.get("move_id") for line in result]
        action_window = {
            "name": _("Vendor Bills"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "views": [[False, "tree"], [False, "form"], [False, "kanban"]],
            "domain": [("id", "in", vendor_bill_ids)],
            "context": {
                "create": False,
            },
        }
        if len(vendor_bill_ids) == 1:
            action_window["views"] = [[False, "form"]]
            action_window["res_id"] = vendor_bill_ids[0]
        return action_window

    # Same issue that above
    def action_open_project_invoices(self):
        query = self.env["account.move.line"]._search(
            [("move_id.move_type", "in", ["out_invoice", "out_refund"])]
        )
        # line that cause the issue:
        # query.add_where('analytic_distribution ? %s', [str(self.analytic_account_id.id)])
        query.add_where(
            "account_move_line.analytic_distribution ? %s",
            [str(self.analytic_account_id.id)],
        )
        # line that sole the issue:
        query.order = None
        query_string, query_param = query.select("DISTINCT move_id")
        self._cr.execute(query_string, query_param)
        invoice_ids = [line.get("move_id") for line in self._cr.dictfetchall()]
        action = {
            "name": _("Invoices"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "views": [[False, "tree"], [False, "form"], [False, "kanban"]],
            "domain": [("id", "in", invoice_ids)],
            "context": {
                "create": False,
            },
        }
        if len(invoice_ids) == 1:
            action["views"] = [[False, "form"]]
            action["res_id"] = invoice_ids[0]
        return action
