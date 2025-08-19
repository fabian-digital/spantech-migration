# CLAUDE-Odoo18.md - Odoo 16 and 17 to 18 Version Changes Guide

## Overview
This document outlines the major code changes in Odoo 18 compared to versions 17 and 16, providing developers with essential migration information and best practices.

## Table of Contents
- [XML View Changes](#xml-view-changes)
- [Python Field Changes](#python-field-changes)
- [ORM API Changes](#orm-api-changes)
- [Configuration Changes](#configuration-changes)
- [Widget Updates](#widget-updates)
- [Deprecated Features](#deprecated-features)
- [Performance Improvements](#performance-improvements)
- [Migration Guide](#migration-guide)
- [Best Practices](#best-practices)

## XML View Changes

### Tree → List Tag Rename (Odoo 18)
One of the most prominent changes in Odoo 18 is the renaming of the `tree` tag to `list`.

**Before (Odoo 16/17):**
```xml
<tree>
    <field name="name"/>
    <field name="state"/>
</tree>
```

**After (Odoo 18):**
```xml
<list>
    <field name="name"/>
    <field name="state"/>
</list>
```

### Simplified Conditional Attributes (Odoo 18)
Odoo 18 simplifies the use of conditional attributes by replacing `attrs` and `states` with direct attributes.

#### Single Condition
**Before:**
```xml
<field name="shift_id" attrs="{'invisible': [('shift_schedule', '=', [])]}"/>
```

**After:**
```xml
<field name="shift_id" invisible="not shift_schedule"/>
```

#### Multiple Conditions (OR)
**Before:**
```xml
<field name="department_id" attrs="{'invisible': ['|', ('state', '=', 'done'), ('type', '=', 'internal')]}"/>
```

**After:**
```xml
<field name="department_id" invisible="state == 'done' or type == 'internal'"/>
```

#### Multiple Conditions (AND)
**Before:**
```xml
<field name="job_position" attrs="{'readonly': [('state', '=', 'approved'), ('user_id', '!=', user.id)]}"/>
```

**After:**
```xml
<field name="job_position" readonly="state == 'approved' and user_id != user.id"/>
```

#### States Attribute Replacement
**Before:**
```xml
<button string="Submit" states="draft"/>
```

**After:**
```xml
<button string="Submit" invisible="state != 'draft'"/>
```

### Chatter Simplification (Odoo 18)
Odoo 18 introduces a new way to define the chatter, eliminating verbose XML.

**Before:**
```xml
<div class="oe_chatter">
    <field name="message_follower_ids" widget="mail_followers"/>
    <field name="activity_ids" widget="mail_activity"/>
    <field name="message_ids" widget="mail_thread"/>
</div>
```

**After:**
```xml
<chatter/>
<!-- or with customization -->
<chatter reload_on_follower="True"/>
```

## Python Field Changes

### Removed States Attribute (Odoo 18)
Odoo 18 has removed the `states` attribute in Python field definitions.

**Before:**
```python
date = fields.Date(
    string='Date',
    index=True,
    compute='_compute_date', 
    store=True, 
    required=True, 
    readonly=False, 
    precompute=True,
    states={'posted': [('readonly', True)], 'cancel': [('readonly', True)]},
    copy=False,
    tracking=True,
)
```

**After:**
```python
date = fields.Date(
    string='Date',
    index=True,
    compute='_compute_date', 
    store=True, 
    required=True, 
    readonly=False, 
    precompute=True,
    copy=False,
    tracking=True,
)
# Handle readonly logic in UI or through other means
```

## ORM API Changes

### Odoo 18 Changes
- **Name Search**: Searching by name is now implemented as `_search_display_name` like all other fields
- **Access Rights**: New methods to check access rights and rules: `check_access`, `has_access`, and `_filtered_access`
- **Field Aggregation**: The `group_operator` attribute of Field is renamed to `aggregator`
- **Query Operations**: The internal operator `inselect` is removed. Use `in` with a Query or SQL object instead
- **Date Grouping**: Can now group by date parts numbers in `read_group`, `_read_group` and domains
- **Translations**: Made available from the Environment
- **Deprecated Methods**: `_flush_search()`, `fields_get_keys()`, and `get_xml_id()` are deprecated

### Odoo 17 Changes (from 16)
- **Domain Parameter**: The argument `args` is renamed to `domain` for `search()`, `search_count()` and `_search()`
- **Cache API**: New API for flushing to the database and invalidating the cache
- **Index Types**: Developers can define specific index types on fields for PostgreSQL
- **Sequence Removal**: The `_sequence` attribute of Model is removed
- **Limit Attribute**: Removed from One2many and Many2many fields
- **Translations**: Stored as JSONB values, code translations are static and extracted from PO files

## Configuration Changes

### Settings Structure (Odoo 18)
The structure of `res.config.settings` has been simplified with new tags.

**Before:**
```xml
<div class="app_settings_block" data-string="application_settings" string="Application Settings">
    <h2>Example Settings</h2>
    <div class="row mt16 o_settings_container">
        <label for="example_setting" string="Example Setting" class="ml-4 mt-4"/>
    </div>
    <div class="row mt16 o_settings_container">
        <field class="ml-4" name="example_setting"/>
    </div>
    <div class="row mt16 o_settings_container">
        <div class="text-muted ml-4">
            Description for the example setting.
        </div>
    </div>
</div>
```

**After:**
```xml
<app string="Application Settings">
    <block title="Example Settings">
        <setting string="Example Setting" help="Description for the example setting">
            <field name="example_setting"/>
        </setting>
    </block>
</app>
```

## Widget Updates

### DateRange Widget (Odoo 18)
The `daterange` widget has been updated for better functionality.

**Before:**
```xml
<div>
    <field name="start_date" widget="daterange" options="{'related_end_date': 'end_date'}"/>
    <field name="end_date" widget="daterange" options="{'related_start_date': 'start_date'}"/>
</div>
```

**After:**
```xml
<div>
    <field name="start_date" widget="daterange" options="{'end_date_field': 'end_date'}"/>
</div>
```

## Deprecated Features

### Odoo 18 Deprecations
- `Not Number Call` and `Doall` in scheduled actions (cron jobs)
- `_flush_search()` method
- `fields_get_keys()` and `get_xml_id()` methods on Model
- `states` attribute in Python field definitions
- `attrs` and `states` attributes in XML views

### Odoo 17 Deprecations (from 16)
- `_sequence` attribute of Model
- `limit` attribute of One2many and Many2many
- `_mapped_cache()` method
- `args` parameter (renamed to `domain`)

## Performance Improvements

### Odoo 18
- **Database Performance**: 15-20% boost in database performance
- **Backend Speed**: On average, every page in the backend is 3.7 times faster to load and render
- **Frontend Speed**: Website and eCommerce are 2.7 times faster to load controllers
- **Enhanced ORM**: Updated ORM layer performance
- **JavaScript Framework**: Updated JavaScript framework components
- **REST API**: Improved REST API capabilitiesls

### Odoo 17
- **Search Count**: `search_count()` takes the limit argument into account for better performance
- **Cache API**: New flushing and invalidation API for better performance
- **Index Types**: Specific PostgreSQL index types for optimized queries

## Database Schema Changes

[Odoo 18 Database Schema](db_schemas/18_oe_schema.sql)

- In the table mrp_production the field date_planned_start must be renamed date_start


## Migration Guide

### Step 1: Update XML Views
```bash
# Find and replace tree tags
find . -name "*.xml" -exec sed -i 's/<tree>/<list>/g' {} \;
find . -name "*.xml" -exec sed -i 's/<\/tree>/<\/list>/g' {} \;
```

### Step 2: Replace Conditional Attributes
**Search for patterns like:**
```xml
attrs="{'invisible': [('field', '=', 'value')]}"
```

**Replace with:**
```xml
invisible="field == 'value'"
```

### Step 3: Update Python Fields
Remove `states` attributes from field definitions and handle logic in UI.

### Step 4: Update Chatter
Replace verbose chatter XML with simple `<chatter/>` tag.

### Step 5: Update Configuration Settings
Refactor `res.config.settings` views to use new `app`, `block`, and `setting` tags.

### Step 6: Update ORM Methods
- Replace deprecated methods
- Update `args` parameter to `domain`
- Use new access rights methods

## Best Practices

### Code Quality
1. **Use new syntax**: Adopt simplified XML syntax for better readability
2. **Remove deprecated code**: Clean up old attrs/states usage
3. **Optimize queries**: Use new ORM features for better performance
4. **Test thoroughly**: Validate all custom modules after migration

### Migration Strategy
1. **Incremental updates**: Migrate 16→17→18 for complex customizations
2. **Test environment**: Set up parallel test environment
3. **Backup data**: Complete system backup before migration
4. **Partner support**: Consider certified Odoo partner for complex migrations

### Development Guidelines
1. **Follow new patterns**: Use list tags, direct attributes, simplified chatter
2. **Performance focus**: Leverage new ORM capabilities
3. **Future-proof**: Avoid deprecated methods in new development
4. **Documentation**: Update internal docs with new syntax

## Testing Checklist

### Pre-Migration
- [ ] Identify all custom modules
- [ ] Document current customizations
- [ ] Create complete backup
- [ ] Set up test environment

### Post-Migration
- [ ] Verify XML view rendering
- [ ] Test conditional field behavior
- [ ] Validate chatter functionality
- [ ] Check configuration settings
- [ ] Test ORM operations
- [ ] Verify performance improvements

## Common Issues and Solutions

### Issue: XML Views Not Rendering
**Problem**: Old `tree` tags not recognized
**Solution**: Update all `<tree>` to `<list>` tags

### Issue: Conditional Fields Not Working
**Problem**: `attrs` attribute not working
**Solution**: Replace with direct attributes like `invisible="condition"`

### Issue: Chatter Not Displaying
**Problem**: Old chatter XML structure
**Solution**: Replace with simple `<chatter/>` tag

### Issue: Configuration Settings Layout Broken
**Problem**: Old settings structure
**Solution**: Update to use `app`, `block`, `setting` tags

## Resources

- [Odoo 18 Official Documentation](https://www.odoo.com/documentation/18.0/)
- [Odoo 18 Release Notes](https://www.odoo.com/odoo-18-release-notes)
- [ORM API Changelog](https://www.odoo.com/documentation/18.0/developer/reference/backend/orm/changelog.html)
- [Migration Services](https://www.odoo.com/documentation/18.0/administration/upgrade.html)

## Contributing

To contribute to this documentation:
1. Fork the repository
2. Create a feature branch
3. Add examples and clarifications
4. Submit a pull request

## Version History

### v1.0.0 (Current)
- Initial comprehensive guide for Odoo 18 changes
- Complete XML and Python migration examples
- ORM API changes documentation
- Performance improvement details

### Future Updates
- Additional migration examples
- Common error patterns and solutions
- Advanced customization scenarios
- Integration update guidelines