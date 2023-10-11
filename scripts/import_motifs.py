#!/usr/bin/env python3

"""
Import Yaqiao PSSMs from pkl files based on Chris' PSSM class
"""
import argparse
import pickle
import pssm
import mysql.connector

DATABASE_HOST = 'localhost'
DATABASE_USER = 'tfbsdb2'
DATABASE_PASSWORD = 'tfbsdb2'
DATABASE_NAME = 'tfbsdb2'

def dbconn():
    return mysql.connector.connect(host=DATABASE_HOST,
                                   user=DATABASE_USER,
                                   password=DATABASE_PASSWORD,
                                   database=DATABASE_NAME)


DESCRIPTION = """import_motifs.py - import motifs from pickle files"""

MOTIFDB_IDS = {
    "selex": 1, "jaspar": 2, "uniprobe": 3, "transfac": 4
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=DESCRIPTION)
    parser.add_argument('infile', help='pkl file containing the PSSMS')
    parser.add_argument('dbname', help='database name')
    args = parser.parse_args()
    mdb_id = MOTIFDB_IDS[args.dbname]

    conn = dbconn()
    cursor = conn.cursor()
    cursor_inner = conn.cursor()

    with open(args.infile, 'rb') as infile:
        pssms = pickle.load(infile)
        pssm_names = sorted(pssms.keys())
        for name in pssm_names:
            pssm = pssms[name]
            pssm_name = name.replace('$', '_')  # buggy inconsistent name for transfac
            row_idx = 1
            cursor.execute('insert into motifs (motif_database_id, name) values (%s,%s)', [mdb_id, pssm_name])
            motif_pk = cursor.lastrowid
            print("PSSM '%s' #sites: %s evalue: %s" % (pssm_name, pssm.nsites, pssm.eValue))
            for a,c,g,t in pssm.matrix:
                # ACGT
                #print('%.2f %.2f %.2f %.2f' % (a, c, g, t))
                cursor_inner.execute('insert into pssms (motif_id,row_index,a,c,g,t) values (%s,%s,%s,%s,%s,%s)',
                                     [motif_pk, row_idx, a, c, g, t])
                row_idx += 1
        conn.commit()

    cursor_inner.close()
    cursor.close()
    conn.close()
