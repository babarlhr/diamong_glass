# -*- coding: utf-8 -*-
# Copyright 2016 
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
import datetime
from datetime import timedelta, date
# from openerp.exceptions import Warning, ValidationError, UserError




class ManufacturingExtension(models.Model):

	_inherit = 'mrp.production'

	batch_no = fields.Char('Batch No',  copy=False, help="Batch Number")
	work_order_times = fields.One2many('work.center.time','order_id')
	state = fields.Selection([
		('draft', 'Hold'),
		('not_planned', 'Not Planned'),
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



	# def fetch_batch_info(self):
	#     workcenters = self.env['mrp.workcenter'].search([])
	#     self.work_order_times.unlink()
	#     for wk in workcenters:
	#         self.env['work.center.time'].create({
	#             'name':wk.id,
	#             'sequence':wk.sequence,
	#             'order_id':self.id
	#             })

	def plan_mo(self):
		# self.state = "planned"
		workorders = self.env['mrp.workorder'].search([('production_id','=',self.id)])
		for wok in workorders:
			wok.unlink()
		sequences = []
		sorted_seq_wise = self.env['work.center.time'].search([('order_id','=',self.id),('time','!=',False)]).sorted(key=lambda r: r.sequence)
		for seq in sorted_seq_wise:
			sequences.append(seq.sequence)
		sequences = set(sequences)
		sequences = list(sequences)

		order_start = self.date_planned_start
		previous_workorders = ""
		Wk_created = []
		for x in sorted_seq_wise:
			if sequences.index(x.sequence) > 0:
				previous_seq =  sequences[(sequences.index(x.sequence) - 1)]
				previous_workorders = self.env['mrp.workorder'].search([('production_id','=',self.id),('sequence','=',previous_seq)]).sorted(key=lambda r: r.date_planned_finished,reverse=True)
				if previous_workorders:
					previous_end_time = previous_workorders[0]
			# else:
			#     previous_seq = [-1]

			if previous_workorders:
				first_slot = self.env['time.slots.lines'].search([('remaining_time','>',0),('workcenter','=',x.name.id),('start_time','<',previous_end_time.date_planned_finished),('end_time','>',previous_end_time.date_planned_finished)]).sorted(key=lambda r: r.start_time)
				next_slots = self.env['time.slots.lines'].search([('remaining_time','>',0),('workcenter','=',x.name.id),('start_time','>=',previous_end_time.date_planned_finished)]).sorted(key=lambda r: r.start_time)
				time_slots = first_slot + next_slots
			else:
				time_slots = self.env['time.slots.lines'].search([('remaining_time','>',0),('workcenter','=',x.name.id)]).sorted(key=lambda r: r.start_time)
			time_to_adjust = x.time

			count = 0
			Wk_created = []
			for time in time_slots:
				if time_to_adjust > 0:
					if previous_workorders and count == 0:
						starting_time = previous_end_time.date_planned_finished
					else:
						starting_time = time.start_time

					count = count + 1


					if time_to_adjust >= time.remaining_time:
						
						if starting_time < time.start_time:
							starting_time = time.start_time
						start_time = starting_time 
						end_time = time.end_time
						
					if time_to_adjust < time.remaining_time:
						if starting_time < time.start_time:
							starting_time = time.start_time
						start_time = starting_time
						end_time = start_time + timedelta(hours=time_to_adjust,minutes=0)
						if end_time > time.end_time:
							end_time = time.end_time
						

					adjusted_time = ((time.end_time - start_time).total_seconds()/3600)
					
					time_to_adjust = time_to_adjust - adjusted_time

					
					if start_time != end_time:
						CreateWK = workorders.create({
							'name': x.name.name,
							'production_id': self.id,
							'workcenter_id': x.name.id,
							'product_uom_id': self.product_id.uom_id.id,
							'operation_id': x.operation_id.id,
							# 'state': len(workorders) == 0 and 'ready' or 'pending',
							'qty_producing': 100,
							'sequence': x.sequence,
							'date_planned_start': start_time,
							'date_planned_finished': end_time,
							'consumption': self.bom_id.consumption,
							'time_slot_id': time.time_slot_id_lines.id,
							})
						Wk_created.append(CreateWK)
			for ref in Wk_created:
				ref.time_slot_id.RefreshSlotLines()
						# CreateWK.time_slot_id.RefreshSlotLines()
						# print (CreateWK)






# workorder = workorders.create({
# 'name': operation.name,
# 'production_id': self.id,
# 'workcenter_id': operation.workcenter_id.id,
# 'product_uom_id': self.product_id.uom_id.id,
# 'operation_id': operation.id,
# 'state': len(workorders) == 0 and 'ready' or 'pending',
# 'qty_producing': quantity,
# 'consumption': self.bom_id.consumption,






	def not_planned(self):
		self.state = "not_planned"

class WorkCentersTime(models.Model):
	_name = "work.center.time"

	name = fields.Many2one('mrp.workcenter',string = "Name")
	operation_id = fields.Many2one('mrp.routing.workcenter',string ="Operation")
	time = fields.Float()
	sequence = fields.Integer()
	planned_start = fields.Datetime(string = "Planned Start")
	planned_end = fields.Datetime(string = "Planned End")
	actual_start = fields.Datetime(string = "Actual Start")
	actual_end = fields.Datetime(string = "Actual End")
	order_id = fields.Many2one('mrp.production')


class ResourceCalendarExtension(models.Model):

	_inherit = 'resource.calendar.attendance'


	breaks = fields.Many2many('break.time',string = "Break")
	break_from = fields.Float(string = "Break From")
	break_to = fields.Float(string = "Break To")
	day_period = fields.Selection([('morning', 'Morning'), ('afternoon', 'Evening'), ('night', 'Night')], required=True, default='morning')
	total_break = fields.Float(string = "Total Break")
	total_time = fields.Float(string = "Total Time")

	@api.onchange('breaks','hour_from','hour_to')
	def GetTime(self):
		totalBreak = 0
		for brk in self.breaks:
			totalBreak = totalBreak + brk.total_break
		self.total_break = totalBreak
		self.total_time =  self.hour_to - self.hour_from - self.total_break


class WorkCenterExtension(models.Model):

	_inherit = 'mrp.workcenter'

	planned_till = fields.Date(string= "Planned Till")


	def GenerateTimeslots(self):
		all_time_slots = self.env['time.slots'].search([('workcenter','=',self.id)])
		for allt in all_time_slots:
			allt.unlink()
		all_time_slots_lines = self.env['time.slots.lines'].search([('workcenter','=',self.id)])
		for alltl in all_time_slots_lines:
			alltl.unlink()
		delta = timedelta(days=1)
		start_date = fields.date.today()
		while start_date <= self.planned_till:
			for time in self.resource_calendar_id.attendance_ids:
				day_of_week = start_date.weekday() 
				if int(day_of_week) == int(time.dayofweek):
					break_list = []
					for brk in time.breaks:
						time_formated =   '{0:02.0f}:{1:02.0f}'.format(*divmod(brk.break_from * 60, 60))
						date_time_comb = self.time_tango(start_date,time_formated)
						break_list.append({
							'start':brk.break_from,
							'end':brk.break_to,
							})
					
					work_from = '{0:02.0f}:{1:02.0f}'.format(*divmod(time.hour_from * 60, 60))
					work_to = '{0:02.0f}:{1:02.0f}'.format(*divmod(time.hour_to * 60, 60))
					
					break_list_sorted =sorted(break_list, key=lambda k: k['start']) 
					
					for index, brklst in enumerate(break_list_sorted):
						if index == 0:
							start_time = float(brklst.get("start", ""))
							start_time_break = '{0:02.0f}:{1:02.0f}'.format(*divmod(start_time * 60, 60))
							slot_start = self.time_tango(start_date,work_from) - timedelta(hours=5)
							slot_end = self.time_tango(start_date,start_time_break) - timedelta(hours=5)
							self.CreateTimeSlots(slot_start,slot_end,time.name,self.id)

						
						if index == len(break_list)-1:
							previous_index = index -1 
							relevant_break = break_list_sorted[previous_index]
							starting_time = float(relevant_break.get("end", ""))
							starting_time_break = '{0:02.0f}:{1:02.0f}'.format(*divmod(starting_time * 60, 60))
							ending_time = float(brklst.get("start", ""))
							ending_time_break = '{0:02.0f}:{1:02.0f}'.format(*divmod(ending_time * 60, 60))
							slot_start = self.time_tango(start_date,starting_time_break) - timedelta(hours=5)
							slot_end = self.time_tango(start_date,ending_time_break) - timedelta(hours=5)

							self.CreateTimeSlots(slot_start,slot_end,time.name,self.id)

							# Ending Slot

							starting_time_last = float(brklst.get("end", ""))
							starting_time_break_last = '{0:02.0f}:{1:02.0f}'.format(*divmod(starting_time_last * 60, 60))
							slot_start_last = self.time_tango(start_date,starting_time_break_last) - timedelta(hours=5)
							slot_end_last = self.time_tango(start_date,work_to) - timedelta(hours=5)

							self.CreateTimeSlots(slot_start_last,slot_end_last,time.name,self.id)
					   
			start_date += delta

	def time_tango(self,date, time):
		return datetime.datetime.strptime("{}, {}".format(date, time), "%Y-%m-%d, %H:%M")

	def CreateTimeSlots(self,starttime,endtime,shiftname,workcenter):
		CreateSlots = self.env['time.slots'].create({
			'start_time':starttime,
			'end_time':endtime,
			'shift_name':shiftname,
			'workcenter':workcenter,
			})
		CreateSlots.UpdateTime()



class BreakTime(models.Model):
	_name = "break.time"

	break_from = fields.Float(string = "Break From")
	break_to = fields.Float(string = "Break To")
	total_break = fields.Float(string = "Total Break")
	name = fields.Char()

	@api.onchange('break_from','break_to')
	def GetTime(self):
		break_from =  (str(datetime.timedelta(hours=self.break_from))[:-3])
		break_to = (str(datetime.timedelta(hours=self.break_to))[:-3])
		self.total_break = self.break_to - self.break_from 
		self.name = break_from + " - " + break_to

class WorkOrderExtension(models.Model):

	_inherit = 'mrp.workorder'

	sequence = fields.Integer()
	time_slot_id = fields.Many2one('time.slots')

	# def write(self, vals):
		
	# 	super(WorkOrderExtension, self).write(vals)
		



	# 	return True

	def TimeOverlap(self):
		workorder_start = self.env['mrp.workorder'].search([('date_planned_start','<=',self.date_planned_start),('date_planned_finished','>=',self.date_planned_start)])
		workorder_end = self.env['mrp.workorder'].search([('date_planned_start','<=',self.date_planned_start),('date_planned_finished','>=',self.date_planned_start)])

		if workorder_start or workorder_end:
			raise ValidationError("Date is overlapping")




class TimeSlots(models.Model):
	_name = "time.slots"

	start_time = fields.Datetime("Start Time")
	end_time = fields.Datetime("End Time")
	shift_name = fields.Char("Shift Name")
	workcenter = fields.Many2one('mrp.workcenter')
	total_time = fields.Float("Total Time")
	remaining_time = fields.Float("Remaining Time")

	workorder_lines = fields.One2many('mrp.workorder','time_slot_id')
	timeslot_lines = fields.One2many('time.slots.lines','time_slot_id_lines')


	def UpdateTime(self):
		total_time = self.end_time - self.start_time
		time_float = total_time.total_seconds()
		self.total_time = time_float/3600
		self.remaining_time = time_float/3600

	@api.model
	def create(self, vals):
		new_record = super(TimeSlots, self).create(vals)
		new_record.UpdateTime()
		new_record.GenerateSlotLines(new_record.start_time,new_record.end_time,new_record.remaining_time)

		return new_record

	def GenerateSlotLines(self,start_time,end_time,remaining_time):
		self.env['time.slots.lines'].create({
			'start_time':start_time,
			'end_time':end_time,
			'shift_name':self.shift_name,
			'workcenter':self.workcenter.id,
			'remaining_time':remaining_time,
			'time_slot_id_lines':self.id,
			})

	def RefreshSlotLines(self):
		work_orders = self.env['mrp.workorder'].search([('time_slot_id','=',self.id)]).sorted(key=lambda r: r.date_planned_start)
		if work_orders:
			self.timeslot_lines.unlink()       
			relevant_index = 0

			for rec in work_orders:
				if len(work_orders) == 1:
				# previous_order = self.env['mrp.workorder'].search([('time_slot_id','=',self.id)]).sorted(key=lambda r: r.date_planned_start)[relevant_index-1]
					this_order = self.env['mrp.workorder'].search([('time_slot_id','=',self.id)]).sorted(key=lambda r: r.date_planned_start)[relevant_index]
					# next_order = self.env['mrp.workorder'].search([('time_slot_id','=',self.id)]).sorted(key=lambda r: r.date_planned_start)[relevant_index + 1]

					# if not previous_order and not next_order:
					if self.start_time == this_order.date_planned_start:
						start_time = this_order.date_planned_finished
						end_time = self.end_time
						if start_time != end_time:
							self.GenerateSlotLines(start_time,end_time,(end_time-start_time).total_seconds()/3600)
					if self.start_time != this_order.date_planned_start:
						start_time_before = self.start_time
						end_time_before = this_order.date_planned_start
						if start_time_before != end_time_before:
							self.GenerateSlotLines(start_time_before,end_time_before,(end_time_before-start_time_before).total_seconds()/3600)
						start_time = this_order.date_planned_finished
						end_time = self.end_time
						if start_time != end_time:
							self.GenerateSlotLines(start_time,end_time,(end_time-start_time).total_seconds()/3600)
				if len(work_orders) > 1:
					if (relevant_index +1) == 1:
						this_order = self.env['mrp.workorder'].search([('time_slot_id','=',self.id)]).sorted(key=lambda r: r.date_planned_start)[relevant_index]
						if self.start_time != this_order.date_planned_start:
							start_time = self.start_time
							end_time = this_order.date_planned_start
							self.GenerateSlotLines(start_time,end_time,(end_time-start_time).total_seconds()/3600)
					elif (relevant_index +1) == len(work_orders):
						this_order = self.env['mrp.workorder'].search([('time_slot_id','=',self.id)]).sorted(key=lambda r: r.date_planned_start)[relevant_index]
						previous_order = self.env['mrp.workorder'].search([('time_slot_id','=',self.id)]).sorted(key=lambda r: r.date_planned_start)[relevant_index-1]
						if previous_order.date_planned_finished != this_order.date_planned_start:
							start_time = previous_order.date_planned_finished
							end_time = this_order.date_planned_start
							self.GenerateSlotLines(start_time,end_time,(end_time-start_time).total_seconds()/3600)
						if this_order.date_planned_finished != self.end_time:
							start_time = this_order.date_planned_finished
							end_time = self.end_time
							self.GenerateSlotLines(start_time,end_time,(end_time-start_time).total_seconds()/3600)
					else:
						this_order = self.env['mrp.workorder'].search([('time_slot_id','=',self.id)]).sorted(key=lambda r: r.date_planned_start)[relevant_index]
						previous_order = self.env['mrp.workorder'].search([('time_slot_id','=',self.id)]).sorted(key=lambda r: r.date_planned_start)[relevant_index-1]
						if previous_order.date_planned_finished != this_order.date_planned_start:
							start_time = previous_order.date_planned_finished
							end_time = this_order.date_planned_start
							self.GenerateSlotLines(start_time,end_time,(end_time-start_time).total_seconds()/3600)
				relevant_index = relevant_index + 1









				# if this_order.date_planned_start != self.start_time:
				#     start_time = 

				# if len(work_orders) == 1 and rec.date_planned_start > self.start_time:
				#     total_time_n = self.start_time - rec.date_planned_finished
				#     time_float_n = total_time_n.total_seconds()
				#     # self.total_time = time_float/3600
				#     remaining_time_n = time_float_n/3600
				#     self.env['time.slots.lines'].create({
				#             'start_time':self.start_time,
				#             'end_time':rec.date_planned_finished,
				#             'shift_name':self.shift_name,
				#             'workcenter':self.workcenter.id,
				#             'remaining_time': remaining_time_n,
				#             'time_slot_id_lines':self.id,
				#         })
				# this_order = self.env['mrp.workorder'].search([('time_slot_id','=',self.id)]).sorted(key=lambda r: r.date_planned_start)[relevant_index]
				# if relevant_index == 0:
				#     print ("-------------------------------")
				#     start_time = self.start_time
				#     end_time = this_order.date_planned_start
				#     print (end_time)
				#     print (start_time)
					
				# elif (relevant_index + 1) == len(work_orders):
				#     start_time = this_order.date_planned_finished
				#     end_time = self.end_time
				# else:
				#     next_order = self.env['mrp.workorder'].search([('time_slot_id','=',self.id)]).sorted(key=lambda r: r.date_planned_start)[relevant_index + 1]
				#     start_time = this_order.date_planned_finished
				#     end_time = next_order.date_planned_start

				# relevant_index = relevant_index + 1
				# print (end_time)
				# print (start_time)
				# total_time = end_time - start_time
				# print (total_time)
				# time_float = total_time.total_seconds()
				# # self.total_time = time_float/3600
				# remaining_time = time_float/3600

				# if remaining_time != 0:

				
				#     self.env['time.slots.lines'].create({
				#             'start_time':start_time,
				#             'end_time':end_time,
				#             'shift_name':self.shift_name,
				#             'workcenter':self.workcenter.id,
				#             'remaining_time': remaining_time,
				#             'time_slot_id_lines':self.id,
				#         })









class TimeSlotsLines(models.Model):
	_name = "time.slots.lines"

	start_time = fields.Datetime("Start Time")
	end_time = fields.Datetime("End Time")
	shift_name = fields.Char("Shift Name")
	workcenter = fields.Many2one('mrp.workcenter')
	remaining_time = fields.Float("Remaining Time")

	time_slot_id_lines = fields.Many2one('time.slots')


