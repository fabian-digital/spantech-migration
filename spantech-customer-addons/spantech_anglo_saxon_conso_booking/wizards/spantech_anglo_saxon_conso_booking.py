# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class SpantechAngloSaxonConsoBooking(models.TransientModel):
    _name = "spantech.anglo.saxon.conso.booking"

    date_range_id = fields.Many2one(
        comodel_name="date.range",
        string="Date range",
        check_company=True,
        required=True,
    )
    date_start = fields.Date(string="Start Date", required=True)
    date_end = fields.Date(string="End Date", required=True)
    note = fields.Text(string="Notes", readonly=True, default="")
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )

    @api.onchange("date_range_id")
    def _onchange_date_range_id(self):
        self.note = ""
        if self.date_range_id:
            self.date_start = self.date_range_id.date_start
            self.date_end = self.date_range_id.date_end
            dom = self._get_itr_account_domain()
            unposted = self.env["account.move.line"].search_count(
                dom + [("move_id.state", "=", "draft")]
            )
            if unposted:
                self.note += (
                    _("Unposted entries on account '%s' found")
                    % self.company_id.itr_account_id.code
                )
            if self.env.context.get("spantech_ico_pl"):
                unreconciled = self.env["account.move.line"].search_count(
                    dom + [("reconciled", "=", False)]
                )
                if unreconciled:
                    self.note += (
                        _("Unreconciled entries on account '%s' found")
                        % self.company_id.itr_account_id.code
                    )

    def create_move(self):
        if self.env.context.get("spantech_ico_pl"):
            conso_type = "pl"
        else:
            conso_type = "bs"
        return self._create_move(conso_type=conso_type)

    def _create_move(self, conso_type=None):
        euro = self.env["res.currency"].search([("name", "=", "EUR")])
        dom = self._get_itr_account_domain(conso_type=conso_type)
        dom += [("move_id.state", "=", "posted")]
        if conso_type == "pl":
            dom += [
                ("reconciled", "=", True),
                ("ico_conso_pl_move_id", "=", False),
            ]
            conso_type_str = "P&L"
        else:
            dom += [
                ("reconciled", "=", False),
                ("ico_conso_bs_move_id", "=", False),
            ]
            conso_type_str = "BS"
        # TODO:
        # Replace aml search by read_group or SQL if amls volume
        # becomes a performance bottleheck.
        amls = self.env["account.move.line"].search(dom)
        if not amls:
            raise UserError(_("No data found for the selected period."))
        ico_partners = amls.mapped("partner_id").filtered(
            lambda r: r.is_interco_partner
        )
        ico_amt = 0.0
        aml_vals = []
        for ico_partner in ico_partners:
            ico_amls = amls.filtered(lambda r, ico_p=ico_partner: r.partner_id == ico_p)
            if conso_type == "pl":
                ico_account = self.company_id.fg_var_ico_account_id
                ico_partner_amt = sum(ico_amls.mapped("debit"))
                ico_amt += ico_partner_amt
                debit = ico_partner_amt
                credit = 0.0
            else:
                ico_account = self.company_id.itr_ico_account_id
                ico_partner_amt = sum(ico_amls.mapped("credit"))
                ico_amt += ico_partner_amt
                debit = 0.0
                credit = ico_partner_amt
            amt_eur = self.company_id.currency_id._convert(
                debit - credit, euro, self.company_id, self.date_range_id.date_end
            )
            aml_vals.append(
                {
                    "name": f"ITR {conso_type_str} Consolidation ICO balance for "
                    f"{self.date_range_id.name}",
                    "account_id": ico_account.id,
                    "partner_id": ico_partner.id,
                    "debit": debit,
                    "credit": credit,
                    "currency_id": euro.id,
                    "amount_currency": amt_eur,
                }
            )
        if conso_type == "pl":
            debit = 0.0
            credit = ico_amt
            account = self.company_id.fg_var_account_id
        else:
            debit = ico_amt
            credit = 0.0
            account = self.company_id.itr_account_id
        amt_eur = self.company_id.currency_id._convert(
            debit - credit, euro, self.company_id, self.date_range_id.date_end
        )
        aml_vals.append(
            {
                "name": _(
                    "ITR {conso_type} Consolidation non-ICO balance for {period}"
                ).format(conso_type=conso_type_str, period=self.date_range_id.name),
                "account_id": account.id,
                "debit": debit,
                "credit": credit,
                "currency_id": euro.id,
                "amount_currency": amt_eur,
            }
        )
        am_vals = {
            "date": self.date_range_id.date_end,
            "move_type": "entry",
            "ref": _("ITR {conso_type} Consolidation entry for {period}").format(
                conso_type=conso_type_str, period=self.date_range_id.name
            ),
            "journal_id": self.company_id.conso_booking_journal_id.id,
            "company_id": self.company_id.id,
            "line_ids": [(0, 0, x) for x in aml_vals],
        }

        conso_move = self.env["account.move"].create(am_vals)
        if conso_type == "pl":
            amls.write({"ico_conso_pl_move_id": conso_move.id})
        else:
            amls.write({"ico_conso_bs_move_id": conso_move.id})
        self.note = _(
            "The ITR {conso_type} Consolidation entry has been created."
        ).format(conso_type=conso_type_str)
        ctx = dict(self.env.context, conso_move_id=conso_move.id)
        module = __name__.split("addons.")[1].split(".")[0]
        result_view = self.env.ref(
            "%s.spantech_anglo_saxon_conso_booking_view_form_result" % module
        )
        name = _("ICO {conso_type} Consolidation entry").format(
            conso_type=conso_type_str
        )
        return {
            "name": name,
            "res_id": self.id,
            "view_type": "form",
            "view_mode": "form",
            "res_model": "spantech.anglo.saxon.conso.booking",
            "view_id": result_view.id,
            "context": ctx,
            "target": "new",
            "type": "ir.actions.act_window",
        }

    def view_move(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "account.action_move_journal_line"
        )
        domain = safe_eval(action.get("domain") or "[]")
        domain += [("id", "=", self.env.context.get("conso_move_id"))]
        action.update({"domain": domain})
        return action

    def _get_itr_account_domain(self, conso_type=None):
        itr_account_id = self.company_id.itr_account_id
        dom = [
            ("account_id", "=", itr_account_id.id),
            ("date", ">=", self.date_start),
            ("date", "<=", self.date_end),
            ("move_id.state", "=", "posted"),
            ("company_id", "=", self.company_id.id),
        ]
        if conso_type == "pl":
            dom.append(("debit", ">", 0.0))
        else:
            dom.append(("credit", ">", 0.0))
        return dom
