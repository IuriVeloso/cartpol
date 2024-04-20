from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Spacer
from reportlab.platypus.tables import Table, TableStyle, colors
from functools import partial


from cartpol_app.scripts.report.template_generate import report_template

#c = canvas.Canvas(path, pagesize=A4)
#c = report_template(c, 'Joao do Bras', True)

# c.setFillColorRGB(0,0,0)
# c.setFont('Helvetica', 20)	

# c.showPage()
# c.save()

def run_report(data, path, politician_name, has_markdown=True):
    
	if politician_name == None:
		raise ValueError('Politician name is required')
	
	if data == None:
		raise ValueError('Data is required')

	basic_data = [['Bairro','Votos','Dispersão', 'Concentração','Dominância']]
 
	full_data = basic_data + data

	my_doc = SimpleDocTemplate(path, pagesize=A4)

	columns_width = [60*mm,20*mm,30*mm,35*mm,40*mm]

	t = Table(full_data, rowHeights=10*mm, repeatRows=1, 
			colWidths=columns_width)

	t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgreen), 
						('FONTSIZE',(0,0),(-1,-1), 14),
						('VALIGN',(0,0),(-1,-1),'MIDDLE'),]))

	elements = [Spacer(0*mm, 40*mm)]
	elements.append(t)

	my_doc.build(elements, onFirstPage=partial(report_template, politician_name=politician_name, has_markdown=has_markdown))
