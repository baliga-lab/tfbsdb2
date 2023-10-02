#!/usr/bin/env python3

"""
Import TFBSDB data from a PostgresDump in JSON format
"""
import mysql.connector
import os
import json
import glob
import pandas

#DATABASE_HOST = '172.17.0.2'
#DATABASE_USER = 'root'
DATABASE_HOST = 'localhost'
DATABASE_USER = 'tfbsdb2'
DATABASE_PASSWORD = 'tfbsdb2'
DATABASE_NAME = 'tfbsdb2'

def dbconn():
    return mysql.connector.connect(host=DATABASE_HOST,
                                   user=DATABASE_USER,
                                   password=DATABASE_PASSWORD,
                                   database=DATABASE_NAME)


# genes.json  motifs.json  tfbs.json
PATH = '../yaqiao_data/geneHitsDB_humanOnly_with_hitlength/*.csv'

def import_motifhits(conn, path, invalid_motif_file, invalid_genes_file):
    cursor = conn.cursor()
    filename = os.path.basename(path)
    motif_name = filename.replace('fullGenome_motifHits_', '')
    motif_name = motif_name.replace('.csv', '')
    print("Importing hits for motif '%s'..." % motif_name)
    cursor.execute('select id from motifs where name=%s', [motif_name])
    try:
        motif_pk = cursor.fetchone()[0]
    except:
        print("Invalid motif '%s', skipping" % motif_name)
        invalid_motif_file.write('%s\n' % motif_name)
        return
    df = pandas.read_csv(path, header=0)
    for index, row in df.iterrows():
        entrez = row['Entrez ID']
        try:
            entrez = int(entrez)
        except:
            print("Invalid entrez: '%s'" % entrez)
            continue  # skip invalid genes
        promoter = row['Promoter']
        chrom = row['Chr']
        num_instances = row['Instances']
        locations = row['Locations']
        try:
            locations = locations.split(';')
        except AttributeError:
            print("Locations '%s'" % str(locations))
            raise
        strands = row['Strands'].split(';')
        fimo_pvals = row['FIMO P-values']
        try:
            fimo_pvals.split(';')
        except AttributeError:
            print("FIMO pvals: '%s'" % fimo_pvals)
            fimo_pvals = [fimo_pvals]
        match_seqs = row['Matching Sequences'].split(';')

        try:
            cursor.execute('select id from genes where entrez_id=%s', [entrez])
            gene_pk = cursor.fetchone()[0]
            for i in range(num_instances):
                start, stop = locations[i].split('-')
                cursor.execute('insert into tf_binding_sites (gene_id,motif_id,start,stop,orientation,p_value,match_sequence) values (%s,%s,%s,%s,%s,%s,%s)',
                               [gene_pk, motif_pk, start, stop, strands[i], fimo_pvals[i], match_seqs[i]])
        except:
            print("Entrez gene not found: %s" % entrez)
            invalid_genes_file.write('%s\n' % entrez)


if __name__ == '__main__':
    conn = dbconn()
    res = glob.glob(PATH)
    invalid_motif_file = open('invalid_motifs.txt', 'w')
    invalid_genes_file = open('invalid_genes.txt', 'w')
    for path in res:
        import_motifhits(conn, path, invalid_motif_file, invalid_genes_file)
        conn.commit()
    conn.close()
