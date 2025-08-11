# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Spantech Stock Valuation Report",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "category": "Spantech",
    "summary": "Spantech Stock Valuation Report",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "depends": ["spantech_base", "spantech_stock", "stock_account_valuation_report"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/spantech_stock_fifo_valuation_report_wizard.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
