import datetime, csv
import pandas as pd

# address_section_zone_only
INDEX_ADDRESS = 3
INDEX_SECTION_ID = 4
INDEX_ZONE_ID = 5
INDEX_MUNICIPIO = 1
INDEX_MUNICIPIO_NOME = 0
INDEX_SG_ESTADO = 2
INDEX_NOME_LOCAL = 6

def index(input_file, output_file):
	with open(input_file, 'r', encoding='utf-8') as f:
		reader = csv.reader(f, delimiter=',', strict=False)
		next(reader)
		replicated_rows = []
		i = 0
		for row in reader:
			endereco = row[INDEX_ADDRESS].strip()
			section = row[INDEX_SECTION_ID]
			zone = row[INDEX_ZONE_ID]
			municipio_id = row[INDEX_MUNICIPIO]
			df = pd.read_csv(output_file, delimiter=';')

			df['address'] = df['address'].map(lambda x: x.strip())
   			
			result = df.loc[(df['address'] == endereco) & (df['zona'] == int(zone)) & (df['seção'] == int(section)) & (df['municipio_id'] == int(municipio_id))]

			if result.empty:
				result = df.loc[(df['address'] == endereco) & (df['zona'] == int(zone)) & (df['municipio_id'] == int(municipio_id))]
				if not result.empty:
					print(f"Address found:\n {row}\n")
					new_row = result.iloc[0].copy()
					new_row['seção'] = section
					replicated_rows.append(new_row.array)
				else:
					bairro = ''
					cep = ''
					lat = 0
					long = 0
					new_row = [row[INDEX_MUNICIPIO_NOME], municipio_id,  row[INDEX_SG_ESTADO],  endereco, bairro, cep, section, zone, lat, long, False, row[INDEX_NOME_LOCAL]]
					print(f"Row not found \n {new_row} \n")
					replicated_rows.append(new_row)
			i +=1
			if i % 1000 == 0:
				print(f"{i} rows processed\n")
			
	f.close()
	with open(output_file, 'a', encoding='utf-8', newline='') as csv_output:
		writer = csv.writer(csv_output, delimiter=';')
		for row in replicated_rows: writer.writerow(row)
	csv_output.close()




input_file = 'data/address_section_zone_only.csv'
output_file = 'data/local_votacao_tratado_BR_2.csv'

startTime = datetime.datetime.now()
print("\nStarted script running\n")

index(input_file, output_file)

print(f"\nFinished script running\nTotal time: {datetime.datetime.now() - startTime}\n")

#python3 manage.py shell < cartpol_app/scripts/neighborhood_database/index.py