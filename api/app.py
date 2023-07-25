from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
import mysql.connector

app = Flask(__name__)
app.config.from_envvar('APP_SETTINGS')


def dbconn():
    return mysql.connector.connect(host=app.config['DATABASE_HOST'],
                                   user=app.config['DATABASE_USER'],
                                   password=app.config['DATABASE_PASSWORD'],
                                   database=app.config['DATABASE_NAME'])


@app.route("/motif_info/<name>")
def motif_info(name):
    conn = dbconn()
    cursor = conn.cursor()
    cursor.execute('select m.id,db.name from motifs m join motif_databases db on m.motif_database_id=db.id where m.name=%s', [name])
    motif_id, motif_database = cursor.fetchone()
    cursor.execute('select row_index,a,c,g,t from pssms where motif_id=%s order by row_index', [motif_id])
    pssm = []
    for row_idx, a, c, g, t in cursor.fetchall():
        pssm.append({'a': a, 'c': c, 'g': g, 't': t})

    # target genes
    cursor.execute("""select count(g.id) as num_sites,entrez_id,g.chromosome,start_promoter,stop_promoter,
g.orientation,g.tss from tf_binding_sites tfbs join genes g on tfbs.gene_id=g.id
 where motif_id=%s group by entrez_id""", [motif_id])
    target_genes = []
    for num_sites, entrez, chrom, start_prom, stop_prom, orient, tss in cursor.fetchall():
        target_genes.append({'entrez': entrez, 'num_sites': num_sites,
                             'chromosome': chrom,
                             'start_promoter': start_prom, 'stop_promoter': stop_prom,
                             'orientation': orient,
                             'tss': tss})
    cursor.close()
    conn.close()
    return jsonify(database=motif_database, pssm=pssm, target_genes=target_genes)

@app.route("/summary", methods=["GET"])
def summary():
    conn = dbconn()
    cursor = conn.cursor()
    cursor.execute('select count(*) from genes')
    num_genes = cursor.fetchone()[0]

    cursor.execute('select count(*) from motifs')
    num_motifs = cursor.fetchone()[0]

    cursor.execute('select count(*) from tf_binding_sites')
    num_tfbs = cursor.fetchone()[0]

    cursor.close()
    conn.close()
    return jsonify({
        "num_genes": num_genes, "num_motifs": num_motifs,
        "num_tfbs": num_tfbs
    })

if __name__ == "__main__":
    # Please do not set debug=True in production
    app.run(host="0.0.0.0", port=5000, debug=True)
