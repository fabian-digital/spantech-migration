[![Pre-commit Status](https://github.com/Noviat-Projects/Spantech-OCA-Addons/actions/workflows/pre-commit.yml/badge.svg?branch=16.0)](https://github.com/Noviat-Projects/Spantech-OCA-Addons/actions/workflows/pre-commit.yml?query=branch%3A16.0)
[![Build Status](https://github.com/Noviat-Projects/Spantech-OCA-Addons/actions/workflows/test.yml/badge.svg?branch=16.0)](https://github.com/Noviat-Projects/Spantech-OCA-Addons/actions/workflows/test.yml?query=branch%3A16.0)

<!-- /!\ do not modify above this line -->

# OCA addons for Spantech

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_asset_management](account_asset_management/) | 16.0.1.2.5 |  | Assets Management
[account_banking_pain_base](account_banking_pain_base/) | 16.0.1.2.1 |  | Base module for PAIN file generation
[account_banking_sepa_credit_transfer](account_banking_sepa_credit_transfer/) | 16.0.1.1.5 |  | Create SEPA XML files for Credit Transfers
[account_chart_update](account_chart_update/) | 16.0.2.0.5 |  | Wizard to update a company's account chart from a template
[account_financial_report](account_financial_report/) | 16.0.1.10.1 |  | OCA Financial Reports
[account_invoice_check_total](account_invoice_check_total/) | 16.0.1.0.0 |  | Check if the verification total is equal to the bill's total
[account_invoice_force_number](account_invoice_force_number/) | 16.0.1.0.1 |  | Allows to force invoice numbering on specific invoices
[account_invoice_margin](account_invoice_margin/) | 16.0.1.0.1 | [![sergio-teruel](https://github.com/sergio-teruel.png?size=30px)](https://github.com/sergio-teruel) | Show margin in invoices
[account_invoice_margin_sale](account_invoice_margin_sale/) | 16.0.1.0.3 | [![sergio-teruel](https://github.com/sergio-teruel.png?size=30px)](https://github.com/sergio-teruel) [![carlosdauden](https://github.com/carlosdauden.png?size=30px)](https://github.com/carlosdauden) | Set margin in invoices from sale orders
[account_invoice_start_end_dates](account_invoice_start_end_dates/) | 16.0.1.2.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Adds start/end dates on invoice/move lines
[account_journal_lock_date](account_journal_lock_date/) | 16.0.1.0.0 |  | Lock each journal independently
[account_move_exception](account_move_exception/) | 16.0.1.0.0 |  | Custom exceptions on account move
[account_move_line_mrp_info](account_move_line_mrp_info/) | 16.0.1.1.0 |  | Account Move Line Mrp Info
[account_move_line_product](account_move_line_product/) | 16.0.1.0.0 |  | Displays the product in the journal entries and items
[account_move_line_report_xls](account_move_line_report_xls/) | 16.0.1.0.0 |  | Journal Items Excel export
[account_move_line_stock_info](account_move_line_stock_info/) | 16.0.1.1.1 |  | Account Move Line Stock Info
[account_move_line_tax_editable](account_move_line_tax_editable/) | 16.0.1.0.1 |  | Allows to edit taxes on non-posted account move lines
[account_move_tier_validation](account_move_tier_validation/) | 16.0.1.0.1 |  | Extends the functionality of Account Moves to support a tier validation process.
[account_payment_mode](account_payment_mode/) | 16.0.1.2.2 |  | Account Payment Mode
[account_payment_order](account_payment_order/) | 16.0.1.12.3 |  | Account Payment Order
[account_payment_partner](account_payment_partner/) | 16.0.1.2.4 |  | Adds payment mode on partners and invoices
[account_spread_cost_revenue](account_spread_cost_revenue/) | 16.0.1.0.1 |  | Spread costs and revenues over a custom period
[account_statement_base](account_statement_base/) | 16.0.1.12.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Base module for Bank Statements
[account_statement_import_base](account_statement_import_base/) | 16.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Base module for Bank Statement Import
[account_statement_import_camt](account_statement_import_camt/) | 16.0.1.0.2 |  | CAMT Format Bank Statements Import
[account_statement_import_file](account_statement_import_file/) | 16.0.1.0.2 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Import Statement Files
[account_statement_import_txt_xlsx](account_statement_import_txt_xlsx/) | 16.0.1.0.0 | [![alexey-pelykh](https://github.com/alexey-pelykh.png?size=30px)](https://github.com/alexey-pelykh) | Import TXT/CSV or XLSX files as Bank Statements in Odoo
[account_usability](account_usability/) | 16.0.1.0.3 | [![legalsylvain](https://github.com/legalsylvain.png?size=30px)](https://github.com/legalsylvain) | Adds missing menu entries for Account module and adds the option to enable Saxon Accounting
[analytic_distribution_widget_remove_save](analytic_distribution_widget_remove_save/) | 16.0.1.0.1 |  | Remove save button on analytic distribution widget
[attachment_zipped_download](attachment_zipped_download/) | 16.0.2.0.3 |  | Attachment Zipped Download
[auditlog](auditlog/) | 16.0.2.2.1 |  | Audit Log
[auth_session_timeout](auth_session_timeout/) | 16.0.1.0.0 |  | This module disable all inactive sessions since a given delay
[base_exception](base_exception/) | 16.0.2.0.1 | [![hparfr](https://github.com/hparfr.png?size=30px)](https://github.com/hparfr) [![sebastienbeau](https://github.com/sebastienbeau.png?size=30px)](https://github.com/sebastienbeau) | This module provide an abstract model to manage customizable exceptions to be applied on different models (sale order, invoice, ...)
[base_import_match](base_import_match/) | 16.0.1.0.0 |  | Try to avoid duplicates before importing
[base_tier_validation](base_tier_validation/) | 16.0.2.2.2 | [![LoisRForgeFlow](https://github.com/LoisRForgeFlow.png?size=30px)](https://github.com/LoisRForgeFlow) | Implement a validation process based on tiers.
[base_tier_validation_formula](base_tier_validation_formula/) | 16.0.1.0.2 |  | Formulas for Base tier validation
[base_tier_validation_forward](base_tier_validation_forward/) | 16.0.1.1.3 | [![kittiu](https://github.com/kittiu.png?size=30px)](https://github.com/kittiu) | Forward option for base tiers
[base_tier_validation_report](base_tier_validation_report/) | 16.0.1.0.1 | [![kittiu](https://github.com/kittiu.png?size=30px)](https://github.com/kittiu) | Reports related to tier validation
[base_user_role](base_user_role/) | 16.0.1.4.1 | [![sebalix](https://github.com/sebalix.png?size=30px)](https://github.com/sebalix) [![jcdrubay](https://github.com/jcdrubay.png?size=30px)](https://github.com/jcdrubay) [![novawish](https://github.com/novawish.png?size=30px)](https://github.com/novawish) | User roles
[base_user_role_company](base_user_role_company/) | 16.0.1.2.0 |  | User roles by company
[base_view_inheritance_extension](base_view_inheritance_extension/) | 16.0.1.2.1 |  | Adds more operators for view inheritance
[contract](contract/) | 16.0.2.10.0 |  | Recurring - Contracts Management
[contract_invoice_start_end_dates](contract_invoice_start_end_dates/) | 16.0.1.0.0 | [![florian-dacosta](https://github.com/florian-dacosta.png?size=30px)](https://github.com/florian-dacosta) | Contract Invoice Start End Dates
[date_range](date_range/) | 16.0.1.0.9 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | Manage all kind of date range
[intrastat_base](intrastat_base/) | 16.0.1.1.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) [![luc-demeyer](https://github.com/luc-demeyer.png?size=30px)](https://github.com/luc-demeyer) | Base module for Intrastat reporting
[intrastat_product](intrastat_product/) | 16.0.2.1.0 |  | Base module for Intrastat Product
[intrastat_product_generic](intrastat_product_generic/) | 16.0.1.0.0 |  | Generic Intrastat Product Declaration
[intrastat_product_hscodes_import](intrastat_product_hscodes_import/) | 16.0.1.0.0 |  | Module used to import HS Codes for Intrastat Product
[l10n_be_intrastat_product](l10n_be_intrastat_product/) | 16.0.1.0.0 | [![luc-demeyer](https://github.com/luc-demeyer.png?size=30px)](https://github.com/luc-demeyer) [![jdidderen-noviat](https://github.com/jdidderen-noviat.png?size=30px)](https://github.com/jdidderen-noviat) | Intrastat Product Declaration for Belgium
[l10n_be_partner_kbo_bce](l10n_be_partner_kbo_bce/) | 16.0.1.0.1 |  | Belgium - KBO/BCE numbers
[l10n_fr_department](l10n_fr_department/) | 16.0.1.0.1 | [![legalsylvain](https://github.com/legalsylvain.png?size=30px)](https://github.com/legalsylvain) | Populate Database with French Departments (Départements)
[l10n_fr_intrastat_product](l10n_fr_intrastat_product/) | 16.0.2.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | EMEBI (ex-DEB) for France
[l10n_fr_intrastat_service](l10n_fr_intrastat_service/) | 16.0.1.5.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Module for Intrastat service reporting (DES) for France
[l10n_fr_state](l10n_fr_state/) | 16.0.1.0.0 | [![legalsylvain](https://github.com/legalsylvain.png?size=30px)](https://github.com/legalsylvain) | Populate Database with French States (Régions)
[mis_builder](mis_builder/) | 16.0.5.1.12 | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | Build 'Management Information System' Reports and Dashboards
[mrp_attachment_mgmt](mrp_attachment_mgmt/) | 16.0.1.0.0 | [![victoralmau](https://github.com/victoralmau.png?size=30px)](https://github.com/victoralmau) | Mrp Attachment Mgmt
[mrp_bom_current_stock](mrp_bom_current_stock/) | 16.0.1.0.0 |  | MRP BoM Current Stock
[mrp_bom_hierarchy](mrp_bom_hierarchy/) | 16.0.1.2.0 |  | Make it easy to navigate through BoM hierarchy.
[mrp_bom_location](mrp_bom_location/) | 16.0.1.1.1 |  | Adds location field to Bill of Materials and its components.
[mrp_bom_tracking](mrp_bom_tracking/) | 16.0.1.0.0 |  | Logs any change to a BoM in the chatter
[mrp_progress_button](mrp_progress_button/) | 16.0.1.0.0 |  | Add a button on MO to make the MO state 'In Progress'
[mrp_sale_info](mrp_sale_info/) | 16.0.1.1.0 |  | Adds sale information to Manufacturing models
[multi_step_wizard](multi_step_wizard/) | 16.0.1.0.0 |  | Multi-Steps Wizards
[partner_deduplicate_acl](partner_deduplicate_acl/) | 16.0.1.0.1 |  | Contact deduplication with fine-grained permission control
[partner_identification](partner_identification/) | 16.0.1.0.3 |  | Partner Identification Numbers
[procurement_purchase_no_grouping](procurement_purchase_no_grouping/) | 16.0.1.0.0 |  | Procurement Purchase No Grouping
[product_category_type](product_category_type/) | 16.0.1.0.0 | [![legalsylvain](https://github.com/legalsylvain.png?size=30px)](https://github.com/legalsylvain) | Add Type field on Product Categories to distinguish between parent and final categories
[product_harmonized_system](product_harmonized_system/) | 16.0.1.1.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) [![luc-demeyer](https://github.com/luc-demeyer.png?size=30px)](https://github.com/luc-demeyer) | Base module for Product Import/Export reports
[product_harmonized_system_delivery](product_harmonized_system_delivery/) | 16.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) [![luc-demeyer](https://github.com/luc-demeyer.png?size=30px)](https://github.com/luc-demeyer) | Hide native hs_code field provided by the delivery module
[product_harmonized_system_stock](product_harmonized_system_stock/) | 16.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) [![luc-demeyer](https://github.com/luc-demeyer.png?size=30px)](https://github.com/luc-demeyer) | Adds a menu entry for H.S. codes
[product_mrp_info](product_mrp_info/) | 16.0.1.0.0 | [![LoisRForgeFlow](https://github.com/LoisRForgeFlow.png?size=30px)](https://github.com/LoisRForgeFlow) | Adds smart button in product form view linking to manufacturing order list.
[product_tax_multicompany_default](product_tax_multicompany_default/) | 16.0.1.0.2 | [![Shide](https://github.com/Shide.png?size=30px)](https://github.com/Shide) | Product Tax Multi Company Default
[purchase_delivery_split_date](purchase_delivery_split_date/) | 16.0.1.0.4 |  | Allows Purchase Order you confirm to generate one Incoming Shipment for each expected date indicated in the Purchase Order Lines
[purchase_discount](purchase_discount/) | 16.0.2.0.0 |  | Purchase order lines with discounts
[purchase_exception](purchase_exception/) | 16.0.1.0.1 |  | Custom exceptions on purchase order
[purchase_force_invoiced](purchase_force_invoiced/) | 16.0.1.0.1 |  | Allows to force the billing status of the purchase order to "Invoiced"
[purchase_order_type](purchase_order_type/) | 16.0.1.0.2 |  | Purchase Order Type
[purchase_order_uninvoiced_amount](purchase_order_uninvoiced_amount/) | 16.0.1.0.1 |  | Purchase Order Univoiced Amount
[purchase_stock_analytic](purchase_stock_analytic/) | 16.0.1.0.1 |  | Copies the analytic distribution of the purchase order item to the stock move
[purchase_stock_picking_invoice_link](purchase_stock_picking_invoice_link/) | 16.0.1.0.0 |  | Adds link between purchases, pickings and invoices
[purchase_tier_validation](purchase_tier_validation/) | 16.0.1.1.0 |  | Extends the functionality of Purchase Orders to support a tier validation process.
[queue_job](queue_job/) | 16.0.2.6.8 | [![guewen](https://github.com/guewen.png?size=30px)](https://github.com/guewen) | Job Queue
[report_xlsx](report_xlsx/) | 16.0.2.0.2 |  | Base module to create xlsx report
[report_xlsx_helper](report_xlsx_helper/) | 16.0.1.0.0 |  | Report xlsx helpers
[res_company_code](res_company_code/) | 16.0.1.0.0 | [![legalsylvain](https://github.com/legalsylvain.png?size=30px)](https://github.com/legalsylvain) | Add 'code' field on company model
[res_company_search_view](res_company_search_view/) | 16.0.1.0.0 | [![legalsylvain](https://github.com/legalsylvain.png?size=30px)](https://github.com/legalsylvain) | Add a search view for company model
[sale_exception](sale_exception/) | 16.0.1.3.0 |  | Custom exceptions on sale order
[sale_force_invoiced](sale_force_invoiced/) | 16.0.2.1.1 |  | Allows to force the invoice status of the sales order to Invoiced
[sale_margin_sync](sale_margin_sync/) | 16.0.1.0.1 |  | Recompute sale margin when stock move cost price is changed
[sale_order_invoice_amount](sale_order_invoice_amount/) | 16.0.1.0.1 |  | Display the invoiced and uninvoiced total in the sale order
[sale_order_line_date](sale_order_line_date/) | 16.0.1.1.0 |  | Adds a commitment date to each sale order line.
[sale_order_qty_change_no_recompute](sale_order_qty_change_no_recompute/) | 16.0.1.0.1 | [![victoralmau](https://github.com/victoralmau.png?size=30px)](https://github.com/victoralmau) | Prevent recompute if only quantity has changed in sale order line
[sale_procurement_group_by_line](sale_procurement_group_by_line/) | 16.0.1.0.0 |  | Base module for multiple procurement group by Sale order
[sale_report_margin](sale_report_margin/) | 16.0.1.0.0 | [![sergio-teruel](https://github.com/sergio-teruel.png?size=30px)](https://github.com/sergio-teruel) | Sale Report Margin
[sale_start_end_dates](sale_start_end_dates/) | 16.0.1.0.1 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Adds start date and end date on sale order lines
[server_action_mass_edit](server_action_mass_edit/) | 16.0.2.0.3 |  | Mass Editing
[server_environment](server_environment/) | 16.0.1.0.5 |  | move some configurations out of the database
[server_environment_ir_config_parameter](server_environment_ir_config_parameter/) | 16.0.1.1.0 |  | Override System Parameters from server environment file
[shipment_advice](shipment_advice/) | 16.0.1.5.0 |  | Manage your (un)loading process through shipment advices.
[stock_account_valuation_report](stock_account_valuation_report/) | 16.0.1.0.0 |  | Improves logic of the Inventory Valuation Report
[stock_analytic](stock_analytic/) | 16.0.1.3.0 |  | Adds analytic distribution in stock move
[stock_dock](stock_dock/) | 16.0.1.0.1 |  | Manage the loading docks of your warehouse.
[stock_no_negative](stock_no_negative/) | 16.0.1.0.2 |  | Disallow negative stock levels by default
[stock_picking_analytic](stock_picking_analytic/) | 16.0.1.0.1 |  | Allows to define the analytic account on picking level
[stock_picking_back2draft](stock_picking_back2draft/) | 16.0.1.0.0 |  | Reopen cancelled pickings
[stock_picking_invoice_link](stock_picking_invoice_link/) | 16.0.1.1.2 |  | Adds link between pickings and invoices
[stock_picking_purchase_order_link](stock_picking_purchase_order_link/) | 16.0.1.0.1 |  | Link between picking and purchase order
[stock_picking_sale_order_link](stock_picking_sale_order_link/) | 16.0.1.0.0 |  | Link between picking and sale order
[stock_picking_show_backorder](stock_picking_show_backorder/) | 16.0.1.0.0 |  | Provides a new field on stock pickings, allowing to display the corresponding backorders.
[stock_picking_show_return](stock_picking_show_return/) | 16.0.1.0.1 |  | Show returns on stock pickings
[stock_quant_cost_info](stock_quant_cost_info/) | 16.0.1.0.0 |  | Shows the cost of the quants
[web_advanced_search](web_advanced_search/) | 16.0.1.0.5 | [![ivantodorovich](https://github.com/ivantodorovich.png?size=30px)](https://github.com/ivantodorovich) | Easier and more powerful searching tools
[web_company_color](web_company_color/) | 16.0.1.2.3 |  | Web Company Color
[web_dialog_size](web_dialog_size/) | 16.0.1.0.1 |  | A module that lets the user expand a dialog box to the full screen width.
[web_domain_field](web_domain_field/) | 16.0.1.0.1 |  | Use computed field as domain
[web_environment_ribbon](web_environment_ribbon/) | 16.0.1.0.0 |  | Web Environment Ribbon
[web_m2x_options](web_m2x_options/) | 16.0.1.1.3 |  | web_m2x_options
[web_tree_dynamic_colored_field](web_tree_dynamic_colored_field/) | 16.0.1.0.0 |  | Allows you to dynamically color fields on tree views
[web_widget_dropdown_dynamic](web_widget_dropdown_dynamic/) | 16.0.1.0.0 |  | This module adds support for dynamic dropdown widget

[//]: # (end addons)

<!-- prettier-ignore-end -->

----
