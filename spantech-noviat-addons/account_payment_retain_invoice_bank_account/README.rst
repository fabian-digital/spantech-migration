.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=========================================
Retain Parner Bank Account of the invoice
=========================================

Odoo allows to select a bank account on a Vendor Bill for payment purposes.
But this bank account can be replaced by the default one if the
account_payment,_compute_partner_bank_id is triggered.

E.g. a custom module that sets a default journal on a partner record will change
the default journal_id and hence trigger the compute method.

In this module we adapt this method to retain the bank account set by the user/
