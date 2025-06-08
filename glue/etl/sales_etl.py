import sys
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from awsglue.dynamicframe import DynamicFrame

args = getResolvedOptions(sys.argv, ['JOB_NAME','INPUT_PATH','OUTPUT_PATH'])
sc = SparkContext()
glueContext = GlueContext(sc)
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read raw JSON orders
orders_df = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": [args['INPUT_PATH']]},
    format="json"
).toDF()

# Clean/filter
clean_df = orders_df.filter("amount IS NOT NULL")
dyf = DynamicFrame.fromDF(clean_df, glueContext, "dyf")

# Write partitioned Parquet
glueContext.write_dynamic_frame.from_options(
    frame=dyf,
    connection_type="s3",
    connection_options={"path": args['OUTPUT_PATH'], "partitionKeys": ["order_date"]},
    format="parquet"
)

job.commit()