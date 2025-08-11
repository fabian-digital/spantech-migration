# -*- coding: utf-8 -*-
{
    'name': "Attachment Preview",
    'version': '16.0.1.0.0',
    'summary': """
        Document Attachment Preview,
        Image Preview,
        Image Viewer,
        PDF Viewer,
        PDF Preview,
        Attachment Viewer,
        HR Document Viewer,
        HR Document Preview,
        Expense Document Preview,
        Expense Document Viewer,
        Document Attachment Viewer,
        Document Attachment Preview,
        Widget preview,
    """,
    'description': """The Attachment Preview module is a simple but powerful tool that can save you a lot of time and storage space.
        It's easy to use and works with all types of documents, including PDFs,text and images by using widget="nt_binary_preview" 
        on binary field in both tree or form views.""",
    'category': 'Tools',
    'author': 'Neoteric Hub',
    'company': 'Neoteric Hub',
    'live_test_url': '',
    'price': 9,
    'currency': 'USD',
    'website': 'https://www.neoterichub.com',
    'depends': ['base', 'web', 'mail'],
    'data': [
    ],
    'assets': {
        'web.assets_backend': [
            'nthub_binary_field_preview/static/src/js/viewer.js',
            'nthub_binary_field_preview/static/src/js/viewer.css',
            'nthub_binary_field_preview/static/src/js/nthub_binary_preview_viewerjs.js',
            'nthub_binary_field_preview/static/src/xml/nthub_binary_preview.xml',
        ],
    },
    'images': ['static/description/banner.gif'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
