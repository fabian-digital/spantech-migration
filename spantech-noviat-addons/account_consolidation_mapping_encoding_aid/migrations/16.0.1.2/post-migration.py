# Copyright 2025 Noviat.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    accounts = env["account.account"].search(
        [("consolidation_account_id", "!=", False)]
    )
    for account in accounts:
        env.cr.execute(
            f"""
           UPDATE account_move_line
           SET consolidation_account_id = {account.consolidation_account_id.id}
           WHERE consolidation_account_id IS NULL AND account_id = {account.id}
           """
        )
