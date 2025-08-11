# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def _pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    existing_expense_journal = env["account.journal"].search(
        [("name", "=", "Expense Notes Journal SPI")], limit=1
    )
    if not existing_expense_journal:
        existing_expense_journal = env["account.journal"].search(
            [("id", "=", 118)], limit=1
        )
    if existing_expense_journal:
        env["ir.model.data"].create(
            {
                "name": "account_journal_expense_notes",
                "res_id": existing_expense_journal.id,
                "module": "spantech_hr",
                "model": "account.journal",
                "noupdate": True,
            }
        )


def _post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if env.ref("spantech_hr.account_journal_expense_notes", raise_if_not_found=False):
        env.ref(
            "spantech_hr.account_journal_expense_notes", raise_if_not_found=False
        ).write({"is_spantech_expense": True})
