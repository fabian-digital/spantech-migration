# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Spantech Rental",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Spantech",
    "installable": True,
    "depends": [
        "spantech_base",
        "spantech_analytic",
        "spantech_stock",
        "sale_rental",
    ],
    "data": [
        "views/account_analytic_account_views.xml",
        "views/sale_order_views.xml",
        "views/sale_rental_views.xml",
        "views/sale_report_template.xml",
        "views/stock_move_views.xml",
        "views/stock_picking_views.xml",
        "wizards/stock_move_link_rental_wizard_views.xml",
        "security/ir.model.access.csv",
    ],
}
