# FinVox Deployment Guide (AWS ECS + Copilot + GitHub Actions)

This guide explains the step-by-step process to deploy the FinVox application to AWS using a fully serverless, scalable architecture.

## Architecture Overview
- **Environment:** `dev` (Cost-optimized for development/student projects).
- **Compute:** AWS ECS (Fargate) using Graviton (ARM64) for cost savings and high performance.
- **Networking:** Tasks run in **Public Subnets** to avoid the expensive $32/mo NAT Gateway fee. Application Load Balancer (ALB) routes traffic to Backend and Frontend.
- **CI/CD:** GitHub Actions automatically builds Docker images, pushes to Amazon ECR, and triggers ECS Rolling Updates.
- **Secrets:** Managed securely via AWS Systems Manager (SSM) Parameter Store.

---

## Step 1: AWS Copilot Initialization (One-Time Setup)

AWS Copilot handles all the complex infrastructure creation (VPCs, Subnets, Load Balancers, ECS Clusters, etc.) via CloudFormation.

1. **Install Copilot CLI:**
   - Windows: `winget install Amazon.Copilot`
   - Mac: `brew install aws/tap/copilot-cli`

2. **Initialize the Application:**
   Run this from the root of the project to create the `.workspace` and base setup.
   ```bash
   copilot app init finvox
   ```

3. **Create the Dev Environment:**
   This creates the VPC, subnets, and the ECS Cluster (`finvox-dev`).
   ```bash
   copilot env init --name dev --profile default --app finvox
   copilot env deploy --name dev
   ```

---

## Step 2: Add Secrets to AWS SSM

Our application requires API keys (OpenAI, LiveKit, etc.) and Database URLs. We store these securely in AWS SSM, and Copilot injects them into the containers at runtime.

Run the following AWS CLI commands to store your `dev` secrets:

```bash
# Core LLM / Agents
aws ssm put-parameter --name /finvox/dev/OPENAI_API_KEY --value "YOUR_KEY" --type SecureString
aws ssm put-parameter --name /finvox/dev/ANTHROPIC_API_KEY --value "YOUR_KEY" --type SecureString
aws ssm put-parameter --name /finvox/dev/GROQ_API_KEY --value "YOUR_KEY" --type SecureString
aws ssm put-parameter --name /finvox/dev/TAVILY_API_KEY --value "YOUR_KEY" --type SecureString

# LiveKit Voice
aws ssm put-parameter --name /finvox/dev/LIVEKIT_URL --value "wss://YOUR_PROJECT.livekit.cloud" --type SecureString
aws ssm put-parameter --name /finvox/dev/LIVEKIT_API_KEY --value "YOUR_KEY" --type SecureString
aws ssm put-parameter --name /finvox/dev/LIVEKIT_API_SECRET --value "YOUR_SECRET" --type SecureString
aws ssm put-parameter --name /finvox/dev/DEEPGRAM_API_KEY --value "YOUR_KEY" --type SecureString
aws ssm put-parameter --name /finvox/dev/ELEVENLABS_API_KEY --value "YOUR_KEY" --type SecureString

# Databases (Managed Cloud)
aws ssm put-parameter --name /finvox/dev/SUPABASE_URL --value "https://YOUR_PROJECT.supabase.co" --type SecureString
aws ssm put-parameter --name /finvox/dev/SUPABASE_KEY --value "YOUR_KEY" --type SecureString
aws ssm put-parameter --name /finvox/dev/DATABASE_URL --value "postgresql://..." --type SecureString
aws ssm put-parameter --name /finvox/dev/QDRANT_URL --value "https://YOUR_CLUSTER.aws.qdrant.cloud:6333" --type SecureString
aws ssm put-parameter --name /finvox/dev/QDRANT_API_KEY --value "YOUR_KEY" --type SecureString

# Observability
aws ssm put-parameter --name /finvox/dev/LANGFUSE_SECRET_KEY --value "YOUR_KEY" --type SecureString
aws ssm put-parameter --name /finvox/dev/LANGFUSE_PUBLIC_KEY --value "YOUR_KEY" --type SecureString
aws ssm put-parameter --name /finvox/dev/LANGFUSE_HOST --value "https://cloud.langfuse.com" --type SecureString
```

---

## Step 3: Initial Deployment (The Chicken and Egg Solution)

To deploy successfully, the Frontend needs the Backend's URL. But the URL (ALB) is only created *after* we deploy. Here is the trick: we deploy the Backend first, get the URL, and then deploy the Frontend!

1. **Deploy the Backend first:**
   ```bash
   copilot svc deploy --name backend --env dev
   ```
   *Wait for this to finish. Copilot will automatically create the ALB and print a URL at the end (e.g., `http://finvox-publi-1234.ap-southeast-1.elb.amazonaws.com`).*

2. **Update the Frontend Manifest:**
   Copy the URL you just got and paste it into `copilot/frontend/manifest.yml` under `VITE_API_BASE_URL`.

3. **Deploy the rest of the services:**
   Now that the Frontend knows where the Backend is, deploy the remaining services.
   ```bash
   copilot svc deploy --name frontend --env dev
   copilot svc deploy --name voice --env dev
   ```

---

## Step 4: Set up GitHub Actions CI/CD

To automate future deployments, we configure GitHub Actions to use AWS OIDC (OpenID Connect). This means GitHub can deploy securely *without* hardcoded AWS access keys.

### A. AWS IAM Setup (One-time)
1. **Create OIDC Provider:**
   ```bash
   aws iam create-open-id-connect-provider \
     --url https://token.actions.githubusercontent.com \
     --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
     --client-id-list sts.amazonaws.com
   ```
2. **Create IAM Role (`github-actions-finvox`):**
   - Trust Policy: Allow `token.actions.githubusercontent.com` where `sub` contains your GitHub repo (`repo:YourOrg/FinVox:ref:refs/heads/main`).
   - Permissions: `AmazonECS_FullAccess`, `AmazonEC2ContainerRegistryFullAccess`.

### B. GitHub Repository Settings
Go to your GitHub Repo → **Settings** → **Secrets and variables** → **Actions**.

**Add Variables:**
- `AWS_REGION`: e.g., `ap-southeast-1`
- `ECS_CLUSTER`: `finvox-dev`

**Add Secrets:**
- `AWS_ACCOUNT_ID`: Your 12-digit AWS Account ID (e.g., `123456789012`)
- `VITE_API_BASE_URL`: The ALB URL from Step 3 (or your custom domain).

---

## The Daily Workflow

Once the setup is complete, you rarely need to run Copilot commands manually.

1. **Write Code:** Make your changes to the frontend, backend, or voice worker.
2. **Commit & Push:** Push your changes to the `main` branch on GitHub.
3. **Automated CI/CD:**
   - GitHub Actions will run syntax checks.
   - It will build new ARM64 images for all services.
   - It will push them to Amazon ECR.
   - It will tell ECS to pull the new images and perform a **zero-downtime rolling update**.

Your users will instantly see the new version without any manual intervention!
