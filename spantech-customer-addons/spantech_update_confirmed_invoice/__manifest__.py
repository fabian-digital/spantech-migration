# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Update confirmed invoice",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Spantech",
    "depends": ["account", "spantech_base", "spantech_analytic"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
        "wizards/account_invoice_line_update.xml",
    ],
    "installable": True,
}
