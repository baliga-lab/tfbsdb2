#!/usr/bin/env python3

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

def export_genes(conn):
    cursor = conn.cursor()
    cursor2 = conn.cursor()
    cursor.execute("select id,entrez_id,description from genes order by entrez_id")
    for gene_id, entrez, desc in cursor.fetchall():
        print("  <doc>")
        print("    <field name=\"id\">GENE:%d</field>" % gene_id)
        print("    <field name=\"names\">%s</field>" % entrez)

        cursor2.execute('select name from gene_synonyms where gene_id=%s order by name', [gene_id])
        for row in cursor2.fetchall():
            print("    <field name=\"names\">%s</field>" % row[0])

        print("    <field name=\"description\">%s</field>" % desc)
        print("  </doc>")

    cursor2.close()
    cursor.close()

def export_motifs(conn):
    cursor = conn.cursor()
    cursor.execute('select m.id,m.name,mdb.name from motifs m join motif_databases mdb on m.motif_database_id=mdb.id order by m.name')
    for motif_id, motif_name, mdb_name in cursor.fetchall():
        print("  <doc>")
        print("    <field name=\"id\">MOTIF:%d</field>" % motif_id)
        print("    <field name=\"names\">%s</field>" % motif_name)
        print("    <field name=\"motif_database\">%s</field>" % mdb_name)
        print("  </doc>")
    cursor.close()


if __name__ == '__main__':
    conn = dbconn()
    print("<add>")
    export_genes(conn)
    export_motifs(conn)
    print("</add>")
