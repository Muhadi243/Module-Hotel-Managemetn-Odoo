from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HotelReservation(models.Model):
    _name = "hotel_management.reservation"
    _description = "Hotel Reservation"

    name = fields.Char(
        string='Booking Reference',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: self._get_default_name()
    )
    customer_ids = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True
    )
    reservation_reference = fields.Many2one(
        "res.partner",
        string="Reservation Reference",
        required=True,
        tracking=True
    )
    room_id = fields.Many2one(
        "hotel_management.room",
        string="Room",
        required=True,
        tracking=True,
        compute="_compute_room_ids"
    )
    order_date = fields.Date(
        string="Order Date",
        required=True,
        default=fields.Date.today
    )
    reservation_line_ids = fields.One2many(
        "hotel_management.reservation.line",
        "reservation_id",
        string="Reservation Lines"
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('booking', 'Booking'),
        ('checkin', 'Check-In'),
        ('checkout', 'Check-Out'),
        ('done', 'Done')
    ], string="State", readonly=True, copy=False, index=True, tracking=True, default='draft')
    duration = fields.Integer(
        string="Duration",
        compute="_compute_duration",
        store=True
    )

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].next_by_code('reservation.sequence') or 'New'

    @api.model
    def create(self, vals):
        if 'name' not in vals:
            vals['name'] = self._get_default_name()
        return super(HotelReservation, self).create(vals)

    def action_booking(self):
        self.write({'state': 'booking'})
        self._update_room_status()

    def action_checkin(self):
        self.write({'state': 'checkin'})
        self._update_room_status()

    def action_checkout(self):
        self.write({'state': 'checkout'})
        self._update_room_status()

    def action_done(self):
        self.write({'state': 'done'})
        self._update_room_status()

    def action_cancel(self):
        if self.state in ['checkin', 'checkout', 'done']:
            raise UserError("Cannot cancel a reservation that is already checked-in, checked-out or done.")
        self.write({'state': 'draft'})
        self._update_room_status()

    def _update_room_status(self):
        if self.room_id:
            self.room_id._compute_status()

    @api.constrains('order_date')
    def _check_order_date(self):
        if self.order_date and self.order_date < fields.Date.today():
            raise UserError("Order date cannot be in the past.")

    @api.depends('reservation_line_ids.check_in', 'reservation_line_ids.check_out')
    def _compute_duration(self):
        for record in self:
            if record.reservation_line_ids:
                total_duration = 0
                for line in record.reservation_line_ids:
                    if line.check_in and line.check_out:
                        duration = (line.check_out - line.check_in).days
                        total_duration += duration
                record.duration = total_duration
            else:
                record.duration = 0

    @api.constrains('duration')
    def _check_duration(self):
        for record in self:
            if record.duration <= 0:
                raise UserError("Duration must be a positive integer.")

    @api.depends('reservation_line_ids.room_id')
    def _compute_room_ids(self):
        for record in self:
            room_ids = record.reservation_line_ids.mapped('room_id')
            record.room_id = room_ids
