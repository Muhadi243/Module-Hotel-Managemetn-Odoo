from odoo import models, fields, api

class HotelServices(models.Model):
    _name = 'hotel_management.services'
    _description = 'Hotel Service'
    
    name = fields.Char(string='Service Name', required=True)
    price = fields.Float(string='Price', required=True)
