import csv, re

def replicar_linhas_com_range(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as csv_input:
        reader = csv.reader(csv_input, delimiter=';')
        rows = list(reader)

    # Criar uma lista para armazenar as linhas replicadas
    replicated_rows = []

    for row in rows:
        
        sections_id = row[-2].split(";")
        sections = []
        for item in sections_id:
            matches = re.findall(r'\b\d+(?:(?=ª)|\b)', item)
            print(matches, sections_id)
            if(len(matches) == 0):
                continue
            if (len(matches) == 1):
                sections.append(int(matches[0]))
            else:
                for i in range(int(matches[0]), int(matches[1]) + 1):
                    sections.append(i)    

        # Criar um range de 1 a replication_factor+1 e substituir a última coluna da linha
        for i in sections:
            modified_row = row[:-2] + [str(i)]
            replicated_rows.append(modified_row)

    # Escrever as linhas replicadas na nova planilha CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as csv_output:
        writer = csv.writer(csv_output, delimiter=';')
        writer.writerows(replicated_rows)

# Exemplo de uso
input_file = 'locaisSP 2.csv'
output_file = 'locaisSP_2_com_secoes_separadas.csv'
replicar_linhas_com_range(input_file, output_file)