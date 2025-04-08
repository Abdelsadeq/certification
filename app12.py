from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from neo4j import GraphDatabase

import json

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # لضمان أن JSON لا يحول النصوص إلى ASCII
CORS(app)

#NEO4J_URI = "bolt://localhost:7687"
#NEO4J_USER = "neo4j"
#NEO4J_PASSWORD = "Sadeq12345"
#NEO4J_DATABASE = "neo4j"

#driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Wait 60 seconds before connecting using these details, or login to https://console.neo4j.io to validate the Aura Instance is available
NEO4J_URI='neo4j+s://98e2f90e.databases.neo4j.io'
NEO4J_USER='neo4j'
NEO4J_PASSWORD='Yxo3R_ng1uaZ2ner_VNMqGj6xCV1liDQXaBybAAN_3g'
AURA_INSTANCEID='98e2f90e'
AURA_INSTANCENAME='Free instance'


#NEO4J_URI = "bolt://localhost:7687"
#NEO4J_USER = "neo4j"
#NEO4J_PASSWORD = "Sadeq12345"
NEO4J_DATABASE = "neo4j"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))



def serialize_node(node):
    return {
        "id": node.id,
        "labels": list(node.labels),
        "properties": dict(node)
    }
	
@app.route("/")
def Search():
	#certification = get_certifications()
	return render_template("Search.html")

#def home():
#	certification = get_certifications()
#	return render_template("Search.html", certification=certification)
	
@app.route('/certifications', methods=['GET'])
def get_certifications():
    min_budget = request.args.get('min_budget', type=int)
    max_budget = request.args.get('max_budget', type=int)
    path = request.args.get('path')
    specialization = request.args.get('specialization')

    with driver.session(database=NEO4J_DATABASE) as session:
        certifications_query = """
            MATCH (c:Certification)-[:RELEVANT_TO]->(s:Specialization {path: $path, name: $specialization})
            WHERE c.totalCost >= $min_budget AND c.totalCost <= $max_budget
            RETURN c
        """
        job_titles_query = """
            MATCH (j:JobTitle)-[:RELATED_TO]->(s:Specialization {name: $specialization})
            RETURN j.name AS jobTitle
        """

        certifications_result = session.run(certifications_query, min_budget=min_budget, max_budget=max_budget, path=path, specialization=specialization)
        job_titles_result = session.run(job_titles_query, specialization=specialization)

        certifications = [serialize_node(record["c"]) for record in certifications_result]
        job_titles = [record["jobTitle"] for record in job_titles_result]

    return jsonify({"certifications": certifications, "jobTitles": job_titles})

@app.route('/api/specializations', methods=['GET'])
def get_specializations():
    query = """
    MATCH (s:Specialization)
    RETURN DISTINCT s.name AS name
    """
    results = []
    with driver.session(database=NEO4J_DATABASE) as session:
        data = session.run(query)
        for record in data:
            print("Fetched specialization:", record["name"])  # طباعة القيم المسترجعة
            results.append(record["name"])
    print("Final results being sent:", results)
    return jsonify(results)
	
@app.route('/api/paths', methods=['GET'])
def get_paths():
    query = """
    MATCH (s:Specialization)
    RETURN DISTINCT s.path AS path
    """
    results = []
    with driver.session(database=NEO4J_DATABASE) as session:
        data = session.run(query)
        for record in data:
            print("Fetched path:", record["path"])  # طباعة القيم المسترجعة
            results.append(record["path"])
    print("Final results being sent:", results)
    return jsonify(results)

@app.route('/api/add-certification', methods=['POST'])
def add_certification():
    data = request.json

    # إضافة الشهادة وربطها بالتخصص
    query = """
    MATCH (s:Specialization {name: $specializationName})
	WITH s
	CREATE (c:Certification {
		name: $name,
		description: $description,
		validity: $validity,
		provider: $provider,
		isSupportedByHadaf: $isSupportedByHadaf,
		learningSource: $learningSource,
		officialWebsite: $officialWebsite,
		registrationMethod: $registrationMethod,
		trainingCost: $trainingCost,
		examCost: $examCost,
		numberOfExams: $numberOfExams,
		totalCost: $totalCost,
		learningMode: $learningMode
	})-[:RELEVANT_TO]->(s)

    """
    parameters = {
        "name": data["name"],
        "description": data["description"],
        "validity": int(data["validity"]),
        "provider": data["provider"],
        "isSupportedByHadaf": data["isSupportedByHadaf"],
        "learningSource": data["learningSource"],
        "officialWebsite": data["officialWebsite"],
        "registrationMethod": data["registrationMethod"],
        "trainingCost": float(data["trainingCost"]),
        "examCost": float(data["examCost"]),
        "numberOfExams": int(data["numberOfExams"]),
        "totalCost": float(data["trainingCost"]) + float(data["examCost"]),
        "learningMode": data["learningMode"],
        "specializationName": data["specialization"]
    }

    with driver.session(database=NEO4J_DATABASE) as session:
        session.run(query, parameters)

    return jsonify({"message": "Certification added successfully"})
	
