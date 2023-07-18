#!/usr/bin/env python3
import psycopg2
import json

"""
Export TFBS database to JSON
"""

def dbconn():
    conn = psycopg2.connect(database="tfbs",
                        user="dj_ango",
                        password="django")
    return conn

def extract_genes(conn):
    cursor = conn.cursor()
    cursor.execute('select id,name,description,chromosome,start_promoter,stop_promoter,tss,orientation from main_gene order by name')
    genes = []
    gene_map = {}
    for pk, entrez, desc, chrom, start, stop, tss, orient in cursor.fetchall():
        entry = {
            'entrez': int(entrez), 'description': desc, 'chromosome': chrom,
            'start_promoter': start, 'stop_promoter': stop,
            'tss': tss, 'orientation': orient,
            'synonyms': []
        }
        genes.append(entry)
        gene_map[pk] = entry
    cursor.close()
    return gene_map, genes

def add_synonyms(conn, gene_map):
    cursor = conn.cursor()
    cursor.execute('select gene_id, name from main_genesynonyms')
    for gene_id, synonym in cursor.fetchall():
        gene_map[gene_id]['synonyms'].append(synonym)
    cursor.close()

def extract_motifs(conn, gene_map):
    cursor = conn.cursor()
    cursor_inner = conn.cursor()
    cursor.execute('select m.id,m.name,db.name from main_motif m join main_motifdatabase db on m.source_database_id=db.id')
    result = []
    motif_map = {}
    for motif_id,motif_name, db_name in cursor.fetchall():
        cursor_inner.execute('select index,a,c,g,t from main_pssm where motif_id=%s order by index', [motif_id])
        pssm = [{'a': float(a), 'c': float(c), 'g': float(g), 't': float(t)}
                for row,a,c,g,t in cursor_inner.fetchall()]

        cursor_inner.execute('select gene_id from main_gene_motifs where motif_id=%s', [motif_id])
        motif_genes = [gene_map[row[0]]['entrez'] for row in cursor_inner.fetchall()]
        entry = {'motif': motif_name, 'database': db_name, 'pssm': pssm,
                 'genes': sorted(set(motif_genes))}
        motif_map[motif_id] = entry
        result.append(entry)
    cursor.close()
    cursor_inner.close()
    return motif_map, result


def extract_tfbs(conn, gene_map, motif_map):
    result = []
    cursor = conn.cursor()
    cursor.execute('select gene_id,motif_id,start,stop,orientation,p_value,match_sequence from main_tfbs')
    for gene_id,motif_id,start,stop,orient,pval,seq in cursor.fetchall():
        entry = {
            'entrez': gene_map[gene_id]['entrez'], 'motif': motif_map[motif_id]['motif'],
            'start': start, 'stop': stop, 'orientation': orient,
            'p_value': float(pval), 'match_sequence': seq
        }
        result.append(entry)
    cursor.close()
    return result


if __name__ == '__main__':
    conn = dbconn()
    gene_map, genes = extract_genes(conn)
    add_synonyms(conn, gene_map)
    with open('genes.json', 'w') as outfile:
        json.dump(genes, outfile)

    motif_map, motifs = extract_motifs(conn, gene_map)
    with open('motifs.json', 'w') as outfile:
        json.dump(motifs, outfile)

    tfbs = extract_tfbs(conn, gene_map, motif_map)
    with open('tfbs.json', 'w') as outfile:
        json.dump(tfbs, outfile)
    conn.close()
