"""A Python Pulumi program"""

import os
import mimetypes
import pulumi
import pulumi_aws as aws

config = pulumi.Config()
site_dir = config.require("siteDir")

config = pulumi.Config()
environment = config.get("environment") or "dev"
page_file = config.get("pageFile") or "index.html"

bucket = aws.s3.Bucket("my-bucket", tags={"Environment": environment})

for file in os.listdir(site_dir):
 filepath = os.path.join(site_dir, file)
 mime_type, _ = mimetypes.guess_type(filepath)
 obj = aws.s3.BucketObject(file,
    bucket=bucket.id,
    source=pulumi.FileAsset(filepath),
    content_type=mime_type,
)

pulumi.export("bucket_name", bucket.id)
pulumi.export("environment", environment)