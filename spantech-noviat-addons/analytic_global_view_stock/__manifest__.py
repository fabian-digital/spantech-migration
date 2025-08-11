# Copyright 2009-2023 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Analytic Global View - Stock",
    "version": "16.0.1.1.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Analytic",
    "depends": ["analytic_global_view", "stock", "stock_analytic"],
    "data": [
        "views/account_analytic_account_views.xml",
        "views/stock_move_views.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
