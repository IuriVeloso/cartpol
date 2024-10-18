from functools import partial

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.platypus.tables import Table, TableStyle, colors

from cartpol_app.scripts.report.template_generate import report_template

# c = canvas.Canvas(path, pagesize=A4)
# c = report_template(c, 'Joao do Bras', True)

# c.setFillColorRGB(0,0,0)
# c.setFont('Helvetica', 20)

# c.showPage()
# c.save()


def run_report(data, path, politician_name, political_code, has_markdown=True):
    sample_style_sheet = getSampleStyleSheet()

    if politician_name == None:
        raise ValueError('Politician name is required')

    if data == None:
        raise ValueError('Data is required')

    basic_data = [['Bairro', 'Votos', 'RCAN_UESP', 'RUESP_CAN', 'RUESP']]

    full_data = basic_data + data

    rcan_uesp_data = basic_data + \
        sorted(data, reverse=True, key=lambda e: e[2])[:5]
    ruesp_can_data = basic_data + \
        sorted(data, reverse=True, key=lambda e: e[3])[:5]

    my_doc = SimpleDocTemplate(path, pagesize=A4)

    columns_width = [60*mm, 20*mm, 40*mm, 40*mm, 30*mm]

    t = Table(full_data, rowHeights=10*mm, repeatRows=1,
              colWidths=columns_width)

    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                           ('FONTSIZE', (0, 0), (-1, -1), 14),
                           ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),]))

    t2 = Table(rcan_uesp_data, rowHeights=10*mm, repeatRows=1,
               colWidths=columns_width)

    t2.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                            ('FONTSIZE', (0, 0), (-1, -1), 14),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),]))

    t3 = Table(ruesp_can_data, rowHeights=10*mm, repeatRows=1,
               colWidths=columns_width)

    t3.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                            ('FONTSIZE', (0, 0), (-1, -1), 14),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),]))

    text_top15RCAN = Paragraph("TOP 5 RCAN_UESPs do candidato",
                               sample_style_sheet['Heading1'])
    text_top15RUESP_CAN = Paragraph("TOP 5 RUESP_CANs do candidato",
                                    sample_style_sheet['Heading1'])
    text_todosOsBairros = Paragraph(
        "Todos os bairros",
        sample_style_sheet['Heading1']
    )

    espaco_s = Spacer(0*mm, 5*mm)
    espaco_m = Spacer(0*mm, 20*mm)
    espaco_g = Spacer(0*mm, 40*mm)

    elements = [espaco_g, espaco_g, espaco_g, text_top15RCAN, espaco_s, t2, espaco_m, text_top15RUESP_CAN, espaco_s,
                t3,  espaco_m, text_todosOsBairros, espaco_s, t]

    my_doc.build(elements, onFirstPage=partial(report_template,
                                               politician_name=politician_name, political_code=political_code, has_markdown=has_markdown))