@app.route('/api/add-job-title', methods=['POST'])
def add_job_title():
    data = request.json  # استلام البيانات من الطلب

    query = """
    MATCH (s:Specialization {name: $specializationName})
    CREATE (j:JobTitle {name: $jobTitle})
    CREATE (j)-[:RELATED_TO]->(s)
    """
    parameters = {
        "jobTitle": data["name"],  # اسم المسمى الوظيفي
        "specializationName": data["specialization"]  # التخصص المرتبط به
    }

    with driver.session(database=NEO4J_DATABASE) as session:
        session.run(query, parameters)

    return jsonify({"message": "Job title added successfully and linked to specialization"})

@app.route('/api/add-specialization', methods=['POST'])
def add_specialization():
    data = request.json  # استلام البيانات من الطلب

    # استعلام لإضافة تخصص جديد
    query = """
    MERGE (s:Specialization {name: $name})
    ON CREATE SET s.path = $path
    """
    parameters = {
        "name": data["name"],  # اسم التخصص
        "path": data["path"]   # المسار (علمي/إداري/تقني...)
    }

    with driver.session(database=NEO4J_DATABASE) as session:
        session.run(query, parameters)

    return jsonify({"message": "Specialization added successfully"})

	
##########################
	
@app.route('/api/delete-job-title', methods=['POST'])
def delete_job_title():
    data = request.json  # استلام البيانات من الطلب

    query = """
    MATCH (j:JobTitle {name: $jobTitle})
    DETACH DELETE j
    """
    parameters = {
        "jobTitle": data["name"]  # اسم المسمى الوظيفي المراد حذفه
    }

    with driver.session(database=NEO4J_DATABASE) as session:
        session.run(query, parameters)

    return jsonify({"message": "Job title deleted successfully"})

@app.route('/api/job-titles', methods=['GET'])
def get_job_titles():
    query = """
    MATCH (j:JobTitle)
    RETURN j.name AS jobTitle
    """
    results = []
    with driver.session(database=NEO4J_DATABASE) as session:
        data = session.run(query)
        for record in data:
            results.append(record["jobTitle"])
    return jsonify(results)


#####################33

@app.route('/api/delete-certification', methods=['POST'])
def delete_certification():
    data = request.json  # استلام البيانات من الطلب

    query = """
    MATCH (c:Certification {name: $certificationName})
    DETACH DELETE c
    """
    parameters = {
        "certificationName": data["name"]  # اسم الشهادة المراد حذفها
    }

    with driver.session(database=NEO4J_DATABASE) as session:
        session.run(query, parameters)

    return jsonify({"message": "Certification deleted successfully"})

@app.route('/api/certifications-list', methods=['GET'])
def get_certifications_list():
    query = """
    MATCH (c:Certification)
    RETURN c.name AS certificationName
    """
    results = []
    with driver.session(database=NEO4J_DATABASE) as session:
        data = session.run(query)
        for record in data:
            results.append(record["certificationName"])
    return jsonify(results)
##############################


@app.route('/api/delete-specialization', methods=['POST'])
def delete_specialization():
    data = request.json  # استلام البيانات من الطلب

    query = """
    MATCH (s:Specialization {name: $specializationName})
    DETACH DELETE s
    """
    parameters = {
        "specializationName": data["name"]  # اسم التخصص المراد حذفه
    }

    with driver.session(database=NEO4J_DATABASE) as session:
        session.run(query, parameters)

    return jsonify({"message": "Specialization deleted successfully"})



if __name__ == '__main__':
	
    app.run(debug=True)
