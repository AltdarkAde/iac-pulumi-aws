# Infrastructure as Code with Pulumi and AWS

A hands-on project where I learn **Infrastructure as Code (IaC)** by building real AWS resources with [Pulumi](https://www.pulumi.com/), step by step, and documenting each lab as I go.

## Labs

| Lab | Topic | Status |
|-----|-------|--------|
| [Lab 1](lab-1-s3-bucket/README.md) | Provisioning Infrastructure with an S3 Bucket | In progress |
| Lab 2 | Provisioning EC2 Virtual Machines | Planned |
| Lab 3 | Deploying Docker Images to ECS & Fargate | Planned |

## Before You Start

All labs share the same setup: Pulumi, an AWS account, the AWS CLI, and an IAM user with access keys.

See **[docs/setup.md](docs/setup.md)** for the full walkthrough.

## Tools

| Tool | Version |
|------|---------|
| Pulumi | 3.268.0 |
| AWS CLI | 2.38.1 |
| OS | Ubuntu 24.04 |
| Language | Python |

## Repository Structure

```
.
├── README.md                 # This file
├── docs/
│   └── setup.md              # Pulumi, AWS account, CLI, and credentials setup
├── lab-1-s3-bucket/          # Lab 1: S3 bucket
├── lab-2-ec2/                # Lab 2: EC2 (coming soon)
└── lab-3-ecs-fargate/        # Lab 3: ECS & Fargate (coming soon)
```

## Security

- Never commit AWS access keys, secret keys, or `.csv` credential files.
- Credentials live in `~/.aws/`, outside this repo.
- Labs use an `AdministratorAccess` IAM user for convenience. This is fine for learning, but real environments should use least-privilege policies.
- Destroy resources at the end of each lab to avoid unexpected charges.
