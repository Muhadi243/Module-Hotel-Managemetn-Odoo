from odoo import models, fields, api

class HotelRoomAmenities(models.Model):
    _name = 'hotel_management.room.amenities'
    _description = 'Hotel Room Amenities'

    room_id = fields.Many2one('hotel_management.room', string="Room", required=True, ondelete='cascade')
    amenities_id = fields.Many2one('hotel_management.amenities', string="Amenity", required=True)
    product_id = fields.Many2one('product.product', string="Related Product")
    quantity = fields.Integer(string="Quantity", default=1)
    price_unit = fields.Float(string="Unit Price")
    total_price = fields.Float(string="Total Price", compute='_compute_total_price', store=True)

    @api.depends('quantity', 'price_unit')
    def _compute_total_price(self):
        for record in self:
            record.total_price = record.quantity * record.price_unit

    @api.onchange('amenities_id')
    def _onchange_amenities_id(self):
        if self.amenities_id:
            product = self.env['product.product'].search([('name', '=', self.amenities_id.name)], limit=1)
            if product:
                self.product_id = product.id
                self.price_unit = product.list_price
            else:
                self.product_id = False
                self.price_unit = 0.0

    @api.model
    def create(self, vals):
        if 'product_id' in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            vals['price_unit'] = product.list_price
        
        # Ensure that the room_id is set if not provided
        if 'room_id' not in vals and self.env.context.get('default_room_id'):
            vals['room_id'] = self.env.context['default_room_id']

        return super(HotelRoomAmenities, self).create(vals)

    def write(self, vals):
        if 'product_id' in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            vals['price_unit'] = product.list_price
        
        # Ensure that the room_id is set if not provided
        if 'room_id' not in vals and self.env.context.get('default_room_id'):
            vals['room_id'] = self.env.context['default_room_id']

        return super(HotelRoomAmenities, self).write(vals)
