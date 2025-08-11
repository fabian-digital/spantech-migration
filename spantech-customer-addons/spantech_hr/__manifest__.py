# Copyright 2009-2025 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Spantech HR",
    "version": "16.0.1.1.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Spantech",
    "depends": [
        "spantech_base",
        "spantech_account",
        "hr_expense",
        # "account_bank_statement_import_csv",
        "account_statement_import_txt_xlsx",
        "account_bank_statement_advanced",
        "nthub_binary_field_preview",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/account_account_datas.xml",
        "data/account_journal_datas.xml",
        "views/account_bank_statement_views.xml",
        "views/account_journal_views.xml",
        "views/attachment_views.xml",
        "views/hr_employee_views.xml",
        "views/hr_expense_views.xml",
        "views/product_template_views.xml",
        "views/res_config_settings_views.xml",
        "wizards/hr_expense_update_wizard_views.xml",
    ],
    "pre_init_hook": "_pre_init_hook",
    "post_init_hook": "_post_init_hook",
    "installable": True,
}
