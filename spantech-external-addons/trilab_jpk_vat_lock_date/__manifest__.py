# noinspection PyStatementEffect
{
    'name': 'Trilab JPK VAT Date Lock',
    'summary': '''
        Allow JPK VAT Date lock (similar to accounting dates)
        ''',
    'description': '',
    'author': 'Trilab',
    'website': 'https://trilab.pl',
    'category': 'Accounting',
    'version': '16.0.0.1.0',
    'depends': ['account_accountant', 'trilab_jpk_vat'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/jpk_vat_date_exception.xml',
        'views/account_change_lock_date.xml',
    ],
    'images': [],
    'assets': {},
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'OPL-1',
    'price': 0.0,
    'currency': 'EUR',
}
