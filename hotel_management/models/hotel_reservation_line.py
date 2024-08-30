from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class HotelReservationLine(models.Model):
    _name = "hotel_management.reservation.line"
    _description = "Reservation Line Details"

    reservation_id = fields.Many2one("hotel_management.reservation", string="Reservation")
    room_id = fields.Many2one("hotel_management.room", string="Room",store=True, required=True)
    check_in = fields.Date(string="Check-In")
    check_out = fields.Date(string="Check-Out")
    rent = fields.Float(string="Rent", required=True)
    duration = fields.Integer(string="Duration", compute="_compute_duration", store=True)
    sub_total = fields.Float(string="Sub Total", compute="_compute_sub_total", store=True)

    @api.onchange('room_id')
    def _onchange_room_id(self):
        if self.room_id:
            self.rent = self.room_id.rent

    @api.depends('rent', 'duration')
    def _compute_sub_total(self):
        for line in self:
            line.sub_total = line.rent * line.duration if line.rent and line.duration else 0

    @api.depends('check_in', 'check_out')
    def _compute_duration(self):
        for line in self:
            if line.check_in and line.check_out:
                # Menghitung jumlah hari antara check_in dan check_out
                check_in_date = fields.Date.from_string(line.check_in)
                check_out_date = fields.Date.from_string(line.check_out)
                duration = (check_out_date - check_in_date).days
                # Menangani kasus di mana check_out lebih awal dari check_in
                if duration < 0:
                    raise ValidationError("Check-Out date cannot be earlier than Check-In date.")
                line.duration = duration
            else:
                line.duration = 0

    def _update_status(self):
        now = datetime.now().date()
        for line in self:
            # Memperbarui status ruangan berdasarkan tanggal check-in dan check-out
            if line.check_in <= now < line.check_out:
                line.room_id.status = 'occupied'
            else:
                # Cek status reservasi dan update status ruangan
                reservation = line.reservation_id
                if reservation:
                    if reservation.state == 'draft':
                        line.room_id.status = 'booked'
                    elif reservation.state in ['checkin', 'checkout', 'done']:
                        line.room_id.status = 'available'

    
    def write(self, vals):
        res = super(HotelReservationLine, self).write(vals)
        self._update_status()
        return res
    
    @api.model
    def create(self, vals):
        record = super(HotelReservationLine, self).create(vals)
        record._update_status()
        return record

