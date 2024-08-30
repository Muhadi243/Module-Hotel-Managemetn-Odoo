from odoo import fields, models, api

class HotelFloor(models.Model):
    _name = "hotel_management.floor"
    _description = "Hotel Floor"
    
    name = fields.Char(string="Floor")
    manager_ids = fields.Many2one("res.partner", string="Manager")
