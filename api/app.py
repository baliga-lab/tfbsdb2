from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
import mysql.connector
import requests

app = Flask(__name__)
app.config.from_envvar('APP_SETTINGS')


def dbconn():
    return mysql.connector.connect(host=app.config['DATABASE_HOST'],
                                   user=app.config['DATABASE_USER'],
                                   password=app.config['DATABASE_PASSWORD'],
                                   database=app.config['DATABASE_NAME'])


@app.route("/motifs")
def motifs():
    conn = dbconn()
    cursor = conn.cursor()
    cursor.execute('select m.name,db.name from motifs m join motif_databases db on m.motif_database_id=db.id order by m.name')

    motifs = [{"name": motif_name, "db": motif_db} for motif_name, motif_db in cursor.fetchall()]
    return jsonify(motifs=motifs)


@app.route("/genes")
def genes():
    conn = dbconn()
    cursor = conn.cursor()
    cursor.execute('select entrez_id,description,chromosome,start_promoter,stop_promoter,tss,orientation from genes order by entrez_id')

    genes = [{
        "entrez": entrez,
        "description": desc,
        "chromosome": chrom,
        "start_promoter": start_prom,
        "stop_promoter": stop_prom,
        "tss": tss,
        "strand": strand
    } for entrez, desc, chrom, start_prom, stop_prom, tss, strand in cursor.fetchall()]
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
                             'strang': orient,
                             'tss': tss})
    cursor.close()
    conn.close()
    return jsonify(database=motif_database, pssm=pssm, target_genes=target_genes)


@app.route("/gene_info/<entrez>")
def gene_info(entrez):
    conn = dbconn()
    cursor = conn.cursor()
    cursor.execute("""select id,chromosome,start_promoter,stop_promoter,orientation,tss,description
from genes where entrez_id=%s""", [entrez])
    gene_pk, chrom, start_prom, stop_prom, orient, tss, desc = cursor.fetchone()

    synonyms = []
    cursor.execute('select name,synonym_type from gene_synonyms where gene_id=%s', [gene_pk])
    for name, syn_type in cursor.fetchall():
        synonyms.append({'name': name, 'type': syn_type})

    # TF binding sites
    cursor.execute("""select m.name,mdb.name,start,stop,orientation,p_value,match_sequence
from tf_binding_sites tfbs join motifs m on tfbs.motif_id=m.id
join motif_databases mdb on m.motif_database_id=mdb.id
where gene_id=%s order by m.name""", [gene_pk])
    binding_sites = []
    for motif, motif_db, start, stop, orient, pval, seq in cursor.fetchall():
        binding_sites.append({
            "motif": motif, "motif_database": motif_db,
            "start": start, "stop": stop, "strand": orient,
            "p_value": pval, "match_sequence": seq
        })
    cursor.close()
    conn.close()
    return jsonify(entrez=entrez, chromosome=chrom, start_promoter=start_prom,
                   stop_promoter=stop_prom, orientation=orient, tss=tss,
                   description=desc, synonyms=synonyms, tf_binding_sites=binding_sites)


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


@app.route('/autocomplete/<search_term>')
def autocomplete(search_term):
    """
    http://localhost:8983/solr/halodata/suggest?suggest=true&suggest.build=true&suggest.dictionary=mySuggester&wt=json&suggest.q=VNG000    """
    solr_url = app.config['SOLR_SUGGEST_URL']
    solr_url += 'suggest.q=' + search_term
    print(solr_url)
    r = requests.get(solr_url)
    solr_result = r.json()
    suggest_result = solr_result['suggest']['mySuggester'][search_term]
    #count = suggest_result['num_found']
    entries = []
    terms_set = set()
    for s in suggest_result['suggestions']:
        term = s['term']
        terms = term.split(',')
        for t in terms:
            terms_set.add(t)
    entries = [{'Description': t} for t in sorted(terms_set)]
    count = len(entries)
    return jsonify(count=count, entries=entries)


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
