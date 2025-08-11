# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Spantech Intercompany",
    "version": "16.0.0.1.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Spantech",
    "depends": [
        "spantech_account",
        "spantech_purchase",
        "spantech_sale",
        "spantech_analytic",
        "account_inter_company_rules",
        "sale_purchase_inter_company_rules",
        "sale_order_line_date",
    ],
    "data": [
        "data/mail_template.xml",
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
        "views/product_template_views.xml",
        "views/purchase_order_views.xml",
        "views/res_config_settings_views.xml",
        "views/res_partner_views.xml",
        "views/sale_order_views.xml",
        "report/purchase_intercomapny_report_views.xml",
        "views/report_invoice.xml",
        "views/report_saleorder.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "spantech_intercompany/static/src/components/**/*",
        ],
    },
    "installable": True,
}
