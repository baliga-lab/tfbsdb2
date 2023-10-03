from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
import mysql.connector
import requests

app = Flask(__name__)
CORS(app)
app.config.from_envvar('APP_SETTINGS')


def dbconn():
    return mysql.connector.connect(host=app.config['DATABASE_HOST'],
                                   user=app.config['DATABASE_USER'],
                                   password=app.config['DATABASE_PASSWORD'],
                                   database=app.config['DATABASE_NAME'])


@app.route("/info")
def info():
    return jsonify(info="I exist !")

@app.route("/motifs")
def motifs():
    conn = dbconn()
    cursor = conn.cursor()
    cursor.execute('select m.id,m.name,db.name from motifs m join motif_databases db on m.motif_database_id=db.id order by m.name')

    motifs = [{"id": motif_id, "name": motif_name, "db": motif_db} for motif_id, motif_name, motif_db in cursor.fetchall()]
    return jsonify(motifs=motifs)


@app.route("/genes")
def genes():
    conn = dbconn()
    cursor = conn.cursor()
    cursor.execute('select g.id,s.name,entrez_id,description,chromosome,start_promoter,stop_promoter,tss,orientation from genes g join gene_synonyms s on s.gene_id=g.id order by entrez_id')

    genes = [{
        "id": gene_id,
        "synonyms": synonyms,
        "entrez": entrez,
        "description": desc,
        "chromosome": chrom,
        "start_promoter": start_prom,
        "stop_promoter": stop_prom,
        "tss": tss,
        "strand": strand
    } for gene_id, synonyms,entrez, desc, chrom, start_prom, stop_prom, tss, strand in cursor.fetchall()]
    return jsonify(genes=genes)

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
                             'strand': orient,
                             'tss': tss})
    cursor.close()
    conn.close()
    return jsonify(database=motif_database, pssm=pssm, target_genes=target_genes)


@app.route("/gene_info/<gene_id>")
def gene_info(gene_id):
    conn = dbconn()
    cursor = conn.cursor()
    cursor.execute("""select entrez_id,chromosome,start_promoter,stop_promoter,orientation,tss,description
from genes where id=%s""", [gene_id])
    entrez, chrom, start_prom, stop_prom, orient, tss, desc = cursor.fetchone()

    synonyms = []
    cursor.execute('select name,synonym_type from gene_synonyms where gene_id=%s', [gene_id])
    for name, syn_type in cursor.fetchall():
        synonyms.append({'name': name, 'type': syn_type})
    cursor.close()
    conn.close()
    return jsonify(entrez=entrez, chromosome=chrom, start_promoter=start_prom,
                   stop_promoter=stop_prom, orientation=orient, tss=tss,
                   description=desc, synonyms=synonyms)


@app.route("/motif_shortinfo/<motif_id>")
def motif_shortinfo(motif_id):
    conn = dbconn()
    cursor = conn.cursor()
    cursor.execute("""select m.name as motif_name, mdb.name as db_name from motifs m join motif_databases mdb on m.motif_database_id=mdb.id where m.id=%s""", [motif_id])
    motif_name, motif_database = cursor.fetchone()

    cursor.close()
    conn.close()
    return jsonify(motif_name=motif_name, motif_database=motif_database)


@app.route("/gene_tf_binding_sites/<gene_id>")
def gene_tf_binding_sites(gene_id):
    conn = dbconn()
    cursor = conn.cursor()
    # TF binding sites
    cursor.execute("""select m.id,m.name,mdb.name,start,stop,orientation,p_value,match_sequence
from tf_binding_sites tfbs join motifs m on tfbs.motif_id=m.id
join motif_databases mdb on m.motif_database_id=mdb.id
where gene_id=%s order by m.name""", [gene_id])
    binding_sites = []
    for motif_id, motif, motif_db, start, stop, orient, pval, seq in cursor.fetchall():
        binding_sites.append({
            "motif_id": motif_id,
            "motif": motif, "motif_database": motif_db,
            "start": start, "stop": stop, "strand": orient,
            "p_value": pval, "match_sequence": seq
        })
    cursor.close()
    conn.close()
    return jsonify(tf_binding_sites=binding_sites)


