'''
将得到的知识图谱将其显示在 节点和关系旁边
'''
#!/usr/bin/env python
import os
from json import dumps
import logging
from dotenv import load_dotenv, find_dotenv

from flask import Flask, g, Response, request, jsonify
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
    if not hasattr(g, 'neo4j_db'):
        if neo4jVersion.startswith("5"):
            g.neo4j_db = driver.session(database=database)
        else:
            g.neo4j_db = driver.session()
    return g.neo4j_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'neo4j_db'):
        g.neo4j_db.close()


@app.route("/")
def get_index():
    return app.send_static_file('qureyindex.html')

def buildNodes(nodeRecord): #构建web显示节点
    data = {"id": nodeRecord._id, "label": list(nodeRecord._labels)[0]} #将集合元素变为list，然后取出值
    data.update(dict(nodeRecord._properties))

    return {"data": data}


def buildEdges(relationRecord): #构建web显示边
    data = {"source": relationRecord.start_node._id,
            "target":relationRecord.end_node._id,
            "relationship": relationRecord.type}

    return {"data": data}

def serialize_acupoint(acupoint):
    return {
        'id': acupoint['id'],
        'name': acupoint['name'],
        'position': acupoint['position']
    }


def serialize_disease(disease):
    return {
        'name': disease['name'],
        # 'job': disease[1],
        # 'role': disease[2]
    }


@app.route("/graph")
def get_graph():
    db = get_db()
    results = db.read_transaction(lambda tx: list(tx.run("MATCH (m:Acupoint)<-[r:treat_point]-(a:Disease) "
                                                         "RETURN m,a,r "
                                                         "LIMIT $limit", {
                                                             "limit": request.args.get("limit",
                                                                                       100)})))

    nodeList = []
    edgeList = []
    for result in results:
        nodeList.append(result[0])
        nodeList.append(result[1])
        nodeList = list(set(nodeList))
        edgeList.append(result[2])

    nodes = list(map(buildNodes, nodeList))
    rels = list(map(buildEdges, edgeList))
    # return Response(dumps({"nodes": nodes, "links": rels}),
    #                 mimetype="application/json")
    return jsonify(elements={"nodes": nodes, "edges":rels})


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





if __name__ == '__main__':
    # logging.info('Running on port %d, database is at %s', port, url)
    app.run(port=port)
