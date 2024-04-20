from reportlab.lib.units import mm

path='/Users/iuri.felix/TCC/cartpol/myfile.pdf'

def report_template(c, _doc, politician_name = 'Politico Z', has_markdown = True):
	c.saveState()
 
	print(_doc)
 
	c.translate(mm, mm)
	c.setStrokeColorRGB(0,1,0)
	c.setLineWidth(5)
	c.line(10*mm, 250*mm, 200*mm, 250*mm)
 
	if has_markdown:
		c.rotate(45)
		c.setFillColorCMYK(0,0,0,0.08)
		c.setFont('Helvetica', 100)
		c.drawString(140*mm, 40*mm, 'CartPol')
		c.rotate(-45)

	# c.setFillColorCMYK(.2,.2,0,.39)
	c.setFillColorRGB(0,0,0)
	# c.setFillColor('lightgreen')
	c.setFont('Helvetica', 12)
	c.drawString(10*mm, 240*mm, 'Candidato:')
	c.setFont('Helvetica-Bold', 24)	
	c.drawString(35*mm, 240*mm, politician_name)

	# Creating a rectangle
 	# c.setLineWidth(10)
	# c.setStrokeColor('yellow')
	# c.setFillColor('lightgreen')
	# c.rect(50*mm,85*mm,100*mm,185*mm, fill=1)
  
	c.restoreState()
    