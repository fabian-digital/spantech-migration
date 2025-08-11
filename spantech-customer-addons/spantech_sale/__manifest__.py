# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Spantech Sale",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Spantech",
    "depends": [
        "attachment_zipped_download",
        "spantech_base",
        "spantech_partner",
        "spantech_account",
        "spantech_product",
        "spantech_analytic",
        "purchase_stock",
        "sale_management",
        "sale_stock",
        "sale_order_ratio",
        "sale_order_ratio_invoice_amount",
        "sale_force_invoiced",
        "sale_purchase_inter_company_rules",
        "sale_order_line_date",
        "web_domain_field",
    ],
    "installable": True,
    "data": [
        "views/res_company_views.xml",
        "views/purchase_order_views.xml",
        "views/sale_order_views.xml",
        "views/res_config_settings_views.xml",
        "wizards/sale_make_invoice_advance_views.xml",
        "views/report_saleorder.xml",
    ],
}
