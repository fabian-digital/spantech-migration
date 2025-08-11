# noinspection PyStatementEffect
{
    'name': 'Trilab Invoice PL',
    'author': 'Trilab',
    'website': 'https://trilab.pl',
    'version': '16.0.88.1.0',
    'category': 'Accounting',
    'summary': 'Base module to manage invoice in PL',
    'description': """Base module to manage invoices and invoice correction
    according to Polish law and best practices""",
    'depends': ['account', 'sale', 'sale_management', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/account_move_reversal.xml',
        'wizard/sale_advance_payment_inv.xml',
        'views/account_move.xml',
        'views/report_invoice.xml',
        'views/sale_views.xml',
        'views/res_config_settings.xml',
    ],
    'images': ['static/description/banner.png', 'static/description/invoice.png'],
    'assets': {'web.report_assets_common': ['trilab_invoice/static/src/scss/layout_boxed.scss']},
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
    'price': 140.0,
    'currency': 'EUR',
}
