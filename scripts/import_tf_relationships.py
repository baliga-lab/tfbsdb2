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


PATH = '../yaqiao_data/reformated_geneHitsDB_humanOnly_with_hitlength.csv'

if __name__ == '__main__':
    df = pandas.read_csv(PATH, sep=',')
    motif_ids = {}
    gene_ids = {}
    conn = dbconn()
    cursor = conn.cursor()
    cursor.execute('select gene_id,name from gene_synonyms')
    for gene_id, gene_name in cursor.fetchall():
        gene_ids[gene_name] = gene_id
    cursor.execute('select id,entrez_id from genes')
    for gene_id, entrez in cursor.fetchall():
        gene_ids[str(entrez)] = gene_id

    cursor.execute('select id,name from motifs')
    for motif_id, motif_name in cursor.fetchall():
        motif_ids[motif_name] = motif_id

    missing_genes = set()
    missing_tfs = set()

    success = 0
    tfs_found = 0
    target_genes_found = 0
    for index, row in df.iterrows():
        tf = row['TF']  # a gene name
        target_gene = str(row['TargetGene'])  # an entrez id
        motif_name = row['MotifName']  # a name
        motif_db = row['MotifDb']  # ignore

        if tf not in gene_ids:
            missing_tfs.add(tf)
            continue
        tfs_found += 1
        tf_id = gene_ids[tf]

        if target_gene not in gene_ids:
            missing_genes.add(target_gene)
            continue
        target_genes_found += 1
        target_gene_id = gene_ids[target_gene]

        motif_id = motif_ids[motif_name]

        # 1. import tf to target gene
        cursor.execute('select count(*) from tf_to_target_gene where tf_id=%s and target_gene_id=%s',
                       [tf_id, target_gene_id])
        if cursor.fetchone()[0] == 0:  # insert new
            cursor.execute('insert into tf_to_target_gene (tf_id,target_gene_id) values (%s,%s)',
                           [tf_id, target_gene_id])

        # 2. import tf binding sites
        # multiple, semicolon separated hits
        strands = row['Strand'].split(';')
        locations = row['Location'].split(';')
        fimo_pvals = row['p-value'].split(';')
        match_seqs = row['MatchSequence'].split(';')
        num_instances = len(locations)
        for i in range(num_instances):
            start, stop = locations[i].split('-')
            cursor.execute('insert into tf_binding_sites (gene_id,motif_id,start,stop,orientation,p_value,match_sequence) values (%s,%s,%s,%s,%s,%s,%s)',
                           [gene_id, motif_id, start, stop, strands[i], fimo_pvals[i], match_seqs[i]])
        #success += 1
    conn.commit()

    """
    print('successful hits: %d tfs found: %d (missing: %d) target genes: %d (missing: %d)' % (success,
                                                                                              tfs_found,
                                                                                              len(missing_tfs),
                                                                                              target_genes_found,
                                                                                              len(missing_genes)))"""
    with open('missing_genes.txt', 'w') as outfile:
        for gene in missing_genes:
            outfile.write('%s\n' % gene)
    with open('missing_tfs.txt', 'w') as outfile:
        for tf in missing_tfs:
            outfile.write('%s\n' % tf)
