#!/usr/bin/env python3

import mysql.connector
import os
import json

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

def import_genes(conn, path):
    with open(path) as infile:
        genes = json.load(infile)
    cursor = conn.cursor()
    cursor_inner = conn.cursor()
    for gene in genes:
        cursor.execute('insert into genes (entrez_id,description,chromosome,start_promoter,stop_promoter,tss,orientation) values (%s,%s,%s,%s,%s,%s,%s)', [gene['entrez'], gene['description'],
                                                                                                                                                    gene['chromosome'], gene['start_promoter'], gene['stop_promoter'],
                                                                                                                                                    gene['tss'], gene['orientation'] ])
        gene_pk = cursor.lastrowid
        for synonym in gene['synonyms']:
            cursor_inner.execute('insert into gene_synonyms (gene_id,name,synonym_type) values (%s,%s,%s)',
                                 [gene_pk, synonym, "hgnc"])
    cursor.close()
    cursor_inner.close()
    conn.commit()


def import_motifs(conn, path):
    cursor = conn.cursor()
    cursor_inner = conn.cursor()
    dbmap = {}

    with open(path) as infile:
        motifs = json.load(infile)
        motif_dbs = set()
        for motif in motifs:
            motif_dbs.add(motif['database'])
        # add to database
        for motif_db in motif_dbs:
            cursor.execute('insert into motif_databases (name) values (%s)', [motif_db])
            db_pk = cursor.lastrowid
            dbmap[motif_db] = db_pk

        for motif in motifs:
            motif_name = motif['motif']
            db_pk = dbmap[motif['database']]
            cursor.execute('select count(*) from motifs where name=%s', [motif_name])
            num_existing = cursor.fetchone()[0]
            if num_existing > 0:
                # There are 2 motifs that exists with the same name, but different case
                cursor.execute('select id from motifs where name=%s', [motif_name])
                motif_pk = cursor.fetchone()[0]
            else:
                cursor.execute('insert into motifs (motif_database_id,name) values (%s,%s)', [db_pk, motif_name])
                motif_pk = cursor.lastrowid
            pssm = motif['pssm']

            for row_num, row in enumerate(pssm):
                cursor_inner.execute('insert into pssms (motif_id,row_index,a,c,g,t) values (%s,%s,%s,%s,%s,%s)',
                                     [motif_pk, row_num + 1, row['a'], row['c'], row['g'], row['t']])

    conn.commit()
    cursor.close()
    cursor_inner.close()


def import_tfbs(conn, path):
    cursor = conn.cursor()
    gene_map = {}
    motif_map = {}
    with open(path) as infile:
        tfbs = json.load(infile)
        for site in tfbs:
            entrez = site['entrez']
            if entrez not in gene_map:
                cursor.execute('select id from genes where entrez_id=%s', [entrez])
                gene_id = cursor.fetchone()[0]
                gene_map[entrez] = gene_id
            else:
                gene_id = gene_map[entrez]
            motif = site['motif']
            if motif not in motif_map:
                cursor.execute('select id from motifs where name=%s', [motif])
                for row in cursor.fetchall():  # DANGER: MOTIFS MIGHT NOT BE UNIQUE !!!!
                    motif_id = row[0]
                motif_map[motif] = motif_id
            else:
                motif_id = motif_map[motif]

            cursor.execute('insert into tf_binding_sites (gene_id,motif_id,start,stop,orientation,p_value,match_sequence) values (%s,%s,%s,%s,%s,%s,%s)', [gene_id, motif_id, site['start'], site['stop'],
                                                                                                                                                           site['orientation'], site['p_value'], site['match_sequence']])
    conn.commit()
    cursor.close()

# genes.json  motifs.json  tfbs.json
FOLDER = '../legacy_data'
if __name__ == '__main__':
    conn = dbconn()
    import_genes(conn, os.path.join(FOLDER, 'genes.json'))
    import_motifs(conn, os.path.join(FOLDER, 'motifs.json'))
    import_tfbs(conn, os.path.join(FOLDER, 'tfbs.json'))
    conn.close()
