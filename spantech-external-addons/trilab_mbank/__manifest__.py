{
    'name': 'Trilab mBank CompanyConnect Integration (PL)',
    'summary': 'Integrate with mBank CompanyConnect',
    'description': 'Integrate with mBank CompanyConnect',
    'author': 'Trilab',
    'website': 'https://trilab.pl',
    'category': 'Accounting/Accounting',
    'version': '16.0.5.0.0',

    'depends': [
        'base_iban',
        'account_batch_payment',
    ],

    'data': [
        # security
        'security/ir.model.access.csv',

        # data
        'data/data.xml',
        'data/ir_cron.xml',

        # wizard
        'wizard/statement_import_wizard.xml',
        'wizard/get_session_token_wizard.xml',
        'wizard/copy_session_token_wizard.xml',

        # views
        'views/account_batch_payment.xml',
        'views/account_journal.xml',
    ],
    'images': [
        'static/description/banner.png'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'OPL-1',
    'price': 300.0,
    'currency': 'EUR'
}
