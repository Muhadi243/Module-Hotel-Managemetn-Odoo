from odoo import models, fields, api

class HotelAmenities(models.Model):
    _name = 'hotel_management.amenities'
    _description = 'Hotel Amenities'

    name = fields.Char(string='Amenities Name', required=True)
    icon = fields.Binary(string='Icon')
    product_id = fields.Many2one('product.product', string='Related Product')
    product_name = fields.Char(string='Product Name')  # Field untuk nama produk
    list_price = fields.Float(string='List Price', help="The price of the amenity", compute='_compute_list_price', store=True)

    @api.depends('product_id')
    def _compute_list_price(self):
        for record in self:
            record.list_price = record.product_id.list_price if record.product_id else 100

    @api.model
    def create(self, vals):
        if 'product_name' in vals:
            # Cari produk berdasarkan nama
            product = self.env['product.product'].search([('name', '=', vals['product_name'])], limit=1)
            if product:
                vals['product_id'] = product.id
                # Hapus 'product_name' dari vals untuk menghindari penulisan di database
                vals.pop('product_name')

        # Buat record Hotel Amenity
        res = super(HotelAmenities, self).create(vals)
        
        # Jika tidak ada product_id yang terisi, buat produk baru
        if not res.product_id and res.product_name:
            product_vals = {
                'name': res.product_name,
                'type': 'service',
                'uom_id': self.env.ref('uom.product_uom_unit').id,  # Asumsikan 'uom.product_uom_unit' ada
                'uom_po_id': self.env.ref('uom.product_uom_unit').id,  # Asumsikan 'uom.product_uom_unit' ada
                'image_1920': res.icon,
            }
            product = self.env['product.product'].create(product_vals)
            res.write({'product_id': product.id})

        # Pastikan list_price dihitung setelah product_id diupdate
        res._compute_list_price()

        return res
