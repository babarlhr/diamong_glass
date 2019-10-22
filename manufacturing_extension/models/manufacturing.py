# -*- coding: utf-8 -*-
# Copyright 2016 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ManufacturingExtension(models.Model):

    _inherit = 'mrp.production'

    batch_no = fields.Char('Batch No',  copy=False, help="Batch Number")
    work_order_times = fields.One2many('work.center.time','order_id')
    state = fields.Selection([
        ('draft', 'Not Planned'),
        ('hold', 'Hold'),
        ('confirmed', 'Confirmed'),
        ('planned', 'Planned'),
        ('progress', 'In Progress'),
        ('to_close', 'To Close'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='State',
        compute='_compute_state', copy=False, index=True, readonly=True,
        store=True, tracking=True,
        help=" * Draft: The MO is not confirmed yet.\n"
             " * Confirmed: The MO is confirmed, the stock rules and the reordering of the components are trigerred.\n"
             " * Planned: The WO are planned.\n"
             " * In Progress: The production has started (on the MO or on the WO).\n"
             " * To Close: The production is done, the MO has to be closed.\n"
             " * Done: The MO is closed, the stock moves are posted. \n"
             " * Cancelled: The MO has been cancelled, can't be confirmed anymore.")



    def fetch_batch_info(self):
        workcenters = self.env['mrp.workcenter'].search([])
        self.work_order_times.unlink()
        for wk in workcenters:
            self.env['work.center.time'].create({
                'name':wk.id,
                'sequence':wk.sequence,
                'order_id':self.id
                })

    def plan_mo(self):
        self.state = "planned"

    def hold_batch(self):
        self.state = "hold"

class WorkCentersTime(models.Model):
    _name = "work.center.time"

    name = fields.Many2one('mrp.workcenter',string = "Name")
    time = fields.Float()
    sequence = fields.Integer()
    planned_start = fields.Datetime(string = "Planned Start")
    planned_end = fields.Datetime(string = "Planned End")
    actual_start = fields.Datetime(string = "Actual Start")
    actual_end = fields.Datetime(string = "Actual End")
    order_id = fields.Many2one('mrp.production')


class ResourceCalendarExtension(models.Model):

    _inherit = 'resource.calendar.attendance'

    break_from = fields.Float(string = "Break From")
    break_to = fields.Float(string = "Break To")
    day_period = fields.Selection([('morning', 'Morning'), ('afternoon', 'Evening'), ('night', 'Night')], required=True, default='morning')
    total_break = fields.Float(string = "Total Break")
    total_time = fields.Float(string = "Total Time")

    @api.onchange('break_from','break_to','hour_from','hour_to')
    def GetTime(self):
        self.total_break = self.break_to - self.break_from
        self.total_time =  self.hour_to - self.hour_from - self.total_break

    