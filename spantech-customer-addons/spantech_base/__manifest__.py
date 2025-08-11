# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)..

{
    "name": "Spantech Base",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Spantech",
    "depends": ["web", "mail", "auditlog", "res_company_code"],
    "installable": True,
    "data": [
        "security/auditlog_security.xml",
        "security/ir.model.access.csv",
        "data/decimal_precision_data.xml",
        "data/paperformat.xml",
        "views/audit_log_views.xml",
        "views/res_config_settings_views.xml",
        "views/res_users_views.xml",
        "report/external_layout_striped_template.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "/spantech_base/static/src/scss/font.scss",
        ],
    },
}
