# Lab 1: Provisioning Infrastructure with an S3 Bucket

In this lab I used Pulumi (Python) to create, update, configure, duplicate, and destroy an **Amazon S3 bucket**, covering the full lifecycle of infrastructure as code. Along the way I hit and fixed several real errors, which are documented in [Issues and Fixes](#issues-and-fixes).

**Prerequisites:** the [environment setup](../docs/setup.md).

## Table of Contents

1. [Create a New Project](#1-create-a-new-project)
2. [Configure AWS](#2-configure-aws)
3. [Provision Infrastructure](#3-provision-infrastructure)
4. [Update Infrastructure](#4-update-infrastructure)
5. [Make the Stack Configurable](#5-make-the-stack-configurable)
6. [Create a Second Stack](#6-create-a-second-stack)
7. [Destroy Infrastructure](#7-destroy-infrastructure)
8. [Issues and Fixes](#issues-and-fixes)
9. [What I Learned](#what-i-learned)

## Key Concepts

| Term | Meaning |
|------|---------|
| **Project** | A folder with a Pulumi program and a `Pulumi.yaml` file |
| **Stack** | One deployed instance of a project (here `dev` and `prod`), each with its own config and state |
| **State** | Pulumi's record of what is deployed. Stored in Pulumi Cloud for this lab |
| **Resource** | A cloud object defined in code, such as a bucket or a file in a bucket |

## Final Layout

```
lab-1-s3-bucket/
├── README.md
├── __main__.py        # Infrastructure code
├── Pulumi.yaml        # Project definition
├── requirements.txt   # Python dependencies (pulumi, pulumi-aws)
├── www/               # Site files for the dev stack
└── wwwprod/           # Site files for the prod stack
```

---

## 1. Create a New Project

I used the default Pulumi Cloud backend (free tier), so state is stored online and no passphrase is needed.

```bash
mkdir -p ~/projects/ioc-lab1 && cd ~/projects/ioc-lab1
pulumi new python
```

I used the generic `python` template with project name `ioc-lab1` and stack `dev`. This template has no AWS provider, so I added it myself in step 2.

The first run failed while creating the virtual environment (see [Issues and Fixes](#issues-and-fixes)). After installing `python3.12-venv`, I finished the install:

```bash
sudo apt install -y python3.12-venv
rm -rf venv
pulumi install
```

I added a `.gitignore` entry for `venv/` and `__pycache__/` so they stay out of Git.

---

## 2. Configure AWS

Credentials come from `aws configure` ([setup guide](../docs/setup.md#5-configure-the-keys)), so no keys live in the project.

Install the AWS provider into the virtual environment and add it to `requirements.txt`:

```bash
source venv/bin/activate
pip install pulumi-aws
pip freeze | grep -i pulumi-aws     # note the version
echo "pulumi-aws" >> requirements.txt
```

My account sits inside an AWS Organization with a **service control policy (SCP)** that only allows the **`eu-north-1` (Stockholm)** region (details in [Issues and Fixes](#issues-and-fixes)), so I set that region on the stack:

```bash
pulumi config set aws:region eu-north-1
aws configure set region eu-north-1
```

---

## 3. Provision Infrastructure

The starter program creates one bucket and exports its name:

```python
import pulumi
import pulumi_aws as aws

bucket = aws.s3.Bucket("my-bucket")

pulumi.export("bucket_name", bucket.id)
```

```bash
pulumi up
```

The first attempt failed with `AccessDenied` from the SCP (in the wrong region). After switching to `eu-north-1`, it succeeded:

```
 +   └─ aws:s3:Bucket   my-bucket   created (9s)
Resources:
    + 1 created
```

Pulumi added a random suffix to the bucket name (`my-bucket-xxxxxxx`) so it is globally unique. I confirmed it with `pulumi stack output bucket_name` and `aws s3 ls`.

---

## 4. Update Infrastructure

I added an `index.html` file in a `www/` folder and uploaded it with a `BucketObject`:

```python
import os
import pulumi
import pulumi_aws as aws

bucket = aws.s3.Bucket("my-bucket")

filepath = os.path.join("www", "index.html")
obj = aws.s3.BucketObject(
    "index.html",
    bucket=bucket.id,
    source=pulumi.FileAsset(filepath),
)

pulumi.export("bucket_name", bucket.id)
```

`pulumi up` created only the new object and left the bucket unchanged (`+ 1 created`, `2 unchanged`). That is the key idea of IaC: Pulumi compares code to state and changes only the difference.

I first tried to make the bucket a public website with `acl="public-read"`, which failed. I kept the bucket **private** instead (see [Issues and Fixes](#issues-and-fixes)). To view a file in a private bucket, I used a temporary signed link:

```bash
aws s3 presign s3://$(pulumi stack output bucket_name)/index.html --expires-in 300 --region eu-north-1
```

---

## 5. Make the Stack Configurable

I moved hard-coded values into stack config. The final program uploads every file in a configurable folder and tags the bucket with the environment name:

```python
"""A Python Pulumi program"""

import os
import mimetypes
import pulumi
import pulumi_aws as aws

config = pulumi.Config()
site_dir = config.require("siteDir")
environment = config.get("environment") or "dev"

bucket = aws.s3.Bucket("my-bucket", tags={"Environment": environment})

for file in os.listdir(site_dir):
    filepath = os.path.join(site_dir, file)
    if not os.path.isfile(filepath):
        continue
    mime_type, _ = mimetypes.guess_type(filepath)
    aws.s3.BucketObject(
        file,
        bucket=bucket.id,
        key=file,
        source=pulumi.FileAsset(filepath),
        content_type=mime_type,
    )

pulumi.export("bucket_name", bucket.id)
pulumi.export("environment", environment)
```

Config for the dev stack:

```bash
pulumi config set siteDir www
pulumi config set environment dev
pulumi config
```

I then added an `about.html` page. After fixing a bug in my loop (see [Issues and Fixes](#issues-and-fixes)), the preview showed exactly one change (`~ update` on `about.html`), and `aws s3 ls` showed the file grow from 88 to 305 bytes.

---

## 6. Create a Second Stack

A new stack is a separate deployment of the same code with its own config:

```bash
mkdir wwwprod
cp www/index.html wwwprod/        # then edited to say "(In Production)"
pulumi stack init prod
pulumi config set aws:region eu-north-1
pulumi config set environment prod
pulumi config set siteDir wwwprod
pulumi up
```

The prod stack created its own bucket (`my-bucket-xxxxxxx`, a different name from dev) with its own page. I used `pulumi stack ls` to see both stacks and `pulumi stack select` to switch between them.

Stacks do **not** inherit config from each other. My first prod deployment tagged its bucket `Environment: dev` because I hadn't set `environment`, so the code's default applied. Set required config explicitly on every new stack, including `aws:region`.

---

## 7. Destroy Infrastructure

To avoid unexpected charges from forgotten resources, I destroyed both stacks and removed them, one at a time:

```bash
pulumi stack select prod
pulumi destroy          # - 3 deleted
pulumi stack rm prod

pulumi stack select dev
pulumi destroy          # - 4 deleted
pulumi stack rm dev

pulumi stack ls         # empty
aws s3 ls               # no lab buckets left
```

`pulumi destroy` deletes the cloud resources. `pulumi stack rm` deletes the stack's record and history, so it should only run after a successful destroy.

I also deleted a test bucket I created by hand with the AWS CLI while debugging. Pulumi doesn't manage resources it didn't create, so `destroy` would not have removed it.

---

## Issues and Fixes

| # | Problem | Cause | Fix |
|---|---------|-------|-----|
| 1 | `pulumi new` failed: `ensurepip is not available` | The `python3-venv` package was missing on Ubuntu | `sudo apt install python3.12-venv`, then `rm -rf venv` and `pulumi install`. A retry of `pulumi new` said the project already existed, because the files had been created before the install step failed. |
| 2 | Generic `python` template had no AWS code | The `python` template doesn't include the AWS provider | `pip install pulumi-aws` and add it to `requirements.txt` |
| 3 | `AccessDenied ... explicit deny in a service control policy` on `s3:CreateBucket` | My AWS account is in an Organization whose SCP blocks most regions | Confirmed with the plain AWS CLI (same error), tested several regions, and found only `eu-north-1` allowed. Set `aws:region eu-north-1` on every stack. |
| 4 | `InvalidAccessKeyId` in `af-south-1` | That is an opt-in region not enabled for my account | Unrelated to the SCP; ignored |
| 5 | `AccessControlListNotSupported` when using `acl="public-read"` | New S3 buckets have ACLs disabled and Block Public Access on | Switched to a private bucket. A public site would need a public-access-block override and a bucket policy instead of ACLs. |
| 6 | Updates kept failing on `PutObjectAcl` after removing the ACL | The failed run left `acl` in Pulumi's state, so Pulumi tried to reset it on a bucket that rejects ACLs | Removed the object from state with `pulumi state delete '<urn>'`, then `pulumi up` recreated it |
| 7 | `SyntaxError: invalid syntax. Perhaps you forgot a comma?` | Missing comma after `source=pulumi.FileAsset(filepath)` | Added the comma |
| 8 | `Duplicate resource URN` | A loop created several resources with the same name (`index.html`) | Named each resource after its file |
| 9 | Editing `about.html` showed `4 unchanged`, and `about.html` kept showing `index.html` content | A bug in my loop: the path used `page_file` (always `index.html`) instead of the loop variable `file`, so every object uploaded the same file | Changed `os.path.join(site_dir, page_file)` to `os.path.join(site_dir, file)` |
| 10 | `curl` on the old website endpoint returned `403 Forbidden` | The bucket is private, which is the intended result | Used `aws s3 presign` for temporary access |
| 11 | `AWS_IO_TLS_NEGOTIATION_TIMEOUT` on `aws s3 cp` | A slow or unstable connection | Retried; the classic transfer client is a fallback (`aws configure set default.s3.preferred_transfer_client classic`) |
| 12 | `pulumi config set iac-lab1:siteDir ...` had no effect | The prefix didn't match the project name `ioc-lab1` | Set config without a prefix, so Pulumi uses the current project's name |
| 13 | Prod bucket tagged `Environment: dev` | New stacks don't inherit config, so the code default applied | `pulumi config set environment prod` |

---

## What I Learned

- A Pulumi **project** holds the code and each **stack** is a separate deployment of it. Config is per stack and is not inherited.
- `pulumi preview` shows exactly what will change. Reading it before answering "yes" caught several mistakes, and anything marked `replace` deserves extra care.
- If a preview shows no change after you edit something, check that the resource is really pointing at the file you edited.
- Organization-level policies (SCPs) override IAM permissions, even `AdministratorAccess`. Testing with the plain AWS CLI shows whether a problem is Pulumi or AWS.
- Private by default is safer. Temporary presigned URLs give access without exposing a bucket.
- Always destroy lab resources, and delete anything created outside Pulumi by hand.

## Security Notes

- No access keys, account IDs, or organization IDs are stored in this repo. All sample output has been redacted.
- Presigned URLs contain an access key ID, so don't publish them.
