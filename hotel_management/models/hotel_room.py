from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HotelRoom(models.Model):
    _name = 'hotel_management.room'
    _description = 'Hotel Room'

    name = fields.Char(string="Room Name", required=True)
    icon = fields.Binary(string='Icon')
    floor_id = fields.Many2one('hotel_management.floor', string="Floor", ondelete='set null')
    manager_id = fields.Many2one('res.partner', string="Manager")
    room_type = fields.Selection([('single', 'Single'), ('double', 'Double'),('tripel', 'Tripel')], string="Room Type")
    rent = fields.Float(string="Rent Price")
    number_of_person = fields.Integer(string="Number of Person")
    description = fields.Html(string="Description")
    reservation_ids = fields.One2many('hotel_management.reservation', 'room_id', string='Reservations')
    reservation_line_ids = fields.One2many('hotel_management.reservation.line', 'room_id', string='Reservation Lines')
    amenities_id = fields.One2many('hotel_management.room.amenities', 'room_id', string='Amenities')

    total_amenity_cost = fields.Float(string="Total Amenity Cost", compute='_compute_total_amenity_cost', store=True)
    status = fields.Selection([
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('occupied', 'Occupied'),
    ], string='Status', default='available', compute='_compute_status', store=True)

    @api.onchange('floor_id')
    def _onchange_floor_id(self):
        if self.floor_id:
            self.manager_id = self.floor_id.manager_ids

    @api.depends('reservation_line_ids.check_in', 'reservation_line_ids.check_out', 'reservation_line_ids.reservation_id.state')
    def _compute_status(self):
        for room in self:
            now = fields.Date.today()
            status = 'available'

            for line in room.reservation_line_ids:
                check_in = line.check_in
                check_out = line.check_out
                reservation_state = line.reservation_id.state

                if check_in and check_out and check_in <= now <= check_out:
                    if reservation_state == 'checkin':
                        status = 'occupied'
                    elif reservation_state == 'checkout':
                        status = 'available'
                    elif reservation_state == 'booking':
                        status = 'booked'
                    break
                elif reservation_state == 'checkin':
                    status = 'occupied'
                elif reservation_state == 'booking' and status != 'occupied':
                    status = 'booked'

            room.status = status

    @api.model
    def create(self, vals):
        if 'floor_id' in vals:
            floor = self.env['hotel_management.floor'].browse(vals['floor_id'])
            if floor.manager_ids:
                vals['manager_id'] = floor.manager_ids.id
        res = super(HotelRoom, self).create(vals)
        return res

    def write(self, vals):
        if 'floor_id' in vals:
            floor = self.env['hotel_management.floor'].browse(vals['floor_id'])
            if floor.manager_ids:
                vals['manager_id'] = floor.manager_ids.id
        res = super(HotelRoom, self).write(vals)
        return res

    def unlink(self):
        for room in self:
            if room.reservation_line_ids:
                room.reservation_line_ids.unlink()
        return super(HotelRoom, self).unlink()
