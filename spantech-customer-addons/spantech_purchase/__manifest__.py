# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Spantech Purchase",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Spantech",
    "depends": [
        "spantech_base",
        "spantech_analytic",
        "purchase",
        "sale_purchase_inter_company_rules",
        "purchase_stock",
        "purchase_force_invoiced",
        "purchase_order_ratio",
        "purchase_order_ratio_invoice_amount",
        "purchase_tier_validation",
    ],
    "installable": True,
    "data": [
        "views/purchase_order_views.xml",
        "views/report_purchaseorder.xml",
        "views/account_analytic_views.xml",
        "wizards/change_state_warning_wizard_views.xml",
        "wizards/product_replenish_views.xml",
        "security/ir.model.access.csv",
    ],
}
