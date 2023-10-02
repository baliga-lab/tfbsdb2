#!/usr/bin/env python3

if __name__ == '__main__':
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


PATH = '../yaqiao_data/CorrespondenceTable_from_Motifs_to_TFs.tsv'


if __name__ == '__main__':
    df = pandas.read_csv(PATH, sep='\t', header=None)
    #print(df)
    conn = dbconn()
    cursor = conn.cursor()
    motif_cache = {}
    gene_cache = {}
    for index, row in df.iterrows():
        motif, gene = row
        if motif not in motif_cache:
            cursor.execute('select id from motifs where name=%s', [motif])
            try:
                motif_id = cursor.fetchone()[0]
                motif_cache[motif] = motif_id
            except TypeError:
                continue  # gene not found
        motif_id = motif_cache[motif]
        if gene not in gene_cache:
            cursor.execute('select g.id from genes g join gene_synonyms s on g.id=s.gene_id where s.name=%s', [gene])
            try:
                gene_id = cursor.fetchone()[0]
                gene_cache[gene] = gene_id
            except TypeError:
                continue  # gene not found
        gene_id = gene_cache[gene]
        cursor.execute('insert into gene_motifs (gene_id,motif_id) values (%s,%s)', [gene_id, motif_id])
    conn.commit()
