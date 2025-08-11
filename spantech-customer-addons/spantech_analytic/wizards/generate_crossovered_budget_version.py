# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class GenerateCrossoveredBudgetVersionWiz(models.TransientModel):
    _name = "generate.crossovered.budget.version.wiz"

    crossovered_budget_id = fields.Many2one(
        comodel_name="crossovered.budget",
        string="Budget",
    )
    version = fields.Char(required=True)

    def action_generate_crossovered_budget_version(self):
        if not self.crossovered_budget_id or not self.version:
            return
        version = self.env["crossovered.budget.version"].create(
            self.get_budget_values()
        )
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "spantech_analytic.crossovered_budget_version_action"
        )
        action.update(
            {
                "views": [(False, "form")],
                "res_id": version.id,
            }
        )
        return action

    def get_budget_values(self):
        values = {"version": self.version}
        domain = [
            ("model", "=", self.crossovered_budget_id._name),
            ("name", "not in", tuple(self.budget_fields_to_ignore())),
            ("ttype", "not in", tuple(self.fields_type_ignore())),
        ]
        fields = self.env["ir.model.fields"].sudo().search(domain)
        for field in fields:
            if field.ttype == "many2one":
                values[field.name] = self.crossovered_budget_id[field.name].id
            else:
                values[field.name] = self.crossovered_budget_id[field.name]
        values["crossovered_budget_line"] = self.get_budget_line_values()
        return values

    def get_budget_line_values(self):
        values_list = []
        domain = [
            ("model", "=", self.crossovered_budget_id.crossovered_budget_line._name),
            ("name", "not in", tuple(self.budget_line_fields_to_ignore())),
            ("ttype", "not in", tuple(self.fields_type_ignore())),
        ]
        fields = self.env["ir.model.fields"].sudo().search(domain)
        for line in self.crossovered_budget_id.crossovered_budget_line:
            values = {}
            for field in fields:
                if field.ttype == "many2one":
                    values[field.name] = line[field.name].id
                else:
                    values[field.name] = line[field.name]
            values_list.append((0, 0, values))
        return values_list

    @api.model
    def budget_fields_to_ignore(self):
        specials = {
            "__last_update",
            "display_name",
        }
        return set(models.MAGIC_COLUMNS) | specials

    @api.model
    def budget_line_fields_to_ignore(self):
        specials = {
            "__last_update",
            "display_name",
            "crossovered_budget_id",
        }
        return set(models.MAGIC_COLUMNS) | specials

    @api.model
    def fields_type_ignore(self):
        return [
            "one2many",
            "many2many",
            "properties",
        ]
