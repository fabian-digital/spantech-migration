# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Manufacturing Timesheets/ MRP Timesheets',
    'version': '16.0.0.0.0',
    'category': 'Manufacturing',
    'summary': 'MRP Timesheet on Manufacturing Timesheet manufacturing order timesheet MRP order timesheet workorder timesheet mrp workorder timesheet workorder timesheets Manufacturing worksheet mrp worksheet enter timesheet on Manufacturing timesheet on workorders',
    'description': """
        
        Manage Timesheet on Manufacturing Order in odoo,
        Manage Timesheet on Work Order in odoo,
        Manage Timesheet on MRP in odoo,
        MRP Timesheet on List View in odoo,
        MRP Timesheet on Kanban View in odoo,
        Manage Timesheet in odoo,
    
    """,
    'author': 'BrowseInfo',
    'website': 'https://www.browseinfo.com',
    "price": 20,
    "currency": 'EUR',
    'depends': ['stock', 'hr_timesheet', 'project', 'mrp'],
    'data': [
        'views/account_analytic_line.xml',
        'views/mrp_view.xml',
        'views/mrp_workorder_view.xml',
    ],
    'demo': [],
    'test': [],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    "live_test_url":'https://youtu.be/PmhrNB4BM6o',
    "images":["static/description/Banner.gif"],
}
