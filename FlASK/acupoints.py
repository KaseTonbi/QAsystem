# TODO 该文件是可以正常使用的
#!/usr/bin/env python
import os
from json import dumps
import logging
from dotenv import load_dotenv, find_dotenv

from flask import Flask, g, Response, request
from neo4j import GraphDatabase, basic_auth

load_dotenv(find_dotenv())

app = Flask(__name__, static_url_path='/static/')

url = os.getenv("NEO4J_URI", "bolt://localhost:7687")
username = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "0407zccui")
neo4jVersion = os.getenv("NEO4J_VERSION", "5")
database = os.getenv("NEO4J_DATABASE", "neo4j")

port = os.getenv("PORT", 5059)

# driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j","0407zccui")) # 认证连接数据库
driver = GraphDatabase.driver(url, auth=basic_auth(username, password))

# def get_db():
#     if not hasattr(g, 'neo4j'):
#             g.neo4j_db = driver.session()
#     return g.neo4j_db

def get_db():
    if not hasattr(g, 'neo4j'):
        if neo4jVersion.startswith("5"):
            g.neo4j_db = driver.session(database=database)
        else:
            g.neo4j_db = driver.session()
    return g.neo4j_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'neo4j'):
        g.neo4j_db.close()


@app.route("/")
def get_index():
    return app.send_static_file('qureyindex.html')


def serialize_acupoint(acupoint):
    return {
        'id': acupoint['id'],
        'name': acupoint['name'],
        'position': acupoint['position']
    }


def serialize_disease(disease):
    return {
        'name': disease['name'],
    }


@app.route("/graph")
def get_graph():
    db = get_db()
    results = db.read_transaction(lambda tx: list(tx.run("MATCH (m:Acupoint)<-[:treat_point]-(a:Disease) "
                                                         "RETURN m.name as acupoint, collect(a.name) as disease "
                                                         "LIMIT $limit", {
                                                             "limit": request.args.get("limit",
                                                                                       100)})))
    nodes = []
    rels = []
    i = 0
    for record in results:
        nodes.append({"title": record["acupoint"], "label": "acupoint"})
        target = i
        i += 1
        for name in record['disease']:
            actor = {"title": name, "label": "actor"}
            try:
                source = nodes.index(actor)
            except ValueError:
                nodes.append(actor)
                source = i
                i += 1
            rels.append({"source": source, "target": target})
    return Response(dumps({"nodes": nodes, "links": rels}),
                    mimetype="application/json")


@app.route("/search")
def get_search():
    try:
        q = request.args["q"]
    except KeyError:
        return []
    else:
        db = get_db()
        results = db.read_transaction(lambda tx: list(tx.run("MATCH (acupoint:Acupoint) "
                                                             "WHERE acupoint.name =~ $name "
                                                             "RETURN acupoint", {"name": "(?i).*" + q + ".*"}
                                                             )))
        return Response(dumps([serialize_acupoint(record['acupoint']) for record in results]),
                      mimetype="application/json")


@app.route("/acu/<name>")
def get_acupoint(name):
    db = get_db()
    result = db.read_transaction(lambda tx: tx.run("MATCH (acupoint:Acupoint {name:$name}) "
                                                   "OPTIONAL MATCH (acupoint)<-[r]-(disease:Disease) "
                                                   "RETURN acupoint.name as name,"
                                                   "COLLECT([disease.name, "
                                                   "HEAD(SPLIT(TOLOWER(TYPE(r)), '_')), r.treat_point]) AS disease "
                                                   "LIMIT 1", {"name": name}).single())

    return Response(dumps({"name": result['name'],
                           "disease": [serialize_disease(member)
                                    for member in result['disease']]}),
                    mimetype="application/json")



# @app.route("/acupoint/<title>/vote", methods=["POST"])
# def vote_in_acupoint(title):
#     db = get_db()
#     summary = db.write_transaction(lambda tx: tx.run("MATCH (m:acupoint {title: $title}) "
#                                                     "WITH m, (CASE WHEN exists(m.votes) THEN m.votes ELSE 0 END) AS currentVotes "
#                                                     "SET m.votes = currentVotes + 1;", {"title": title}).consume())
#     updates = summary.counters.properties_set
#
#     db.close()
#
#     return Response(dumps({"updates": updates}), mimetype="application/json")


if __name__ == '__main__':
    # logging.info('Running on port %d, database is at %s', port, url)
    app.run(port=port)
