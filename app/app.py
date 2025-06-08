from flask import Flask, jsonify
import boto3
import time

app = Flask(__name__)
athena = boto3.client('athena', region_name='ap-south-1')

# Athena settings
DATABASE = 'sales_db'
OUTPUT = 's3://your-athena-query-results/'  # Change to your query results bucket

def run_query(query):
    resp = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': DATABASE},
        ResultConfiguration={'OutputLocation': OUTPUT}
    )
    query_id = resp['QueryExecutionId']
    # Wait for query to finish
    while True:
        status = athena.get_query_execution(QueryExecutionId=query_id)
        state = status['QueryExecution']['Status']['State']
        if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        time.sleep(2)
    if state != 'SUCCEEDED':
        raise RuntimeError(f"Query {state}")
    # Fetch results
    results = athena.get_query_results(QueryExecutionId=query_id)
    rows = results['ResultSet']['Rows']
    # Parse header and data
    header = [c['VarCharValue'] for c in rows[0]['Data']]
    data = []
    for r in rows[1:]:
        entry = { header[i]: r['Data'][i].get('VarCharValue') for i in range(len(header)) }
        data.append(entry)
    return data

@app.route('/metrics', methods=['GET'])
def metrics():
    query = '''
    SELECT order_date, SUM(amount) AS daily_revenue
    FROM processed_sales
    GROUP BY order_date
    ORDER BY order_date DESC
    LIMIT 7;
    '''
    return jsonify(run_query(query))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000)