@app.route("/motif_target_genes/<motif_id>")
def motif_target_genes(motif_id):
    conn = dbconn()
    cursor = conn.cursor()
    cursor.execute("""select distinct g.id,g.entrez_id,g.description,g.chromosome,g.orientation,g.start_promoter,g.stop_promoter,g.tss,count(tfbs.id) from genes g join tf_binding_sites tfbs on g.id=tfbs.gene_id join motifs m on m.id=tfbs.motif_id where m.id=%s group by g.id order by g.entrez_id""", [motif_id])
    target_genes = []
    for gene_id, entrez, desc, chrom, strand, prom_start, prom_stop, tss, num_sites in cursor.fetchall():
        target_genes.append({
            "gene_id": gene_id,
            "entrez_id": entrez, "description": desc,
            "chromosome": chrom, "strand": strand,
            "promoter_start": prom_start, "promoter_stop": prom_stop,
            "tss": tss, "num_sites": num_sites
        })
    cursor.close()
    conn.close()
    return jsonify(target_genes=target_genes)


@app.route("/motif_tfs/<motif_id>")
def motif_tfs(motif_id):
    conn = dbconn()
    cursor = conn.cursor()
    cursor_inner = conn.cursor()
    cursor.execute("""select distinct g.id,g.entrez_id,g.description,g.chromosome,g.orientation,g.start_promoter,g.stop_promoter,g.tss from genes g join gene_motifs gm on g.id=gm.gene_id join motifs m on m.id=gm.motif_id where m.id=%s""", [motif_id])
    tfs = []
    for gene_id, entrez, desc, chrom, strand, prom_start, prom_stop, tss in cursor.fetchall():
        cursor_inner.execute('select name from gene_synonyms where gene_id=%s', [gene_id])
        synonyms = [row[0] for row in cursor.fetchall()]
        tfs.append({
            "gene_id": gene_id,
            "synonyms": ', '.join(synonyms),
            "entrez_id": entrez, "description": desc,
            "chromosome": chrom, "strand": strand,
            "promoter_start": prom_start, "promoter_stop": prom_stop,
            "tss": tss
        })
    cursor.close()
    conn.close()
    return jsonify(tfs=tfs)

@app.route("/motif_pssm/<motif_id>")
def motif_pssm(motif_id):
    conn = dbconn()
    cursor = conn.cursor()
    cursor.execute("""select row_index,a,c,g,t from pssms where motif_id=%s order by row_index""", [motif_id])
    pssm_rows = []
    for row_index, a, c, g, t in cursor.fetchall():
        pssm_rows.append({
            "row_index": row_index,
            "a": a, "c": c, "g": g, "t": t
        })
    cursor.close()
    conn.close()
    return jsonify(pssm=pssm_rows)


@app.route('/search/<term>')
def simple_search(term):
    solr_url = app.config['SOLR_QUERY_URL']
    solr_url += '?q=names:%s*' % term
    print("QUERY: " + solr_url)
    r = requests.get(solr_url)
    solr_result = r.json()
    total = solr_result['response']['numFound']
    start = solr_result['response']['start']
    solr_docs = solr_result['response']['docs']
    result = []
    for doc in solr_docs:
        doc_id = doc['id']
        names = doc['names']
        # optional items
        try:
            description = doc['description']
        except:
            description = ''
        try:
            motif_db = doc['motif_database']
        except:
            motif_db = ''

        result.append({
            'id': doc_id,
            'names': names,
            'description': description,
            'motif_database': motif_db
        })

    return jsonify(results=result, num_results=len(result), total=total, start=start)


@app.route('/completions/<search_term>')
def autocomplete(search_term):
    solr_url = app.config['SOLR_SUGGEST_URL']
    solr_url += 'suggest.q=' + search_term
    print(solr_url)
    r = requests.get(solr_url)
    solr_result = r.json()
    suggest_result = solr_result['suggest']['mySuggester'][search_term]
    entries = []
    terms_set = set()
    for s in suggest_result['suggestions']:
        term = s['term']
        terms = term.split(',')
        for t in terms:
            terms_set.add(t)
    count = len(terms_set)
    return jsonify(count=count, completions=sorted(terms_set))


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
