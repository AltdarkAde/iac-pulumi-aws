# Environment Setup (Pulumi + AWS)

This page documents the one-time setup shared by all labs in this repo: installing Pulumi, creating an AWS account, installing the AWS CLI, and configuring credentials.

## Environment

| Item | Value |
|------|-------|
| OS | Ubuntu 24.04 (Linux) |
| Pulumi | v3.268.0 |
| AWS CLI | v2.38.1 |
| Cloud | AWS |

## Table of Contents

1. [Install Pulumi](#1-install-pulumi)
2. [Create a Free AWS Account](#2-create-a-free-aws-account)
3. [Install the AWS CLI](#3-install-the-aws-cli)
4. [Create an IAM User and Access Keys](#4-create-an-iam-user-and-access-keys)
5. [Configure the Keys](#5-configure-the-keys)
6. [Troubleshooting Notes](#troubleshooting-notes)
7. [Next Steps](#next-steps)

---

## 1. Install Pulumi

Pulumi is the Infrastructure as Code (IaC) tool used in this lab. It lets you define cloud resources in a real programming language (Python, TypeScript, Go, etc.).

Install with the official script:

```bash
curl -fsSL https://get.pulumi.com | sh
```

The installer extracts Pulumi to `~/.pulumi/bin` and adds that folder to `PATH` in `~/.bashrc`.

Reload the shell and verify:

```bash
source ~/.bashrc
pulumi version
```

Expected output:

```
v3.268.0
```

> **Note:** My first download from GitHub stalled and failed with an HTTP/2 `PROTOCOL_ERROR`. The installer automatically fell back to `get.pulumi.com` and completed successfully. This is normal on slow or unstable connections.

**Screenshot:** _add a screenshot of `pulumi version` here_

---

## 2. Create a Free AWS Account

1. Go to [aws.amazon.com/free](https://aws.amazon.com/free) and click **Create a Free Account**.
2. Enter an email address and choose an account name.
3. Verify the email with the code AWS sends.
4. Set a strong root password.
5. Add contact details and a payment method (a card is required for identity verification, even for free-tier usage).
6. Complete phone verification.
7. Choose a support plan (the free/basic plan is enough for this lab).
8. Sign in to the [AWS Console](https://console.aws.amazon.com/).

**Recommended right after sign-up:**

- Enable **MFA** on the root user (IAM > Security credentials).
- Set up a **billing alert** (Billing > Budgets) so unexpected charges don't surprise you.
- Do **not** use the root account for day-to-day work or create access keys for it. We create a separate IAM user in step 4.

**Screenshot:** _add a screenshot of the AWS Console home page here (hide your account ID)_

---

## 3. Install the AWS CLI

Install AWS CLI v2 using the official installer script:

```bash
curl -fsSL https://awscli.amazonaws.com/v2/install.sh | bash
```

The installer downloads the package, **verifies the GPG signature**, and installs the binary to `~/.local/bin/aws`.

The installer does not add that folder to `PATH`, so I added it manually:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Verify:

```bash
aws --version
```

Expected output (version details will vary):

```
aws-cli/2.38.1 Python/3.14.6 Linux/7.0.0-38-generic script-exe/x86_64.ubuntu.24
```

**Screenshot:** _add a screenshot of `aws --version` here_

---

## 4. Create an IAM User and Access Keys

Pulumi and the AWS CLI need credentials to talk to AWS. Instead of using the root account, I created a dedicated IAM user.

### 4.1 Create the IAM user

1. In the AWS Console, search for **IAM**.
2. Go to **Users** > **Create user**.
3. **Step 1, Specify user details:** enter the user name `iac`. Leave console access disabled, since this user is CLI-only. Click **Next**.
4. **Step 2, Set permissions:** choose **Attach policies directly** (not "Copy permissions" or "Add user to group"). Search for `AdministratorAccess` and tick it. Click **Next**.
5. **Step 3, Review and create:** confirm the details and click **Create user**.

> **Security note:** `AdministratorAccess` is convenient for a learning lab but far broader than needed. In real environments, use least-privilege policies, such as S3-only permissions for this lab.

**Screenshot:** _add a screenshot of the review page here_

### 4.2 Create the access key

1. Open **IAM > Users > `iac`**.
2. Go to the **Security credentials** tab.
3. Under **Access keys**, click **Create access key**.
4. Select **Command Line Interface (CLI)**, tick the confirmation box, and click **Next**.
5. Optionally add a description tag (e.g. `pulumi-cli`), then click **Create access key**.
6. Copy the **Access key ID** and **Secret access key**, or download the `.csv`.

> **Warning:** The secret access key is shown only once. Never commit it to GitHub, paste it in chats, or put it in screenshots. If a key is ever exposed, delete it in IAM immediately and create a new one.

---

## 5. Configure the Keys

Run the interactive setup:

```bash
aws configure
```

Enter the values when prompted:

```
AWS Access Key ID [None]: <your-access-key-id>
AWS Secret Access Key [None]: <your-secret-access-key>
Default region name [None]: us-east-1
Default output format [None]: json
```

This stores the credentials in `~/.aws/credentials` and the region/output settings in `~/.aws/config`. Pulumi's AWS provider reads these automatically.

Verify the credentials work:

```bash
aws sts get-caller-identity
```

Expected output (values redacted):

```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/iac"
}
```

The ARN ending in `user/iac` confirms the CLI is authenticated as the IAM user I created.

**Screenshot:** _add a screenshot of `aws sts get-caller-identity` here (blur the account ID)_

---

## Troubleshooting Notes

| Problem | Cause | Fix |
|---------|-------|-----|
| Pulumi download fails with `PROTOCOL_ERROR` | Unstable connection to GitHub releases | Installer falls back to `get.pulumi.com` automatically. Wait for it to finish. |
| `pulumi: command not found` | Shell hasn't reloaded `PATH` | Run `source ~/.bashrc` or open a new terminal |
| `aws: command not found` | `~/.local/bin` not on `PATH` | Add it to `~/.bashrc` (see step 3) |
| Duplicate entries in `echo $PATH` | Ran `source ~/.bashrc` multiple times in one session | Harmless. Opening a new terminal resets it. |
| No "Attach policies directly" selected in IAM | Console defaults to "Copy permissions" when no groups or users exist | Manually select **Attach policies directly** |

---

## Next Steps

Continue with [Lab 1: Provisioning Infrastructure with an S3 Bucket](../lab-1-s3-bucket/README.md).

---

## Security Checklist

- [x] Root account not used for CLI access
- [x] Dedicated IAM user created for automation
- [ ] MFA enabled on root account
- [ ] Billing alert configured
- [ ] Access keys never committed to Git (add `.aws/` and `*.csv` to `.gitignore` if relevant)
