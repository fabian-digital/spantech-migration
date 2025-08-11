# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Spantech MRP",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Spantech",
    "external_dependencies": {"python": ["pdf2image"]},
    "depends": [
        "spantech_base",
        "spantech_analytic",
        "mrp",
        "report_xlsx",
        "web_editor",
        "account_move_line_mrp_info",
        "stock_backdating_mrp",
    ],
    "data": [
        "data/paperformat_data.xml",
        "security/ir.model.access.csv",
        "report/report_bom_structure.xml",
        "report/mrp_production_templates.xml",
        "report/mrp_production_handwritten.xml",
        "report/pvc_mo_production_time_report.xml",
        "views/mrp_bom_views.xml",
        "views/mrp_production_views.xml",
        "views/product_template_views.xml",
        "wizards/product_replenish_views.xml",
        "wizards/cancel_reason_wizard_views.xml",
    ],
    "installable": True,
}
