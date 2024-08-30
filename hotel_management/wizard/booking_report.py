from odoo import models, fields, api
import xlsxwriter
import base64
from io import BytesIO

class RoomBookingDetail(models.TransientModel):
    _name = 'room.booking.detail'
    _description = 'Reporting Wizard'

    room_id = fields.Many2one('hotel_management.room', string="Room", required=True)
    customer = fields.Many2one('res.partner', string="Guest Name") 
    check_in = fields.Date(string="Check In", required=True)
    check_out = fields.Date(string="Check Out", required=True)
    name = fields.Char(string="Reservation Name")
    file_data = fields.Binary(string="File Data", readonly=True)
    file_name = fields.Char(string="File Name", readonly=True)

    # def action_room_booking_pdf(self):
    #     # Implement your PDF report generation logic here
    #     return self.action_generate_report()

    def action_room_booking_excel(self):
        return self.action_export_excel()

    def action_export_excel(self):
        domain = []

        # Apply filtering based on the room, customer, and reservation name
        if self.room_id:
            domain.append(('reservation_line_ids.room_id', '=', self.room_id.id))
        if self.customer:
            domain.append(('customer_ids', '=', self.customer.id))
        if self.name:
            domain.append(('name', 'ilike', self.name))

        # Filter based on the range between check_in and check_out
        if self.check_in and self.check_out:
            domain.extend([
                '|',  # OR condition
                '&', ('reservation_line_ids.check_in', '<=', self.check_out), ('reservation_line_ids.check_in', '>=', self.check_in),  # Condition 1
                '&', ('reservation_line_ids.check_out', '>=', self.check_in), ('reservation_line_ids.check_out', '<=', self.check_out)  # Condition 2
            ])

        # Search for reservations based on the domain
        reservations = self.env['hotel_management.reservation'].search(domain)

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        headers = ['No', 'Guest Name', 'Room', 'Check In', 'Check Out', 'Reservation Reference']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        for row_num, reservation in enumerate(reservations, start=1):
            for line in reservation.reservation_line_ids:
                worksheet.write(row_num, 0, row_num)  # No column
                worksheet.write(row_num, 1, reservation.customer_ids.name if reservation.customer_ids else '')  # Guest Name
                worksheet.write(row_num, 2, line.room_id.name if line.room_id else '')  # Room
                worksheet.write(row_num, 3, line.check_in.strftime('%Y-%m-%d') if line.check_in else '')  # Check In
                worksheet.write(row_num, 4, line.check_out.strftime('%Y-%m-%d') if line.check_out else '')  # Check Out
                worksheet.write(row_num, 5, reservation.name if reservation.name else '')  # Reservation Reference

        workbook.close()

        output.seek(0)
        file_data = base64.b64encode(output.read())
        output.close()

        self.write({
            'file_data': file_data,
            'file_name': "room_booking_report.xlsx"
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model={self._name}&id={self.id}&field=file_data&filename_field=file_name&download=true',
            'target': 'new',
        }




    # def action_generate_report(self):
    #     domain = []

    #     if self.room_id:
    #         domain.append(('reservation_line_ids.room_id', '=', self.room_id.id))
    #     if self.customer:
    #         domain.append(('customer_ids', '=', self.customer.id))
    #     if self.name:
    #         domain.append(('name', 'ilike', self.name))
    #     if self.check_in and self.check_out:
    #         domain.append('|')
    #         domain.append('&')
    #         domain.append(('reservation_line_ids.check_in', '<=', self.check_out))
    #         domain.append(('reservation_line_ids.check_out', '>=', self.check_in))
    #         domain.append('&')
    #         domain.append(('reservation_line_ids.check_in', '>=', self.check_in))
    #         domain.append(('reservation_line_ids.check_out', '<=', self.check_out))

    #     # Search for reservations based on the domain
    #     reservations = self.env['hotel_management.reservation'].search(domain)

    #     # Get the reservation lines
    #     reservation_lines = []
    #     for reservation in reservations:
    #         for line in reservation.reservation_line_ids:
    #             reservation_lines.append({
    #                 'room_id': line.room_id.name or '',
    #                 'customer': reservation.customer_ids.name or '',
    #                 'check_in': line.check_in.strftime('%Y-%m-%d') if line.check_in else '',
    #                 'check_out': line.check_out.strftime('%Y-%m-%d') if line.check_out else '',
    #                 'name': reservation.name or '',
    #             })


    #     data = {
    #         'docs': reservation_lines,  # Pass reservation lines instead of reservations
    #         'room_id': self.room_id.name if self.room_id else '',
    #         'customer': self.customer.name if self.customer else '',
    #         'check_in': self.check_in,
    #         'check_out': self.check_out,
    #         'name': self.name,
    #     }

    #     return self.env.ref('hotel_management.action_report_pdf_template').report_action(self, data=data)


    def action_room_booking_pdf(self):
        """Button action_room_booking_pdf function"""
        data = {
            "booking": self.generate_data(),
        }
        return self.env.ref(
            "hotel_management.action_report_room_booking"
        ).report_action(self, data=data)



    def generate_data(self):
        """Generate data to be printed in the report"""
        domain = []
        room_list = []
        
        # Validasi tanggal
        if self.check_in and self.check_out:
            if self.check_in > self.check_out:
                raise ValidationError(
                    _("Check-in date should be less than Check-out date")
                )
        if self.check_in:
            domain.append(('reservation_line_ids.check_in', '>=', self.check_in))
        if self.check_out:
            domain.append(('reservation_line_ids.check_out', '<=', self.check_out))
        
        # Tambahkan filter berdasarkan room_id jika ada
        if self.room_id:
            domain.append(('reservation_line_ids.room_id', '=', self.room_id.id))

        # Cari data berdasarkan domain
        reservations = self.env['hotel_management.reservation'].search(domain)
        
        # Ambil data reservation lines
        for reservation in reservations:
            for line in reservation.reservation_line_ids:
                room_list.append({
                    'room_id': line.room_id.name if line.room_id else '',
                    'customer': reservation.customer_ids.name if reservation.customer_ids else '',
                    'check_in': line.check_in.strftime('%Y-%m-%d') if line.check_in else '',
                    'check_out': line.check_out.strftime('%Y-%m-%d') if line.check_out else '',
                    'name': reservation.name or '',
                })
        
        return room_list
